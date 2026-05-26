"""Smoke-test entry point for B3a fundamentals.

Usage (from the scrapers/ folder with .venv active):

    python -m rupeya.fundamentals OGDC          # 1 ticker, all recent filings
    python -m rupeya.fundamentals OGDC --max 1  # only the most-recent filing
    python -m rupeya.fundamentals OGDC LUCK ENGRO    # multiple tickers

This script is intentionally minimal — it exists to verify the pipeline
works end-to-end before we wire scrape_fundamentals.py + GitHub Actions.

It writes real rows to Supabase. The upsert is idempotent so running
again on the same ticker/period overwrites instead of duplicating.
"""

from __future__ import annotations

import argparse
import sys

from .. import config
from ..loader import RunLogger
from .pipeline import run_for_ticker

log = config.setup_logging()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rupeya.fundamentals",
        description="Run the B3a fundamentals pipeline for one or more tickers.",
    )
    parser.add_argument("tickers", nargs="+", help="Tickers, e.g. OGDC LUCK")
    parser.add_argument(
        "--max", type=int, default=None,
        help="Max filings to process per ticker (smoke testing).",
    )
    parser.add_argument(
        "--delay", type=float, default=None,
        help="Seconds between PDF fetches. Defaults to SCRAPE_DELAY_SECONDS.",
    )
    parser.add_argument(
        "--budget", type=float, default=None,
        help=(
            "Hard USD budget cap on Claude spend for this whole run. "
            "Pipeline aborts the next filing if estimated spend would "
            "exceed this. Recommended for any multi-stock backfill."
        ),
    )
    args = parser.parse_args(argv)

    log.info("=== Rupeya fundamentals run: %s ===", ", ".join(args.tickers))

    grand_total_cost = 0.0
    grand_total_rows = 0
    grand_total_errors = 0

    if args.budget is not None:
        log.info("Hard cost budget for this run: $%.2f", args.budget)

    with RunLogger(source="fundamentals_psx") as run:
        for ticker in args.tickers:
            # Pre-check budget before even starting a ticker
            if (
                args.budget is not None
                and grand_total_cost >= args.budget
            ):
                msg = (
                    f"Budget ${args.budget:.2f} already consumed "
                    f"(${grand_total_cost:.4f}) — skipping remaining tickers"
                )
                log.warning(msg)
                run.add_error(msg)
                break

            stats = run_for_ticker(
                ticker,
                max_filings=args.max,
                polite_delay_seconds=args.delay,
                cost_budget_usd=args.budget,
                cost_so_far_usd=grand_total_cost,
            )
            run.rows_written += stats.upserted_rows
            grand_total_cost += stats.estimated_cost_usd
            grand_total_rows += stats.upserted_rows
            grand_total_errors += len(stats.errors)
            for err in stats.errors:
                run.add_error(f"[{ticker}] {err}")

    log.info("=== RUN SUMMARY ===")
    log.info("Total rows upserted: %d", grand_total_rows)
    log.info("Total errors:        %d", grand_total_errors)
    log.info("Estimated cost:      ~$%.4f", grand_total_cost)

    return 0 if grand_total_errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
