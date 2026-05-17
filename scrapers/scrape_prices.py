"""
Rupeya.ai — Run the daily PSX price scrape.

Orchestrates the end-to-end flow:
    1. Load covered tickers from Supabase
    2. Hit PSX Market Watch
    3. Filter to our universe
    4. Upsert into prices_daily
    5. Record the run in scrape_runs

Idempotent. Safe to run any number of times per day — re-runs overwrite
the same (ticker, date) rows.

Usage:
    cd scrapers
    .venv\\Scripts\\activate
    python scrape_prices.py

To smoke-test on a smaller subset, set SCRAPE_LIMIT in .env:
    SCRAPE_LIMIT=5  # only persist first 5 tickers from the filtered universe
"""

from __future__ import annotations

import sys

from rupeya import config, loader, psx_scraper

log = config.setup_logging()


def main() -> int:
    log.info("=== Rupeya PSX price scrape starting ===")

    with loader.RunLogger(source="psx_market_watch") as run:
        try:
            # 1. Get covered tickers from DB
            covered = loader.get_covered_tickers()
            if not covered:
                run.add_error("No covered tickers in DB — did you run seed_universe.py?")
                return 1

            # 2. Scrape PSX
            all_records = psx_scraper.fetch_market_watch()
            if not all_records:
                run.add_error(
                    "PSX Market Watch returned 0 records — page structure may have changed. "
                    f"Raw HTML dumped to {psx_scraper.DEBUG_DUMP_PATH}."
                )
                return 2

            # 3. Filter to universe
            records = psx_scraper.filter_to_covered(all_records, covered)
            if not records:
                run.add_error(
                    f"No covered tickers matched. Scraped {len(all_records)} tickers, "
                    f"expected to find {len(covered)} in our universe."
                )
                return 3

            # 4. Optional limit for smoke testing
            if config.SCRAPE_LIMIT > 0:
                log.info(
                    "SCRAPE_LIMIT=%d active — truncating to first %d records",
                    config.SCRAPE_LIMIT,
                    config.SCRAPE_LIMIT,
                )
                records = records[: config.SCRAPE_LIMIT]

            # 5. Upsert
            written = loader.upsert_prices(records)
            run.rows_written = written

            # 6. Sanity report
            missing = set(covered) - {r.ticker for r in records}
            if missing:
                missing_str = ", ".join(sorted(missing)[:10])
                more = f" (+{len(missing) - 10} more)" if len(missing) > 10 else ""
                run.add_error(
                    f"{len(missing)} covered ticker(s) not found in scrape: {missing_str}{more}"
                )

            log.info("=== Scrape complete: wrote %d rows ===", written)
            return 0

        except Exception as e:  # noqa: BLE001 — top-level handler
            log.exception("Fatal error during scrape: %s", e)
            run.add_error(f"Fatal: {type(e).__name__}: {e}")
            return 99


if __name__ == "__main__":
    sys.exit(main())
