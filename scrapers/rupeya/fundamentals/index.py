"""PSX DPS company-page fetcher + announcement classifier.

The DPS company page (e.g. dps.psx.com.pk/company/OGDC) is a static HTML
document with two relevant sections for B3a:

  1. A 'Latest Announcements' feed of ~14 recent PDF filings, each
     wrapped in context text like "Apr 29, 2026 — FINANCIAL RESULTS FOR
     THE PERIOD ENDED MARCH 31 2026".

  2. Three inline financial tables (annual headline, quarterly headline,
     annual ratios). We don't parse those here — the orchestrator may
     use them as a cross-check on Claude's PDF extraction.

This module's job is to fetch the page and classify each announcement.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
from selectolax.parser import HTMLParser
from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger("rupeya.fundamentals.index")

DPS_BASE = "https://dps.psx.com.pk"

# Browser-realistic headers — matches scrapers/rupeya/psx_scraper.py
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Rupeya.ai/0.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
}

# Where to dump raw HTML on parse failure for debugging
DEBUG_DUMP_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"

# --- Announcement classification ---------------------------------------------

# Types we care about for B3a. Any other text → "other" → ignored.
ANNOUNCEMENT_TYPES = (
    "financials",          # quarterly / half-yearly / annual financial statements
    "transmission_letter", # 1-page cover sheet; usually attached to financials, skip
    "dividend",            # cash / bonus dividend declarations
    "corporate_action",    # board meetings, AGMs, M&A, rights issues
    "shariah_disclosure",  # Shariah-compliance disclosures
    "other",
)

_DATE_RE = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}"
)


@dataclass
class Announcement:
    """One row from the PSX DPS announcements feed."""

    href: str               # path or absolute URL to the PDF
    date_text: str          # raw date string e.g. "Apr 29, 2026"
    context: str            # full announcement context text
    type: str               # one of ANNOUNCEMENT_TYPES

    @property
    def absolute_url(self) -> str:
        if self.href.startswith("http"):
            return self.href
        return DPS_BASE + self.href


def classify_announcement(ctx: str) -> str:
    """Bucket an announcement by its title/context text.

    Order matters: meetings/AGM checks come first because phrases like
    "Annual General Meeting" contain "annual" which would otherwise
    incorrectly match the financial-report patterns below.
    """
    c = ctx.lower()

    # ---- Meetings / corporate actions ----
    # These take priority over "annual report" / "quarterly report" matching
    # because AGM titles often contain those keywords.
    if (
        "annual general meeting" in c
        or "extraordinary general meeting" in c
        or " agm " in f" {c} "
        or " egm " in f" {c} "
        or "board meeting" in c
        or "closed period" in c
        or "rights issue" in c
        or "bonus issue" in c
        or "share buyback" in c
        or "buy back" in c
        or "resolutions passed" in c
        or "pattern of shareholding" in c
    ):
        return "corporate_action"

    # ---- Dividends ----
    if (
        "interim cash dividend" in c
        or "final cash dividend" in c
        or "cash dividend" in c
        or "credit of" in c and "dividend" in c
    ):
        return "dividend"

    # ---- Shariah disclosures ----
    if "shariah" in c:
        return "shariah_disclosure"

    # ---- Financial filings (broad — this is the main fix) ----
    # PSX practice: most issuers file a "Transmission of [Annual|Quarterly|
    # Half Yearly|9-month] Report" — and *that filing IS the actual
    # financial report*, with the audited statements attached. So we treat
    # transmission filings as financials, not as separate "letter" stubs.
    financial_keywords = (
        # Explicit "FINANCIAL RESULTS" headlines
        "financial results for the period",
        "financial results",
        # Statement / audited references
        "financial statement for",
        "financial statements for",
        "audited financial statement",
        "audited annual financial",
        # Transmission filings (the most common form on PSX)
        "transmission of audited",
        "transmission of quarterly report",
        "transmission of half yearly report",
        "transmission of half-yearly report",
        "transmission of nine months",
        "transmission of 9 months",
        "transmission of annual report",
        "transmission of annual audited",
        # Bare report references
        "quarterly report for",
        "half yearly report for",
        "half-yearly report for",
        "annual report for",
        "nine months report",
    )
    for kw in financial_keywords:
        if kw in c:
            return "financials"

    return "other"


# --- HTTP layer --------------------------------------------------------------

# Some PSX symbols differ from our canonical tickers (we use the longer
# name in the stocks table; PSX's company page uses an abbreviated symbol).
# Restricted to confirmed problem cases — adding speculative entries here
# would break currently-working URLs (e.g. /company/ENGRO already resolves).
_CANONICAL_TO_PSX_SYMBOL: dict[str, str] = {
    "ABBOTT": "ABOT",
    "BERGER": "BERG",
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def fetch_company_page(ticker: str, timeout: float = 30.0) -> str:
    """Fetch dps.psx.com.pk/company/{TICKER} and return raw HTML.

    Resolves canonical-to-PSX symbol mismatches (e.g., ABBOTT → ABOT) via
    _CANONICAL_TO_PSX_SYMBOL so callers can pass our stocks-table ticker
    without worrying about PSX's abbreviated naming.
    """
    psx_symbol = _CANONICAL_TO_PSX_SYMBOL.get(ticker.upper(), ticker.upper())
    url = f"{DPS_BASE}/company/{psx_symbol}"
    log.info("GET %s", url)
    with httpx.Client(
        headers=HEADERS, timeout=timeout, follow_redirects=True, http2=False
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
    log.debug(
        "Company page %s: %d bytes, content-type=%s",
        ticker, len(resp.content), resp.headers.get("content-type", "?"),
    )
    return resp.text


# --- Announcement extraction -------------------------------------------------


def collect_announcements(html: str) -> list[Announcement]:
    """Walk the page DOM, return one Announcement per PDF link.

    Each PDF anchor is wrapped in context that includes a date and a title.
    We climb a few levels above the anchor to find that context.
    """
    tree = HTMLParser(html)
    results: list[Announcement] = []
    seen_hrefs: set[str] = set()

    for a in tree.css("a[href]"):
        href = (a.attributes.get("href") or "").strip()
        if ".pdf" not in href.lower():
            continue
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        # Walk up to the nearest row-like container for context.
        parent = a.parent
        for _ in range(4):
            if parent is None:
                break
            if parent.tag in ("tr", "li", "div"):
                break
            parent = parent.parent
        ctx = parent.text(strip=True) if parent else ""

        m = _DATE_RE.search(ctx)
        date_text = m.group(0) if m else ""

        results.append(
            Announcement(
                href=href,
                date_text=date_text,
                context=ctx,
                type=classify_announcement(ctx),
            )
        )

    log.info("Parsed %d announcement(s) from page", len(results))
    by_type: dict[str, int] = {}
    for r in results:
        by_type[r.type] = by_type.get(r.type, 0) + 1
    log.info("Announcements by type: %s", by_type)
    return results


def dump_debug_html(ticker: str, html: str) -> Path:
    """Save raw HTML for offline inspection. Returns the path written."""
    DEBUG_DUMP_DIR.mkdir(parents=True, exist_ok=True)
    path = DEBUG_DUMP_DIR / f"fundamentals_{ticker}.html"
    path.write_text(html, encoding="utf-8")
    log.info("Dumped raw HTML → %s", path)
    return path
