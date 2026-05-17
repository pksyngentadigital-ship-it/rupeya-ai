"""
Rupeya.ai — Supabase loader + scrape_runs logger.

Writes scraped PriceRecords to public.prices_daily and records a summary
row in public.scrape_runs so we know what happened on every run.

Idempotent: prices_daily PK is (ticker, date) so re-runs upsert cleanly.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone

from . import db
from .psx_scraper import PriceRecord

log = logging.getLogger("rupeya.loader")


def upsert_prices(records: list[PriceRecord]) -> int:
    """
    Upsert price records into prices_daily.
    Returns the number of rows written.
    """
    if not records:
        log.warning("No records to upsert")
        return 0

    client = db.get_client()

    # Convert dataclasses to JSON-friendly dicts (Date → ISO string).
    rows = []
    for r in records:
        row = asdict(r)
        row["date"] = r.date.isoformat()
        rows.append(row)

    # Supabase recommends keeping batch size ≤ 1000 rows. Our universe is <200.
    resp = (
        client.table("prices_daily")
        .upsert(rows, on_conflict="ticker,date")
        .execute()
    )

    written = len(resp.data or [])
    log.info("Upserted %d price rows to prices_daily", written)
    return written


# ---------- scrape_runs logging ----------


class RunLogger:
    """
    Context-style helper for logging a scrape run.

    Usage:
        with RunLogger(source="psx_market_watch") as run:
            ...do work...
            run.rows_written = N
            run.add_error("optional error")
    """

    def __init__(self, source: str):
        self.source = source
        self.started_at = datetime.now(timezone.utc)
        self.rows_written: int = 0
        self.errors: list[str] = []
        self._client = db.get_client()
        self._run_id: str | None = None

    def __enter__(self) -> "RunLogger":
        # Insert the "started" row so we have a record even if the process crashes.
        resp = (
            self._client.table("scrape_runs")
            .insert(
                {
                    "source": self.source,
                    "started_at": self.started_at.isoformat(),
                    "rows_written": 0,
                    "errors": None,
                }
            )
            .execute()
        )
        if resp.data:
            self._run_id = resp.data[0]["id"]
            log.info("Started scrape_run id=%s source=%s", self._run_id, self.source)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        finished_at = datetime.now(timezone.utc)
        duration = (finished_at - self.started_at).total_seconds()

        if exc_val:
            self.errors.append(f"{exc_type.__name__}: {exc_val}")

        update: dict = {
            "finished_at": finished_at.isoformat(),
            "rows_written": self.rows_written,
            "errors": json.loads(json.dumps(self.errors)) if self.errors else None,
        }

        if self._run_id:
            try:
                self._client.table("scrape_runs").update(update).eq(
                    "id", self._run_id
                ).execute()
            except Exception as e:  # noqa: BLE001 — logging only
                log.error("Failed to finalize scrape_run row: %s", e)

        log.info(
            "Finished scrape_run id=%s rows=%d errors=%d duration=%.1fs",
            self._run_id,
            self.rows_written,
            len(self.errors),
            duration,
        )

    def add_error(self, message: str) -> None:
        log.warning("scrape_run error: %s", message)
        self.errors.append(message)


# ---------- Universe loading ----------


def get_covered_tickers() -> list[str]:
    """Pull the list of currently-covered ticker symbols from Supabase."""
    client = db.get_client()
    resp = (
        client.table("stocks")
        .select("ticker")
        .eq("is_covered", True)
        .execute()
    )
    tickers = [row["ticker"] for row in (resp.data or [])]
    log.info("Loaded %d covered tickers from DB", len(tickers))
    return tickers
