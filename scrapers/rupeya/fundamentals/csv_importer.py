"""CSV importer for fundamentals data.

Reads scrapers/imports/*.csv files, validates against the schema,
normalizes periods/units, and upserts to public.fundamentals_quarterly.

Expected CSV header (must match exactly):
    ticker,period,period_end_date,currency,revenue,net_income,eps,
    book_value,debt,cash,fcf,dividend_per_share,source_url

Rules applied per row:
  • period is normalized to canonical (YYYY-Q1/H1/9M/FY) via models.normalize_period
  • Numeric cells with commas / "Rs" prefixes / whitespace are coerced.
  • Empty cells become None.
  • Rows missing ticker OR period are skipped.
  • Numeric values are assumed already in ABSOLUTE PKR. If a row's source
    reported in thousands/millions, the caller should have multiplied
    before writing the CSV (per the external-tool prompt's instructions).
  • source_url is preserved on the in-memory row for logging but is not
    written to fundamentals_quarterly (no column yet).

CLI:
    python -m rupeya.fundamentals.csv_importer
    python -m rupeya.fundamentals.csv_importer --file imports/batch_01.csv
    python -m rupeya.fundamentals.csv_importer --archive    # move imported files to imports/imported/
    python -m rupeya.fundamentals.csv_importer --dry-run     # parse + validate, no DB writes
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path

from .. import config
from ..loader import RunLogger, upsert_fundamentals
from .models import FundamentalRow, normalize_period

log = logging.getLogger("rupeya.fundamentals.csv_importer")

# --- Schema definition -------------------------------------------------------

EXPECTED_HEADER = [
    "ticker", "period", "period_end_date", "currency",
    "revenue", "net_income", "eps", "book_value",
    "debt", "cash", "fcf", "dividend_per_share", "source_url",
]

# Per-share fields (NOT multiplied by units factor — caller already provided
# them in PKR per share).
_PER_SHARE_FIELDS = {"eps", "dividend_per_share"}
_NUMERIC_FIELDS = {
    "revenue", "net_income", "eps", "book_value",
    "debt", "cash", "fcf", "dividend_per_share",
}

IMPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "imports"
ARCHIVE_DIR = IMPORTS_DIR / "imported"


# --- Parsing helpers ---------------------------------------------------------


def _coerce_number(raw: str) -> float | None:
    """Strip commas, currency symbols, whitespace, then parse float.

    Returns None for empty cells or values we can't interpret as numbers.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in ("null", "none", "n/a", "na", "-", "--"):
        return None
    # Drop currency tokens and parens for negatives
    s = re.sub(r"^\s*\(?(rs\.?|pkr|usd|\$)\s*", "", s, flags=re.IGNORECASE)
    s = s.replace(",", "").strip()
    # Parenthesised negatives e.g. "(1,234.56)" → "-1234.56"
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1].strip()
    try:
        return float(s)
    except ValueError:
        return None


def _coerce_date(raw: str) -> Date | None:
    if not raw:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    try:
        return Date.fromisoformat(raw)
    except (TypeError, ValueError):
        # Tolerate things like "2025-06-30T00:00:00" — split on T
        for sep in ("T", " "):
            if sep in raw:
                head = raw.split(sep)[0]
                try:
                    return Date.fromisoformat(head)
                except ValueError:
                    pass
        return None


@dataclass
class ImportStats:
    files_processed: int = 0
    rows_seen: int = 0
    rows_imported: int = 0
    rows_skipped_no_ticker: int = 0
    rows_skipped_bad_period: int = 0
    rows_skipped_other: int = 0
    rows_with_warnings: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


# --- Core parse routine ------------------------------------------------------


def parse_csv(path: Path, stats: ImportStats) -> list[FundamentalRow]:
    """Parse one CSV → list of FundamentalRow.

    Stats are mutated in place to record what happened.
    """
    rows_out: list[FundamentalRow] = []

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            stats.errors.append(f"{path.name}: empty file or no header")
            return rows_out

        # Verify header
        fields = [c.strip() for c in reader.fieldnames]
        missing = [c for c in EXPECTED_HEADER if c not in fields]
        if missing:
            stats.errors.append(
                f"{path.name}: missing required columns {missing}. "
                f"Found: {fields}"
            )
            return rows_out

        for row in reader:
            stats.rows_seen += 1

            ticker = (row.get("ticker") or "").strip().upper()
            if not ticker:
                stats.rows_skipped_no_ticker += 1
                continue

            period_raw = (row.get("period") or "").strip()
            period = normalize_period(period_raw)
            if period is None:
                stats.rows_skipped_bad_period += 1
                log.warning(
                    "%s: skipping row ticker=%s — bad period %r",
                    path.name, ticker, period_raw,
                )
                continue

            # Parse numerics
            nums: dict[str, float | None] = {}
            for field in _NUMERIC_FIELDS:
                nums[field] = _coerce_number(row.get(field, ""))

            # Sanity sniff — flag suspicious revenue values (e.g. obviously in
            # thousands when caller said "absolute PKR")
            warning_flags: list[str] = []
            if nums["revenue"] is not None and nums["revenue"] < 1_000_000:
                warning_flags.append(
                    f"revenue={nums['revenue']:.0f} looks too small for PKR "
                    "absolute — caller may have forgotten units scaling"
                )
            if nums["revenue"] is not None and nums["net_income"] is not None:
                if nums["net_income"] > nums["revenue"]:
                    warning_flags.append(
                        f"net_income {nums['net_income']:.0f} > revenue "
                        f"{nums['revenue']:.0f} — sanity-check this row"
                    )
            if warning_flags:
                stats.rows_with_warnings += 1
                for w in warning_flags:
                    log.warning(
                        "%s [%s %s]: %s", path.name, ticker, period, w,
                    )

            try:
                fr = FundamentalRow(
                    ticker=ticker,
                    period=period,
                    period_end_date=_coerce_date(row.get("period_end_date", "")),
                    revenue=nums["revenue"],
                    net_income=nums["net_income"],
                    eps=nums["eps"],
                    book_value=nums["book_value"],
                    debt=nums["debt"],
                    cash=nums["cash"],
                    fcf=nums["fcf"],
                    dividend_per_share=nums["dividend_per_share"],
                    source="csv_import",
                    source_url=(row.get("source_url") or "").strip() or None,
                    notes=None,
                )
            except Exception as e:  # noqa: BLE001
                stats.rows_skipped_other += 1
                log.warning(
                    "%s: skipping row ticker=%s period=%s — build failed: %s",
                    path.name, ticker, period, e,
                )
                continue

            rows_out.append(fr)
            stats.rows_imported += 1

    return rows_out


# --- Entrypoint --------------------------------------------------------------


def _files_to_process(args) -> list[Path]:
    if args.file:
        return [Path(f) for f in args.file]
    if not IMPORTS_DIR.exists():
        return []
    return sorted(p for p in IMPORTS_DIR.glob("*.csv") if p.is_file())


def main(argv: list[str] | None = None) -> int:
    log_ = config.setup_logging()  # configures root + returns ours
    parser = argparse.ArgumentParser(
        prog="python -m rupeya.fundamentals.csv_importer",
        description="Import fundamentals CSVs into Supabase.",
    )
    parser.add_argument(
        "--file", action="append",
        help="Specific CSV file(s) to import. If omitted, processes all CSVs in scrapers/imports/.",
    )
    parser.add_argument(
        "--archive", action="store_true",
        help="After successful import, move CSV to imports/imported/.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse + validate but do not write to the DB.",
    )
    args = parser.parse_args(argv)

    files = _files_to_process(args)
    if not files:
        log_.info(
            "No CSV files found to import. Looked in %s",
            args.file or str(IMPORTS_DIR),
        )
        return 0

    log_.info("=== CSV import: %d file(s) ===", len(files))
    for f in files:
        log_.info("  • %s", f.name)

    stats = ImportStats()
    all_rows: list[FundamentalRow] = []
    per_file_rows: dict[Path, list[FundamentalRow]] = {}

    for path in files:
        log_.info("Parsing %s", path.name)
        rows = parse_csv(path, stats)
        stats.files_processed += 1
        per_file_rows[path] = rows
        all_rows.extend(rows)
        log_.info("  → %d valid rows", len(rows))

    # Per-ticker counts (for the summary)
    per_ticker: dict[str, int] = defaultdict(int)
    for r in all_rows:
        per_ticker[r.ticker] += 1

    if args.dry_run:
        log_.info("=== DRY RUN — no DB writes ===")
        _print_summary(stats, per_ticker)
        return 0

    if not all_rows:
        log_.warning("No valid rows to import. Exiting.")
        _print_summary(stats, per_ticker)
        return 0

    with RunLogger(source="fundamentals_csv_import") as run:
        try:
            written = upsert_fundamentals(all_rows)
            run.rows_written = written
        except Exception as e:  # noqa: BLE001
            run.add_error(f"upsert failed: {e}")
            log_.exception("Upsert failed")
            return 2

        for err in stats.errors:
            run.add_error(err)

    log_.info("=== IMPORT COMPLETE ===")
    log_.info("Wrote %d row(s) to fundamentals_quarterly", written)
    _print_summary(stats, per_ticker)

    if args.archive:
        ARCHIVE_DIR.mkdir(exist_ok=True)
        for path in files:
            if per_file_rows[path]:
                target = ARCHIVE_DIR / path.name
                try:
                    path.rename(target)
                    log_.info("Archived %s → %s", path.name, target)
                except OSError as e:
                    log_.warning("Could not archive %s: %s", path.name, e)

    return 0


def _print_summary(stats: ImportStats, per_ticker: dict[str, int]) -> None:
    log.info("---- Import summary ----")
    log.info("Files processed:       %d", stats.files_processed)
    log.info("Rows seen:             %d", stats.rows_seen)
    log.info("Rows imported:         %d", stats.rows_imported)
    log.info("Skipped (no ticker):   %d", stats.rows_skipped_no_ticker)
    log.info("Skipped (bad period):  %d", stats.rows_skipped_bad_period)
    log.info("Skipped (other):       %d", stats.rows_skipped_other)
    log.info("Rows with warnings:    %d", stats.rows_with_warnings)
    log.info("File-level errors:     %d", len(stats.errors))
    log.info("Per-ticker counts:     %s",
             ", ".join(f"{k}={v}" for k, v in sorted(per_ticker.items())))


if __name__ == "__main__":
    sys.exit(main())
