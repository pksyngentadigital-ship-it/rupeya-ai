"""Reduce every PDF in filings_archive/ to a small text file of just its
financial-statement pages.

Why this exists: chat-session PDF extraction is constrained by how much
context each Read call consumes. A 30-page annual report mostly contains
the chairman's review, board profiles, and auditor's letter — and a tiny
section of audited financial statements + a 5-year highlights table.
We want to read ONLY the relevant sections.

What it does, per PDF:
  1. Open with pypdf, extract text per page.
  2. Score each page by financial-statement keyword density.
  3. Keep the top-scoring N pages (default 8).
  4. Write them as one .txt file at filings_archive/{TICKER}/__excerpt__{stem}.txt

Idempotent — re-runs skip existing excerpts unless --force is set.

Usage:
    python preprocess_pdfs.py                    # all tickers, all PDFs
    python preprocess_pdfs.py --tickers OGDC FFC # subset
    python preprocess_pdfs.py --force            # re-process even existing excerpts
    python preprocess_pdfs.py --pages 12         # keep top-12 pages per PDF (default 8)
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path

from rupeya import config

log = config.setup_logging()

ARCHIVE_DIR = Path(__file__).resolve().parent / "filings_archive"

# Keyword → weight for scoring page financial-statement-likeness.
# Higher weight = stronger signal that this page contains the data we want.
KEYWORDS = {
    # ── Highly specific to financial-statement tables ──
    "profit after taxation": 6,
    "profit after tax": 5,
    "earnings per share": 5,
    "five year": 5,
    "six year": 5,
    "ten year": 5,
    "financial highlight": 5,
    "financial highlights": 5,
    "at a glance": 4,
    "key ratios": 4,
    # ── Balance sheet / income statement headers ──
    "balance sheet": 4,
    "statement of financial position": 5,  # banks use this exact phrase
    "statement of profit": 4,
    "income statement": 4,
    "cash flow statement": 4,
    "statement of cash flow": 4,
    "comprehensive income": 3,
    # ── Specific line items (general) ──
    "net sales": 3,
    "turnover": 2,
    "gross profit": 2,
    "operating profit": 2,
    "total equity": 4,
    "shareholders' equity": 4,
    "shareholders equity": 4,
    "long term financing": 3,
    "long-term financing": 3,
    "short term borrowings": 3,
    "short-term borrowings": 3,
    "cash and cash equivalents": 4,
    "dividend per share": 4,
    "book value": 3,
    # ── Bank-specific line items (added for B3a Phase 4) ──
    "balances with treasury banks": 5,
    "balances with other banks": 4,
    "lendings to financial institutions": 4,
    "due from financial institutions": 4,
    "borrowings from financial institutions": 4,
    "deposits and other accounts": 5,
    "subordinated debt": 4,
    "interest bearing liabilities": 5,
    "non-performing loans": 3,
    "advances - net": 4,
    "investments - net": 4,
    "fee and commission": 3,
    "non mark-up income": 3,
    "non markup income": 3,
    "mark-up / return / interest earned": 5,
    "mark-up / return / interest expensed": 5,
    "net mark-up": 4,
    "net markup": 4,
    "credit loss allowance": 3,
    # ── Common report markers ──
    "interest earned": 2,
    "markup earned": 2,
    "mark-up": 2,
    "revenue": 2,
    "dividend": 1,
    # ── Multi-year summary tables (annual reports) ──
    "year ended": 2,
    "ratios": 2,
    "summary": 1,
    # ── Insurance-specific line items (added for B3a Phase 5) ──
    "net premium written": 5,
    "net premium earned": 5,
    "gross premium written": 4,
    "gross premium": 4,
    "premium income": 4,
    "net premium": 4,
    "underwriting result": 5,
    "underwriting expenses": 4,
    "underwriting income": 4,
    "policyholders": 4,
    "policy holders": 4,
    "claims expenses": 4,
    "net claims": 4,
    "reinsurance": 3,
    "investment income": 4,
    "takaful": 3,
    "operator's fund": 3,
    "participants' takaful fund": 3,
    # ── Shipping/transport-specific (added for B3a Phase 5) ──
    "freight revenue": 5,
    "freight earnings": 5,
    "charter hire": 4,
    "voyage profit": 4,
    "fleet": 2,
    "vessel": 2,
    "slot charter": 3,
    "demurrage": 3,
    "bunker": 2,
}

NUMBER_RE = re.compile(r"\d")
SEPARATOR = "=" * 70


def score_page(text: str) -> int:
    """Return an integer financial-statement relevance score for a page."""
    if not text:
        return 0
    low = text.lower()

    # Keyword-driven score
    score = 0
    for kw, w in KEYWORDS.items():
        c = low.count(kw)
        if c:
            score += w * c

    # Numeric density — financial tables have LOTS of digits.
    # Scale: 100 digits ≈ 1 point. A typical income statement page has
    # 200-600 digits.
    digits = sum(1 for ch in text if ch.isdigit())
    score += digits // 100

    return score


def process_pdf(pdf_path: Path, top_n: int) -> Path | None:
    """Extract top-N relevant pages from one PDF as a .txt excerpt.

    Returns the path of the written excerpt, or None on failure.
    """
    try:
        from pypdf import PdfReader  # local import keeps startup cost out of help text
        from pypdf.errors import PdfReadError
    except ImportError:
        log.error("pypdf not installed. Run: pip install -r requirements.txt")
        return None

    excerpt_path = pdf_path.parent / f"__excerpt__{pdf_path.stem}.txt"

    try:
        reader = PdfReader(str(pdf_path))
    except (PdfReadError, OSError, ValueError) as e:
        log.warning("  cannot open %s: %s", pdf_path.name, e)
        return None

    # Decrypt empty-password PDFs if needed
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:  # noqa: BLE001
            log.warning("  %s is encrypted — skipping", pdf_path.name)
            return None

    pages_with_scores: list[tuple[int, str, int]] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # noqa: BLE001
            log.debug("  %s page %d extraction error: %s", pdf_path.name, i, e)
            text = ""
        pages_with_scores.append((i, text, score_page(text)))

    # Sort by score (desc), take top N, then sort back by page order so the
    # output reads like a coherent excerpt.
    by_score = sorted(pages_with_scores, key=lambda x: -x[2])
    top = by_score[:top_n]
    top.sort(key=lambda x: x[0])

    # Write excerpt
    out_lines: list[str] = [
        f"# Excerpt from {pdf_path.name}",
        f"# Source dir: {pdf_path.parent.name}",
        f"# Total pages: {len(reader.pages)}",
        f"# Pages kept (top {top_n} by financial-statement score): "
        f"{[i for i, _, _ in top]}",
        "",
    ]
    for page_no, text, score in top:
        out_lines.append(SEPARATOR)
        out_lines.append(f"PAGE {page_no + 1}  (score={score})")
        out_lines.append(SEPARATOR)
        out_lines.append(text.strip())
        out_lines.append("")

    excerpt_path.write_text("\n".join(out_lines), encoding="utf-8")
    return excerpt_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python preprocess_pdfs.py",
        description="Reduce filings_archive PDFs to small relevant-pages text excerpts.",
    )
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Restrict to specific ticker folders. Defaults to all.",
    )
    parser.add_argument(
        "--pages", type=int, default=8,
        help="Number of top-scoring pages to keep per PDF (default 8).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-process PDFs even if an excerpt already exists.",
    )
    args = parser.parse_args(argv)

    if not ARCHIVE_DIR.exists():
        log.error("Archive dir not found: %s. Run build_filings_inventory.py first.", ARCHIVE_DIR)
        return 1

    # Collect tickers
    all_tickers = sorted(d.name for d in ARCHIVE_DIR.iterdir() if d.is_dir())
    if args.tickers:
        targets = [t for t in (t.upper() for t in args.tickers) if t in all_tickers]
        missing = set(args.tickers) - set(all_tickers)
        if missing:
            log.warning("Ticker folder(s) not found: %s", ", ".join(missing))
    else:
        targets = all_tickers

    if not targets:
        log.error("No ticker folders to process.")
        return 1

    log.info("=== PDF preprocessor: %d ticker folder(s), top %d pages each ===",
             len(targets), args.pages)

    start = time.time()
    total_pdfs = 0
    total_skipped = 0
    total_written = 0
    total_failed = 0
    bytes_in = 0
    bytes_out = 0

    for i, ticker in enumerate(targets, 1):
        tdir = ARCHIVE_DIR / ticker
        pdfs = sorted(p for p in tdir.glob("*.pdf"))
        if not pdfs:
            log.info("[%d/%d] %s — no PDFs", i, len(targets), ticker)
            continue

        log.info("[%d/%d] %s — %d PDF(s)", i, len(targets), ticker, len(pdfs))

        for pdf in pdfs:
            total_pdfs += 1
            excerpt = tdir / f"__excerpt__{pdf.stem}.txt"
            if excerpt.exists() and not args.force:
                total_skipped += 1
                log.debug("  [skip] %s", pdf.name)
                continue

            bytes_in += pdf.stat().st_size
            written = process_pdf(pdf, args.pages)
            if written is None:
                total_failed += 1
                continue
            total_written += 1
            bytes_out += written.stat().st_size
            log.info("  %s → %s (%d KB)", pdf.name, written.name, written.stat().st_size // 1024)

    duration = time.time() - start
    log.info("=== PREPROCESS SUMMARY ===")
    log.info("Total PDFs seen:       %d", total_pdfs)
    log.info("Excerpts written:      %d", total_written)
    log.info("Skipped (existed):     %d", total_skipped)
    log.info("Failed:                %d", total_failed)
    if bytes_in:
        log.info(
            "Compression:           %.1f MB in → %.1f MB out (%.0f%% smaller)",
            bytes_in / 1e6, bytes_out / 1e6,
            100 * (1 - bytes_out / bytes_in) if bytes_in else 0,
        )
    log.info("Duration:              %.1fs", duration)

    return 0


if __name__ == "__main__":
    sys.exit(main())
