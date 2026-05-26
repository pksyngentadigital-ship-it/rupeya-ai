"""Rupeya.ai fundamentals scraper — Phase B3a.

Pipeline:
    dps.psx.com.pk/company/{TICKER}    (filings_index)
        → list of "Financial Results / Financial Statement" announcements
        → download each PDF                                (extractor)
        → Claude Haiku → structured FundamentalRow         (extractor)
        → upsert into public.fundamentals_quarterly        (loader)

The orchestrator (pipeline.py) ties them together with a skip-if-exists
guard so re-runs are ~free.
"""

from .models import FundamentalRow, PERIOD_KINDS, normalize_period
from .index import (
    Announcement,
    collect_announcements,
    fetch_company_page,
    classify_announcement,
)
from .extractor import extract_fundamentals_from_pdf, EXTRACTION_PROMPT
from .pipeline import run_for_ticker

__all__ = [
    "FundamentalRow",
    "PERIOD_KINDS",
    "normalize_period",
    "Announcement",
    "fetch_company_page",
    "collect_announcements",
    "classify_announcement",
    "extract_fundamentals_from_pdf",
    "EXTRACTION_PROMPT",
    "run_for_ticker",
]
