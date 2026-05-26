"""PSX filing PDF → structured FundamentalRow via Claude Haiku.

Cost discipline:
  • Always use Haiku (rupeya.llm_models.FUNDAMENTALS_EXTRACTION_MODEL).
  • Caller is expected to have already checked skip-if-exists in the DB.
  • Token usage is returned to the caller for telemetry in scrape_runs.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from .index import HEADERS, DPS_BASE, DEBUG_DUMP_DIR
from .models import FundamentalRow, UNIT_FACTORS, normalize_period
from .. import config  # noqa: F401  — side-effect: loads .env
from ..llm_models import FUNDAMENTALS_EXTRACTION_MODEL

log = logging.getLogger("rupeya.fundamentals.extractor")

# Per-1M-token pricing for cost telemetry (Haiku 4.5). Update if pricing changes.
_HAIKU_INPUT_USD_PER_M = 1.0
_HAIKU_OUTPUT_USD_PER_M = 5.0


EXTRACTION_PROMPT = """\
You are extracting structured fundamentals from a Pakistan Stock Exchange \
(PSX) company filing PDF. Return ONLY valid JSON — no commentary, no \
markdown fences, no explanations outside the JSON object.

The schema to fill is below. Match it EXACTLY.

{
  "ticker": "<string, the ticker symbol provided to you>",
  "period": "<canonical period code; see rules below>",
  "period_end_date": "<ISO date YYYY-MM-DD of the last day of the period covered by this filing>",
  "currency": "<e.g. PKR>",
  "units": "<one of: actuals, thousands, millions, billions>",
  "revenue": <number or null — total revenue / sales / turnover for the period>,
  "net_income": <number or null — profit after taxation attributable to ordinary shareholders>,
  "eps": <number or null — basic earnings per share in PKR; not multiplied by units>,
  "book_value": <number or null — total equity attributable to ordinary shareholders at period end>,
  "debt": <number or null — total interest-bearing debt (short + long term loans, lease liabilities) at period end>,
  "cash": <number or null — cash and cash equivalents at period end>,
  "fcf": <number or null — CFO minus CapEx if BOTH are disclosed in cash flow statement; otherwise null>,
  "dividend_per_share": <number or null — declared dividend per share for the period in PKR>,
  "notes": "<short string flagging anything missing, unusual, or ambiguous>"
}

PERIOD CODE RULES (CRITICAL):
This is the canonical period format we store in our DB. Use it exactly.

  • "YYYY-Q1"  →  first 3 months of the issuer's fiscal year (cumulative)
  • "YYYY-H1"  →  first 6 months of the issuer's fiscal year (half-year cumulative)
  • "YYYY-9M"  →  first 9 months of the issuer's fiscal year (Pakistani "Q3" filing)
  • "YYYY-FY"  →  full fiscal year (12 months)

Where YYYY is the fiscal year in which the period ENDS.

Pakistani fiscal-year conventions you'll see in PSX filings:
  • Oil & Gas, fertilizer, cement, food companies: Jul-Jun fiscal year.
    A "9-month report" ending 31 March covers Jul → Mar and is labelled "YYYY-9M"
    where YYYY is the calendar year of June (so a Mar-2026 9M filing is "2026-9M").
  • Banks (HBL, MCB, UBL etc) and some others: calendar fiscal year (Jan-Dec).
    A filing ending 31 March of calendar year 2026 is "2026-Q1".

If the filing covers 3 months of operations → period_kind = Q1.
If the filing covers 6 months / "half year" → H1.
If the filing covers 9 months / "nine months" → 9M.
If the filing covers 12 months / "annual" / "year ended" → FY.

DATA RULES:
- Numeric values must be raw numbers (no commas, no currency symbols).
- The "units" field tells us the scale (thousands / millions / etc.).
- "book_value" = TOTAL equity attributable to ordinary shareholders, NOT book value per share.
- "debt" excludes trade payables and tax payables; INCLUDES short-term borrowings, long-term loans, and lease liabilities (any interest-bearing).
- "fcf" — only compute it if BOTH cash from operations AND capital expenditure are disclosed in the cash flow statement. Otherwise return null.
- "dividend_per_share" — total interim + final per share declared for this period.
- For 9-month / half-yearly filings, revenue/net_income/eps are CUMULATIVE figures (don't try to compute standalone-quarter values).
- When in doubt, return null and explain in "notes". Do NOT guess.
"""


# --- Public API --------------------------------------------------------------


@dataclass
class ExtractionResult:
    """Bundle of the structured row + telemetry from one Claude call."""

    row: FundamentalRow | None
    raw_response: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    error: str | None = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def _download_pdf(url: str, timeout: float = 60.0) -> bytes:
    if url.startswith("/"):
        url = DPS_BASE + url
    log.info("GET PDF %s", url)
    with httpx.Client(
        headers=HEADERS, timeout=timeout, follow_redirects=True, http2=False
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def extract_fundamentals_from_pdf(
    ticker: str,
    pdf_url: str,
    *,
    cache_pdf: bool = True,
) -> ExtractionResult:
    """Download a PSX filing PDF, extract fundamentals via Claude Haiku.

    Returns ExtractionResult — telemetry is populated even on failure so the
    orchestrator can log accurate cost-per-run numbers.
    """
    try:
        pdf_bytes = _download_pdf(pdf_url)
    except Exception as e:  # noqa: BLE001
        return ExtractionResult(
            row=None, raw_response="",
            input_tokens=0, output_tokens=0, estimated_cost_usd=0,
            error=f"PDF download failed: {e}",
        )

    if not pdf_bytes.startswith(b"%PDF"):
        bad_path = DEBUG_DUMP_DIR / f"fundamentals_{ticker}_bad.bin"
        DEBUG_DUMP_DIR.mkdir(parents=True, exist_ok=True)
        bad_path.write_bytes(pdf_bytes)
        return ExtractionResult(
            row=None, raw_response="",
            input_tokens=0, output_tokens=0, estimated_cost_usd=0,
            error=(
                f"Downloaded file is not a PDF (first 16 bytes: {pdf_bytes[:16]!r}). "
                f"Saved to {bad_path}."
            ),
        )

    if cache_pdf:
        DEBUG_DUMP_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = DEBUG_DUMP_DIR / f"fundamentals_{ticker}_latest.pdf"
        try:
            cache_path.write_bytes(pdf_bytes)
        except OSError as e:
            log.warning("Could not cache PDF: %s", e)

    # --- Call Claude ---
    try:
        from anthropic import Anthropic
    except ImportError:
        return ExtractionResult(
            row=None, raw_response="",
            input_tokens=0, output_tokens=0, estimated_cost_usd=0,
            error="anthropic SDK not installed",
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return ExtractionResult(
            row=None, raw_response="",
            input_tokens=0, output_tokens=0, estimated_cost_usd=0,
            error="ANTHROPIC_API_KEY missing from environment",
        )

    client = Anthropic(api_key=api_key)
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")

    try:
        resp = client.messages.create(
            model=FUNDAMENTALS_EXTRACTION_MODEL,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT + f"\n\nThe ticker is {ticker}.",
                    },
                ],
            }],
        )
    except Exception as e:  # noqa: BLE001
        return ExtractionResult(
            row=None, raw_response="",
            input_tokens=0, output_tokens=0, estimated_cost_usd=0,
            error=f"Claude call failed: {type(e).__name__}: {e}",
        )

    usage = resp.usage
    cost = (
        (usage.input_tokens / 1_000_000) * _HAIKU_INPUT_USD_PER_M
        + (usage.output_tokens / 1_000_000) * _HAIKU_OUTPUT_USD_PER_M
    )

    raw_text = resp.content[0].text.strip()
    # Strip ```json fences if Haiku added them
    if raw_text.startswith("```"):
        raw_text = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.DOTALL
        )

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        return ExtractionResult(
            row=None, raw_response=raw_text,
            input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
            estimated_cost_usd=cost,
            error=f"Claude returned invalid JSON: {e}",
        )

    row = _parsed_to_row(ticker, pdf_url, parsed)
    if row is None:
        return ExtractionResult(
            row=None, raw_response=raw_text,
            input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
            estimated_cost_usd=cost,
            error="Could not normalize Claude output into FundamentalRow",
        )

    return ExtractionResult(
        row=row, raw_response=raw_text,
        input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
        estimated_cost_usd=cost,
        error=None,
    )


# --- Internal: JSON dict → FundamentalRow ------------------------------------


def _parsed_to_row(
    ticker: str, source_url: str, parsed: dict
) -> FundamentalRow | None:
    """Apply unit scaling, normalize period, build a FundamentalRow."""
    units = (parsed.get("units") or "").strip().lower()
    factor = UNIT_FACTORS.get(units, 1)
    if units and units not in UNIT_FACTORS:
        log.warning(
            "Unknown units value %r for %s — treating as actuals (factor=1)",
            units, ticker,
        )

    period_raw = parsed.get("period") or ""
    period = normalize_period(period_raw)
    if period is None:
        log.warning("Could not normalize period %r for %s", period_raw, ticker)
        return None

    end_date_raw = parsed.get("period_end_date")
    end_date: Date | None = None
    if end_date_raw:
        try:
            end_date = Date.fromisoformat(end_date_raw)
        except (ValueError, TypeError):
            log.warning(
                "Bad period_end_date %r for %s — leaving null", end_date_raw, ticker,
            )

    def scale(key: str) -> float | None:
        v = parsed.get(key)
        if v is None:
            return None
        try:
            return float(v) * factor
        except (TypeError, ValueError):
            return None

    def passthrough(key: str) -> float | None:
        """For per-share values that don't get unit-scaled."""
        v = parsed.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return FundamentalRow(
        ticker=ticker.upper(),
        period=period,
        period_end_date=end_date,
        revenue=scale("revenue"),
        net_income=scale("net_income"),
        eps=passthrough("eps"),
        book_value=scale("book_value"),
        debt=scale("debt"),
        cash=scale("cash"),
        fcf=scale("fcf"),
        dividend_per_share=passthrough("dividend_per_share"),
        source="psx_pdf_claude",
        source_url=source_url,
        notes=parsed.get("notes") or None,
    )
