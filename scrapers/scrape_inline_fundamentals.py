"""Top-level runner for inline PSX DPS fundamentals scraping.

For each covered ticker in public.stocks, fetch the DPS company page,
parse the annual highlights table, and upsert one row per fiscal year
to public.fundamentals_quarterly.

The result is shallow data (3 of 8 columns) for the full universe.
Use this to bootstrap mid-caps that don't have a deep extraction yet.

Usage:
    cd scrapers
    .venv\\Scripts\\activate
    python scrape_inline_fundamentals.py                      # all covered tickers
    python scrape_inline_fundamentals.py --tickers OGDC LUCK  # subset

Cost: $0. No LLM calls. Just HTTP requests + HTML parsing.
"""

from __future__ import annotations

import argparse
import sys
import time

from rupeya import config, loader
from rupeya.fundamentals.index import dump_debug_html, fetch_company_page
from rupeya.fundamentals.inline_parser import parse_annual_table
from rupeya.loader import RunLogger

log = config.setup_logging()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scrape_inline_fundamentals.py",
        description="Scrape inline annual highlights tables from PSX DPS.",
    )
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Restrict to specific tickers. Defaults to all covered.",
    )
    parser.add_argument(
        "--delay", type=float, default=None,
        help="Seconds between requests. Defaults to SCRAPE_DELAY_SECONDS.",
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

    log.info("=== Inline fundamentals scrape: %d ticker(s) ===", len(tickers))

    all_rows = []
    per_ticker: dict[str, int] = {}
    fetch_failures: list[str] = []
    parse_failures: list[str] = []

    with RunLogger(source="fundamentals_psx_inline") as run:
        for i, ticker in enumerate(tickers, 1):
            log.info("[%d/%d] %s", i, len(tickers), ticker)
            try:
                html = fetch_company_page(ticker)
            except Exception as e:  # noqa: BLE001
                fetch_failures.append(ticker)
                run.add_error(f"{ticker}: fetch failed: {e}")
                log.warning("[%s] fetch failed: %s", ticker, e)
                if delay > 0 and i < len(tickers):
                    time.sleep(delay)
                continue

            try:
                rows = parse_annual_table(html, ticker)
            except Exception as e:  # noqa: BLE001
                parse_failures.append(ticker)
                run.add_error(f"{ticker}: parse failed: {e}")
                log.exception("[%s] parse failed", ticker)
                dump_debug_html(ticker, html)
                if delay > 0 and i < len(tickers):
                    time.sleep(delay)
                continue

            if not rows:
                parse_failures.append(ticker)
                run.add_error(f"{ticker}: 0 rows extracted")
                log.warning("[%s] no rows extracted (saving HTML for inspection)", ticker)
                dump_debug_html(ticker, html)
            else:
                per_ticker[ticker] = len(rows)
                all_rows.extend(rows)

            if delay > 0 and i < len(tickers):
                time.sleep(delay)

        # Upsert everything in one shot
        if all_rows:
            try:
                written = loader.upsert_fundamentals(all_rows)
                run.rows_written = written
                log.info("Upserted %d row(s)", written)
            except Exception as e:  # noqa: BLE001
                run.add_error(f"upsert failed: {e}")
                log.exception("Upsert failed")
                return 2

    log.info("=== INLINE SCRAPE SUMMARY ===")
    log.info("Tickers attempted:    %d", len(tickers))
    log.info("Tickers with rows:    %d", len(per_ticker))
    log.info("Total rows upserted:  %d", len(all_rows))
    log.info("Fetch failures:       %d (%s)",
             len(fetch_failures), ", ".join(fetch_failures[:10]) or "—")
    log.info("Parse failures:       %d (%s)",
             len(parse_failures), ", ".join(parse_failures[:10]) or "—")

    return 0


if __name__ == "__main__":
    sys.exit(main())
