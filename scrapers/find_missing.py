"""
Diagnostic — for each ticker in our covered universe that wasn't found
on PSX Market Watch, search PSX symbols for likely matches (prefix +
substring) so we can extend PSX_TO_CANONICAL.

Usage:
    cd scrapers
    .venv\\Scripts\\activate
    python find_missing.py
"""

from __future__ import annotations

from rupeya import config, loader, psx_scraper

log = config.setup_logging()


def main() -> None:
    log.info("Loading covered universe + PSX Market Watch...")
    covered = set(loader.get_covered_tickers())
    all_records = psx_scraper.fetch_market_watch()
    psx_symbols = sorted({r.ticker for r in all_records})
    found = {r.ticker for r in all_records if r.ticker in covered}

    missing = sorted(covered - found)

    print()
    print("=" * 60)
    print(f"COVERED tickers NOT found on PSX: {len(missing)}")
    print("=" * 60)

    for m in missing:
        # Find PSX symbols that share a prefix or contain our ticker as substring
        prefix_matches = [s for s in psx_symbols if s.startswith(m[:3])]
        substr_matches = [s for s in psx_symbols if m in s or s in m]
        # Dedupe and show the most likely
        suggestions = sorted(set(prefix_matches[:5] + substr_matches[:5]))
        sug = ", ".join(suggestions[:8]) if suggestions else "(none)"
        print(f"  {m:<10}  → candidates on PSX: {sug}")

    print()
    print(f"Total PSX symbols available: {len(psx_symbols)}")
    print(f"Already mapped via PSX_TO_CANONICAL: {len(psx_scraper.PSX_TO_CANONICAL)}")


if __name__ == "__main__":
    main()
