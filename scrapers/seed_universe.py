"""
Rupeya.ai — Seed the public.stocks table with the initial covered universe.

Idempotent: upserts on `ticker`, safe to re-run.

Usage:
    cd scrapers
    .venv\\Scripts\\activate
    python seed_universe.py
"""

from __future__ import annotations

from rupeya import config, db
from rupeya.universe import UNIVERSE

log = config.setup_logging()


def main() -> None:
    log.info("Preparing to seed %d stocks into public.stocks", len(UNIVERSE))

    client = db.get_client()

    # Mark every seeded stock as covered so the price scraper picks it up.
    rows = [{**s, "is_covered": True} for s in UNIVERSE]

    # Batch upsert. Supabase allows up to ~1000 rows per request; 100 is fine.
    resp = client.table("stocks").upsert(rows, on_conflict="ticker").execute()

    written = len(resp.data or [])
    log.info("Upserted %d rows", written)

    # Verification — count covered + Shariah totals
    covered = (
        client.table("stocks")
        .select("ticker", count="exact")
        .eq("is_covered", True)
        .execute()
    )
    shariah = (
        client.table("stocks")
        .select("ticker", count="exact")
        .eq("is_covered", True)
        .eq("is_shariah_compliant", True)
        .execute()
    )

    log.info("Verification — covered stocks in DB: %d", covered.count or 0)
    log.info("Verification — Shariah-compliant covered stocks: %d", shariah.count or 0)
    log.info("Done.")


if __name__ == "__main__":
    main()
