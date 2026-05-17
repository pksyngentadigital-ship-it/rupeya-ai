"""
Diagnostic — print the PSX Market Watch table structure.

Run this when the scraper produces weird values. It dumps:
  • The table's column headers (so we know what each cell is)
  • The first 3 data rows with every cell's index + content
  • Total row count
  • A search for "ENGRO" so we can see if it's there under a different label

Usage:
    cd scrapers
    .venv\\Scripts\\activate
    python debug_psx.py
"""

from selectolax.parser import HTMLParser

from rupeya import config, psx_scraper

log = config.setup_logging()


def main() -> None:
    resp = psx_scraper._http_get(psx_scraper.PSX_MARKET_WATCH_URL)
    print(f"\nResponse: HTTP {resp.status_code}, {len(resp.content)} bytes")
    print(f"Content-Type: {resp.headers.get('content-type')}\n")

    tree = HTMLParser(resp.text)

    # ---- Table headers ----
    print("=" * 60)
    print("TABLE COLUMN HEADERS")
    print("=" * 60)
    for sel in ("table thead th", "table thead tr th", "thead th"):
        headers = tree.css(sel)
        if headers:
            print(f"(matched with selector: {sel!r})")
            for i, h in enumerate(headers):
                print(f"  [{i:>2}] {h.text(strip=True)!r}")
            break
    else:
        print("  (no <thead> found — table may not have headers)")

    # ---- First 3 data rows ----
    print()
    print("=" * 60)
    print("FIRST 3 DATA ROWS (all cells with index)")
    print("=" * 60)

    rows = tree.css("table tbody tr") or tree.css("table tr")[1:]  # skip header
    print(f"Total data rows found: {len(rows)}\n")

    for ri, row in enumerate(rows[:3]):
        cells = row.css("td")
        ticker = cells[0].text(strip=True) if cells else "?"
        print(f"--- Row {ri} (ticker={ticker!r}, {len(cells)} cells) ---")
        for ci, cell in enumerate(cells):
            text = cell.text(strip=True)
            print(f"  [{ci:>2}] {text!r}")
        print()

    # ---- ENGRO search ----
    print("=" * 60)
    print("SEARCHING FOR 'ENGRO' IN ALL ROWS")
    print("=" * 60)
    matches = []
    for row in rows:
        cells = row.css("td")
        if not cells:
            continue
        first_cell = cells[0].text(strip=True).upper()
        if "ENGRO" in first_cell or first_cell.startswith("ENG"):
            matches.append((first_cell, [c.text(strip=True) for c in cells]))

    if not matches:
        print("  ❌ No rows starting with 'ENG' found.")
        print("     Either PSX uses a different symbol, or our scraper missed it.")
    else:
        for ticker, vals in matches:
            print(f"  ✓ {ticker}: {vals}")


if __name__ == "__main__":
    main()
