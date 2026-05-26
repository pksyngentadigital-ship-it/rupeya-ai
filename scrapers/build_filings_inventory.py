"""Auto-discover + download fundamentals PDFs for every covered PSX stock.

Strategy per ticker:
  1. Try a curated list of "multi-year compilation" PDFs from company IR
     pages. These cover 5–10 years of data in a single document and are
     gold for in-session extraction.
  2. Then fetch the PSX DPS company page and identify the 2 most recent
     "financials" announcements (annual or quarterly/H1/9M). Download those.

All downloads land in scrapers/filings_archive/{TICKER}/.
A manifest CSV is written to scrapers/filings_archive/manifest.csv listing
what was found per stock.

Cost: $0. No LLM calls. Pure HTTP.

Usage:
    cd scrapers
    .venv\\Scripts\\activate
    python build_filings_inventory.py                # all covered tickers
    python build_filings_inventory.py --tickers OGDC LUCK ENGRO  # subset
    python build_filings_inventory.py --skip-existing  # don't re-download
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from rupeya import config, loader
from rupeya.fundamentals.index import (
    DPS_BASE,
    HEADERS,
    collect_announcements,
    fetch_company_page,
)

log = config.setup_logging()

ARCHIVE_DIR = Path(__file__).resolve().parent / "filings_archive"
MANIFEST_PATH = ARCHIVE_DIR / "manifest.csv"


# ---------------------------------------------------------------------------
# Curated multi-year compilation URLs.
# These come from Gemini Deep Research's cited sources + manual additions
# as we discover them per stock. Adding URLs here is the main way to
# improve coverage for deep extraction.
#
# Each entry: TICKER → list of URLs to PDFs containing multi-year data.
# ---------------------------------------------------------------------------
KNOWN_COMPILATION_URLS: dict[str, list[str]] = {
    "OGDC": [
        "https://www.ogdcl.com/sites/default/files/Six%20Years%20Performance-2022.pdf",
    ],
    "ENGRO": [
        "https://www.engro.com/app/media/2025/03/ECORP-Annual-Report-2024.pdf",
    ],
    "LUCK": [
        "https://www.lucky-cement.com/wp-content/uploads/2022/09/Financial-Ratios-for-website.pdf",
        "https://www.lucky-cement.com/wp-content/uploads/2025/06/Financial-Ratios-at-Lucky-Cements.pdf",
        "https://www.lucky-cement.com/wp-content/themes/luckycement/pdf/financial%20ratios/Six%20Year%20at%20a%20Glance.pdf",
    ],
    "MCB": [
        "https://www.mcb.com.pk/assets/documents/Financial-Highlights-Key-Ratios.pdf",
        "https://www.mcb.com.pk/assets/documents/Financial-Highlights-Key-Ratios-14-03-25.pdf",
    ],
    "MEBL": [
        "https://www.meezanbank.com/wp-content/themes/mbl/downloads/annualreport2025.pdf",
        "https://www.meezanbank.com/wp-content/themes/mbl/downloads/annualreport20.pdf",
    ],
    "PSO": [
        "https://psopk.com/files/financial-reports/annual/2024/PSO-Annual-Report-2024.pdf",
    ],
    "PPL": [
        "https://www.ppl.com.pk/sites/default/files/2024-10/PPL%20AR%202024.pdf",
    ],
    # More to be added as we discover IR pages with multi-year compilations.
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def _download(url: str, timeout: float = 60.0) -> bytes:
    log.debug("GET %s", url)
    with httpx.Client(
        headers=HEADERS, timeout=timeout, follow_redirects=True, http2=False
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def _filename_for_url(url: str, label: str) -> str:
    """Produce a stable, human-readable filename for the downloaded PDF."""
    parsed = urlparse(url)
    # Last path segment, sans query string
    name = Path(parsed.path).name or "file.pdf"
    # Drop URL-encoded spaces
    name = name.replace("%20", "_")
    if not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"
    return f"{label}__{name}"


def _save_pdf(content: bytes, target: Path) -> bool:
    if not content.startswith(b"%PDF"):
        log.warning(
            "  %s: response is not a PDF (%r). Skipping.",
            target.name, content[:16],
        )
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    log.info("  saved → %s (%d KB)", target.name, len(content) // 1024)
    return True


# ---------------------------------------------------------------------------
# Per-ticker workflow
# ---------------------------------------------------------------------------


def process_ticker(
    ticker: str,
    skip_existing: bool,
    delay: float,
) -> dict:
    """Run discovery + download for one ticker. Returns a manifest dict."""
    ticker = ticker.upper()
    ticker_dir = ARCHIVE_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)

    found_files: list[str] = []
    errors: list[str] = []

    # ---- (1) curated multi-year compilations ----
    for url in KNOWN_COMPILATION_URLS.get(ticker, []):
        fname = _filename_for_url(url, "compilation")
        target = ticker_dir / fname
        if skip_existing and target.exists():
            log.info("  [skip exists] %s", fname)
            found_files.append(str(target))
            continue
        try:
            content = _download(url)
        except Exception as e:  # noqa: BLE001
            errors.append(f"compilation download failed ({url}): {e}")
            log.warning("  compilation fetch failed for %s: %s", url, e)
            continue
        if _save_pdf(content, target):
            found_files.append(str(target))
        if delay > 0:
            time.sleep(delay)

    # ---- (2) PSX DPS most-recent financial filings ----
    try:
        html = fetch_company_page(ticker)
    except Exception as e:  # noqa: BLE001
        errors.append(f"DPS page fetch failed: {e}")
        log.warning("  DPS page fetch failed: %s", e)
        return {
            "ticker": ticker,
            "files_count": len(found_files),
            "files": found_files,
            "errors": errors,
        }

    anns = collect_announcements(html)
    financials = [a for a in anns if a.type == "financials"]
    # Keep up to 4 most recent financial filings — typically gives us the
    # latest annual + half-yearly + quarterly + 9-month variants. Each PDF
    # is small (<5MB) so the storage cost is trivial.
    for ann in financials[:4]:
        url = ann.absolute_url
        fname = _filename_for_url(url, f"psx_{ann.date_text.replace(' ', '_').replace(',', '')}")
        target = ticker_dir / fname
        if skip_existing and target.exists():
            log.info("  [skip exists] %s", fname)
            found_files.append(str(target))
            continue
        try:
            content = _download(url)
        except Exception as e:  # noqa: BLE001
            errors.append(f"PSX filing download failed ({url}): {e}")
            log.warning("  PSX filing fetch failed: %s", e)
            continue
        if _save_pdf(content, target):
            found_files.append(str(target))
        if delay > 0:
            time.sleep(delay)

    return {
        "ticker": ticker,
        "files_count": len(found_files),
        "files": found_files,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python build_filings_inventory.py",
        description=(
            "Auto-discover + download fundamentals PDFs for covered PSX stocks. "
            "Output goes to scrapers/filings_archive/{TICKER}/."
        ),
    )
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Restrict to specific tickers. Defaults to all covered.",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Don't re-download files that already exist on disk.",
    )
    parser.add_argument(
        "--delay", type=float, default=None,
        help="Seconds between downloads. Defaults to SCRAPE_DELAY_SECONDS.",
    )
    args = parser.parse_args(argv)

    delay = float(config.SCRAPE_DELAY_SECONDS) if args.delay is None else args.delay

    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        tickers = loader.get_covered_tickers()

    if not tickers:
        log.error("No tickers to process.")
        return 1

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    log.info("=== Filings inventory: %d ticker(s) ===", len(tickers))
    log.info("Archive directory: %s", ARCHIVE_DIR)
    log.info("Curated compilation URLs available for: %s",
             ", ".join(sorted(KNOWN_COMPILATION_URLS.keys())))

    manifest_rows: list[dict] = []
    for i, ticker in enumerate(tickers, 1):
        log.info("[%d/%d] %s", i, len(tickers), ticker)
        entry = process_ticker(ticker, args.skip_existing, delay)
        manifest_rows.append(entry)

    # Write manifest CSV
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "files_count", "files", "errors"])
        for r in manifest_rows:
            w.writerow([
                r["ticker"],
                r["files_count"],
                "|".join(r["files"]),
                "|".join(r["errors"]) if r["errors"] else "",
            ])

    # Summary
    total_files = sum(r["files_count"] for r in manifest_rows)
    tickers_with_files = sum(1 for r in manifest_rows if r["files_count"] > 0)
    tickers_with_errors = sum(1 for r in manifest_rows if r["errors"])

    log.info("=== INVENTORY SUMMARY ===")
    log.info("Tickers attempted:      %d", len(tickers))
    log.info("Tickers with ≥1 file:   %d", tickers_with_files)
    log.info("Tickers with errors:    %d", tickers_with_errors)
    log.info("Total PDFs downloaded:  %d", total_files)
    log.info("Manifest:               %s", MANIFEST_PATH)

    return 0 if tickers_with_files > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
