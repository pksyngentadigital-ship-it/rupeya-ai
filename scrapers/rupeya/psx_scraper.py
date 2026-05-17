"""
Rupeya.ai — PSX market data scraper.

Fetches end-of-day prices from PSX's public Market Watch page. The page is
a single HTML document with a table containing one row per listed stock
(symbol + OHLCV + change). We parse it with selectolax and return a list
of PriceRecord objects.

Design:
  • One HTTP request gets prices for ALL listed PSX stocks (~600+).
  • We filter to our covered universe afterwards.
  • Retries with exponential backoff on transient errors.
  • Polite User-Agent identifies us (per blueprint Section 17, we want to
    be a good scraping citizen).
  • Saves the raw HTML to disk on parse failure for debugging.

This is the primary source for B2. If PSX changes the page structure or
blocks us, see DEBUG_DUMP_PATH for the last raw response.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path
from typing import Iterable

import httpx
from selectolax.parser import HTMLParser
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from . import config

log = logging.getLogger("rupeya.psx_scraper")

PSX_MARKET_WATCH_URL = "https://dps.psx.com.pk/market-watch"

# PSX uses slightly different symbols than common-usage tickers in a few
# cases. Map PSX-side symbols → our canonical ticker so app-side code stays
# consistent. Discovered via debug_psx.py; extend as more mismatches surface.
PSX_TO_CANONICAL: dict[str, str] = {
    "ENGROH": "ENGRO",
    "ABOT": "ABBOTT",
    "BERG": "BERGER",
    "UPFL": "UNILEVER",
}

# Browser-realistic headers — PSX serves slightly different HTML to bots.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Rupeya.ai/0.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
}

# Where to dump the raw HTML for offline parse debugging
DEBUG_DUMP_PATH = Path(__file__).resolve().parent.parent / ".cache" / "psx_market_watch.html"


@dataclass
class PriceRecord:
    """One end-of-day price row for a single ticker."""

    ticker: str
    date: Date
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: int | None


# ---------- HTTP layer ----------


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def _http_get(url: str, timeout: float = 30.0) -> httpx.Response:
    log.debug("GET %s", url)
    with httpx.Client(
        headers=HEADERS,
        timeout=timeout,
        follow_redirects=True,
        http2=False,
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp


def _dump_html_for_debug(html: str) -> None:
    """Write last raw response to disk so we can grep/inspect parse failures."""
    try:
        DEBUG_DUMP_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_DUMP_PATH.write_text(html, encoding="utf-8")
        log.info("Raw HTML saved to %s (%d bytes)", DEBUG_DUMP_PATH, len(html))
    except OSError as e:
        log.warning("Could not save debug HTML: %s", e)


# ---------- Parsing ----------


def _parse_float(s: str) -> float | None:
    """Parse PSX number formats: '1,234.56' -> 1234.56, '-' / 'N/A' -> None."""
    s = (s or "").replace(",", "").strip()
    if not s or s in ("-", "N/A", "n/a", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_int(s: str) -> int | None:
    f = _parse_float(s)
    return int(f) if f is not None else None


def _parse_market_watch_table(html: str, as_of: Date) -> list[PriceRecord]:
    """
    Parse the Market Watch HTML and return one PriceRecord per data row.

    PSX column order (verified via debug_psx.py on 2026-05-17):
         0  SYMBOL
         1  SECTOR        (numeric code)
         2  LISTED IN     (index memberships)
         3  LDCP          (last day close)
         4  OPEN
         5  HIGH
         6  LOW
         7  CURRENT       (treated as close for EOD scrape)
         8  CHANGE
         9  CHANGE (%)
        10  VOLUME
    """
    tree = HTMLParser(html)

    candidates = [
        "table#marketWatchTable tbody tr",
        "table.tbl tbody tr",
        "table tbody tr",
    ]
    rows_nodes = []
    for selector in candidates:
        rows_nodes = tree.css(selector)
        if rows_nodes:
            log.debug("Matched %d rows with selector '%s'", len(rows_nodes), selector)
            break

    if not rows_nodes:
        log.error("No table rows found on Market Watch page — page structure changed?")
        _dump_html_for_debug(html)
        return []

    records: list[PriceRecord] = []
    skipped = 0

    for row in rows_nodes:
        cells = row.css("td")
        if len(cells) < 11:
            skipped += 1
            continue

        try:
            psx_symbol = cells[0].text(strip=True).upper()
            if not psx_symbol or not psx_symbol.replace("-", "").isalnum():
                skipped += 1
                continue

            # Strip "XD" suffix (ex-dividend marker — PSX uses e.g. OGDCXD on
            # the ex-div trading day for OGDC). After stripping, apply the
            # explicit alias map (e.g. ENGROH → ENGRO).
            canonical = psx_symbol[:-2] if psx_symbol.endswith("XD") else psx_symbol
            ticker = PSX_TO_CANONICAL.get(canonical, canonical)

            open_p = _parse_float(cells[4].text(strip=True))
            high = _parse_float(cells[5].text(strip=True))
            low = _parse_float(cells[6].text(strip=True))
            close = _parse_float(cells[7].text(strip=True))
            volume = _parse_int(cells[10].text(strip=True))

            if close is None:
                skipped += 1
                continue

            records.append(
                PriceRecord(
                    ticker=ticker,
                    date=as_of,
                    open=open_p,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )
            )
        except (IndexError, ValueError) as e:
            log.warning("Parse error on row (sym=%s): %s", cells[0].text() if cells else "?", e)
            skipped += 1

    log.info("Parsed %d price records (skipped %d)", len(records), skipped)
    return records


# ---------- Public API ----------


def fetch_market_watch(as_of: Date | None = None) -> list[PriceRecord]:
    """
    Fetch the PSX Market Watch page and return EOD prices for every listed
    ticker that has a current price. `as_of` defaults to today's date.
    """
    as_of = as_of or Date.today()
    log.info("Fetching PSX Market Watch (date=%s)", as_of.isoformat())

    resp = _http_get(PSX_MARKET_WATCH_URL)
    log.info(
        "Market Watch: %d bytes, content-type=%s",
        len(resp.content),
        resp.headers.get("content-type", "?"),
    )

    records = _parse_market_watch_table(resp.text, as_of)

    if not records:
        # Save HTML so the next debugging session has it
        _dump_html_for_debug(resp.text)

    return records


def filter_to_covered(
    records: list[PriceRecord], covered_tickers: Iterable[str]
) -> list[PriceRecord]:
    """Keep only records for tickers in our covered universe."""
    covered = {t.upper() for t in covered_tickers}
    filtered = [r for r in records if r.ticker in covered]
    log.info(
        "Filtered to covered universe: %d/%d records kept",
        len(filtered),
        len(records),
    )
    return filtered
