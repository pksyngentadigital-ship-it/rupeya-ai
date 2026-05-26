"""Parse inline financial-highlights tables from PSX DPS company pages.

The DPS company page (dps.psx.com.pk/company/{TICKER}) renders three
inline tables we care about:

  Table A: ANNUAL HIGHLIGHTS — last 4 fiscal years
      | 2025 | 2024 | 2023 | 2022 |
      Sales / Revenue
      Profit after Taxation / Net income
      EPS

  Table B: QUARTERLY HIGHLIGHTS — last 4 standalone quarters
      (we skip this for MVP — standalone-quarter values mix awkwardly
      with our cumulative-period storage convention)

  Table C: RATIOS — gross margin, net margin, etc.
      (we skip — derived elsewhere from raw numbers)

This module ONLY parses Table A. For each year column we yield one
FundamentalRow with period="{YYYY}-FY" and 3 of 8 columns populated
(revenue, net_income, eps). The other 5 columns stay null until a deeper
extraction (PDF / Claude / in-session) fills them in.

PSX inline values are in PKR THOUSANDS — we multiply by 1,000 to store
absolute PKR, consistent with the rest of fundamentals_quarterly.
"""

from __future__ import annotations

import logging
import re
from datetime import date as Date

from selectolax.parser import HTMLParser

from .models import FundamentalRow

log = logging.getLogger("rupeya.fundamentals.inline_parser")

# Header text fragments we look for to identify each known row.
# All match case-insensitively against the first cell of each row.
_ROW_LABEL_MATCHERS = {
    "revenue": (
        "sales", "revenue", "net sales", "turnover", "net turnover",
        "total revenue", "interest earned", "markup earned",
        "mark-up / return / interest earned",
    ),
    "net_income": (
        "profit after taxation", "profit after tax", "net income",
        "net profit", "pat", "profit for the year",
        "profit attributable to ordinary shareholders",
    ),
    "eps": (
        "eps", "earnings per share", "basic eps", "basic earnings per share",
    ),
}

# Match a 4-digit year header cell. Some pages use "2025-06-30" or "2025"; we
# accept either.
_YEAR_HEADER_RE = re.compile(r"\b(20\d{2})\b")

# PSX inline numbers come with thousand-separator commas and possibly trailing
# units suffixes like "(Rs in '000)". This regex extracts the numeric core.
_NUMBER_CLEAN_RE = re.compile(r"[,\s]")

# PSX inline values are reported in thousands of PKR.
INLINE_UNITS_FACTOR = 1_000


def _clean_number(raw: str) -> float | None:
    if raw is None:
        return None
    s = raw.strip()
    if not s or s in ("-", "--", "N/A", "n/a"):
        return None
    s = _NUMBER_CLEAN_RE.sub("", s)
    # Parenthesised negatives e.g. "(1234)" → "-1234"
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return None


def _label_matches(cell_text: str, candidates: tuple[str, ...]) -> bool:
    low = cell_text.lower().strip().rstrip(":")
    return any(low == c or low.startswith(c) for c in candidates)


def _row_first_cell(row) -> str:
    cells = row.css("th, td")
    if not cells:
        return ""
    return cells[0].text(strip=True)


def _row_values(row) -> list[str]:
    """Return the data cells of a row (everything except the leading label cell)."""
    cells = row.css("th, td")
    return [c.text(strip=True) for c in cells[1:]]


def _find_annual_table(tree: HTMLParser):
    """Locate the table containing the annual highlights.

    Heuristic: a table that has at least one revenue-like row AND
    at least one EPS-like row, AND column headers that look like years.
    """
    for table in tree.css("table"):
        rows = table.css("tr")
        if not rows:
            continue

        # Capture row labels
        labels = [_row_first_cell(r) for r in rows]

        has_revenue_row = any(
            _label_matches(l, _ROW_LABEL_MATCHERS["revenue"]) for l in labels
        )
        has_eps_row = any(
            _label_matches(l, _ROW_LABEL_MATCHERS["eps"]) for l in labels
        )

        # The first row usually carries the year headers.
        header_cells = rows[0].css("th, td")
        header_text = " ".join(c.text(strip=True) for c in header_cells)
        years_found = list(set(_YEAR_HEADER_RE.findall(header_text)))

        # We want at least 3 distinct years AND both rows we look for.
        if has_revenue_row and has_eps_row and len(years_found) >= 3:
            return table

    return None


def _extract_year_columns(table) -> list[tuple[int, int]]:
    """Return [(column_index, fiscal_year), ...] from the first row's headers.

    column_index is 1-based offset from the LABEL cell (i.e. index 0 in
    _row_values output corresponds to column_index 1).
    """
    rows = table.css("tr")
    if not rows:
        return []
    header_cells = rows[0].css("th, td")
    # Skip the leading label cell (often empty for header row)
    out: list[tuple[int, int]] = []
    for i, cell in enumerate(header_cells[1:], start=1):
        text = cell.text(strip=True)
        m = _YEAR_HEADER_RE.search(text)
        if m:
            out.append((i - 1, int(m.group(1))))  # value index is i-1 in _row_values
    return out


# --- Public API --------------------------------------------------------------


def parse_annual_table(html: str, ticker: str) -> list[FundamentalRow]:
    """Return one FundamentalRow per fiscal-year column found in the
    annual highlights table on the DPS page.

    Each row has only `revenue`, `net_income`, `eps` populated (the
    remaining 5 columns stay None). Period is "{YYYY}-FY" with the
    period_end_date inferred from the fiscal year (best-effort).
    """
    tree = HTMLParser(html)
    table = _find_annual_table(tree)
    if table is None:
        log.warning("%s: no annual highlights table found on DPS page", ticker)
        return []

    year_cols = _extract_year_columns(table)
    if not year_cols:
        log.warning("%s: annual table found but no year columns parsed", ticker)
        return []

    log.debug(
        "%s: annual table — year columns: %s",
        ticker, [(i, y) for i, y in year_cols],
    )

    # Gather values per metric
    values_by_metric: dict[str, list[str]] = {}
    for row in table.css("tr"):
        label = _row_first_cell(row)
        for metric, candidates in _ROW_LABEL_MATCHERS.items():
            if _label_matches(label, candidates):
                values_by_metric[metric] = _row_values(row)
                break

    # Build one row per year column
    out: list[FundamentalRow] = []
    for col_idx, year in year_cols:
        revenue_raw = (values_by_metric.get("revenue") or [None])
        net_income_raw = (values_by_metric.get("net_income") or [None])
        eps_raw = (values_by_metric.get("eps") or [None])

        def at(values: list[str | None], i: int) -> str | None:
            return values[i] if values and i < len(values) else None

        rev = _clean_number(at(revenue_raw, col_idx) or "")
        ni = _clean_number(at(net_income_raw, col_idx) or "")
        eps = _clean_number(at(eps_raw, col_idx) or "")

        # Apply units scaling — PSX inline is in thousands
        rev_abs = rev * INLINE_UNITS_FACTOR if rev is not None else None
        ni_abs = ni * INLINE_UNITS_FACTOR if ni is not None else None
        # EPS is per share — no scaling

        # If everything is null, skip this column entirely
        if rev_abs is None and ni_abs is None and eps is None:
            continue

        # period_end_date heuristic: we don't know the fiscal cycle from
        # the inline table alone. Banks = Dec 31, most others = Jun 30.
        # Leave null and let downstream logic fill it.
        out.append(
            FundamentalRow(
                ticker=ticker.upper(),
                period=f"{year}-FY",
                period_end_date=None,
                revenue=rev_abs,
                net_income=ni_abs,
                eps=eps,
                book_value=None,
                debt=None,
                cash=None,
                fcf=None,
                dividend_per_share=None,
                source="psx_inline_html",
                source_url=f"https://dps.psx.com.pk/company/{ticker.upper()}",
                notes="Extracted from DPS inline annual table (partial: 3 of 8 columns).",
            )
        )

    log.info("%s: inline parser yielded %d annual row(s)", ticker, len(out))
    return out
