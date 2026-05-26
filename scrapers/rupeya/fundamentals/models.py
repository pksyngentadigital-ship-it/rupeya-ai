"""Domain models for B3a fundamentals.

Period convention (Pakistani fiscal-year cumulative buckets):
    2026-Q1  →  3-month cumulative from fiscal-year start
    2026-H1  →  6-month cumulative (half-year)
    2026-9M  →  9-month cumulative (Pakistani "Q3" filing)
    2026-FY  →  12-month annual

Standalone quarters (Q2, Q3, Q4) are derived later by subtraction in the
quant engine: Q3 standalone = 9M − H1. We DO NOT compute them at scrape
time; the scraper is a dumb transcriber of what the issuer published.

Year in the period string is the fiscal year in which the period ENDS.
So for an Oil & Gas company with Jul–Jun fiscal year:
    Filing for Jul–Sep 2025 → "2026-Q1"  (fiscal year ends Jun 2026)
For a bank using calendar-year fiscal:
    Filing for Jan–Mar 2026 → "2026-Q1"  (fiscal year ends Dec 2026)

`period_end_date` disambiguates the actual calendar dates either way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date as Date, datetime, timezone

PERIOD_KINDS: tuple[str, ...] = ("Q1", "H1", "9M", "FY")

# Units factor: filings publish in 'thousands' or 'millions'. We multiply
# at extraction time so what lands in the DB is absolute PKR.
UNIT_FACTORS: dict[str, int] = {
    "actuals": 1,
    "actual": 1,
    "thousands": 1_000,
    "thousand": 1_000,
    "millions": 1_000_000,
    "million": 1_000_000,
    "billions": 1_000_000_000,
    "billion": 1_000_000_000,
}


@dataclass
class FundamentalRow:
    """One row of audited / unaudited financial data for a (ticker, period).

    Numeric fields below are in ABSOLUTE PKR (no units scaling).
    EPS and dividend_per_share are per-share values and not multiplied.
    """

    ticker: str
    period: str                       # canonical, e.g. "2026-9M"
    period_end_date: Date | None
    revenue: float | None
    net_income: float | None
    eps: float | None
    book_value: float | None
    debt: float | None
    cash: float | None
    fcf: float | None
    dividend_per_share: float | None

    # --- bookkeeping (not all persisted to fundamentals_quarterly today;
    # we keep them on the dataclass so a future schema migration is trivial)
    source: str = "psx_pdf_claude"
    source_url: str | None = None
    notes: str | None = None
    extracted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ---- Conversion helpers ----

    def to_db_row(self) -> dict:
        """Return only the columns that fundamentals_quarterly has today.

        Other fields (period_end_date, source, notes, extracted_at) are
        carried elsewhere (logs, scrape_runs.errors) until we migrate the
        schema to persist them.
        """
        return {
            "ticker": self.ticker,
            "period": self.period,
            "revenue": self.revenue,
            "net_income": self.net_income,
            "eps": self.eps,
            "book_value": self.book_value,
            "debt": self.debt,
            "cash": self.cash,
            "fcf": self.fcf,
            "dividend_per_share": self.dividend_per_share,
        }


# ---------------- Period normalization ---------------------------------------


_CANONICAL_RE = re.compile(r"^(\d{4})-(Q1|H1|9M|FY)$")
_LOOSE_PATTERNS = (
    # Already-canonical variants with whitespace / lowercase
    re.compile(r"^(?P<year>\d{4})[-_\s/](?P<kind>q1|h1|9m|fy)$", re.IGNORECASE),
    # "Q1 2026", "9M-2026"
    re.compile(r"^(?P<kind>q1|h1|9m|fy)[-_\s/](?P<year>\d{4})$", re.IGNORECASE),
)
# Map Pakistani filings' Q-numbering to our cumulative codes:
#   Issuer's "Q1" → 3-month cumulative → our "Q1"
#   Issuer's "Q2 / half-yearly" → 6-month cumulative → our "H1"
#   Issuer's "Q3 / 9-month" → 9-month cumulative → our "9M"
#   Issuer's "annual / Q4" → 12-month → our "FY"
_Q_TO_CUMULATIVE = {
    "Q1": "Q1",
    "Q2": "H1",
    "H1": "H1",
    "Q3": "9M",
    "9M": "9M",
    "Q4": "FY",
    "FY": "FY",
}


def normalize_period(value: str) -> str | None:
    """Coerce a free-form period string into canonical "YYYY-{Q1|H1|9M|FY}".

    Returns None if we can't make sense of the input.
    """
    if not value:
        return None
    s = value.strip().replace(" ", "")
    if not s:
        return None
    # Already canonical?
    if _CANONICAL_RE.match(s.upper()):
        return s.upper()
    # Loose forms
    for pat in _LOOSE_PATTERNS:
        m = pat.match(s)
        if m:
            year = m.group("year")
            kind = m.group("kind").upper()
            mapped = _Q_TO_CUMULATIVE.get(kind, kind)
            if mapped in PERIOD_KINDS:
                return f"{year}-{mapped}"
    # Last-ditch: any 4-digit year + any kind keyword anywhere in the string
    year_m = re.search(r"(20\d{2})", s)
    kind_m = re.search(r"(Q1|H1|9M|FY|Q2|Q3|Q4)", s.upper())
    if year_m and kind_m:
        mapped = _Q_TO_CUMULATIVE.get(kind_m.group(1), kind_m.group(1))
        if mapped in PERIOD_KINDS:
            return f"{year_m.group(1)}-{mapped}"
    return None
