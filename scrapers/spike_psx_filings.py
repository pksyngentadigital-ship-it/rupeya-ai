"""
Rupeya.ai — B3a discovery spike (throwaway script).

Goal: de-risk the B3a fundamentals architecture by proving the
PSX-DPS → financial-data extraction pipeline works end-to-end on ONE
stock (OGDC). We'd rather discover that PSX DPS is JS-rendered, or
that filings live somewhere different from what we assumed, NOW —
before building a whole rupeya/fundamentals/ subpackage around a
broken assumption.

What this script does:
  1. Verify ANTHROPIC_API_KEY works (tiny "say OK" call to Haiku)
  2. Fetch OGDC's company page on PSX Data Portal Service
  3. Save the raw HTML to scrapers/.cache/ so we can eyeball it
  4. Analyze: how many tables, how many PDF links, do any tables
     mention revenue / EPS / profit / etc?
  5. If a financial-looking table is found, print its first ~10 rows
  6. Report findings + tell us what to do next

Will be deleted once rupeya/fundamentals/ replaces it.

Usage:
    cd scrapers
    .venv\\Scripts\\activate
    pip install -r requirements.txt   # if not already
    python spike_psx_filings.py
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import sys
from pathlib import Path

import httpx
from selectolax.parser import HTMLParser

from rupeya import config
from rupeya.llm_models import FUNDAMENTALS_EXTRACTION_MODEL

# config.setup_logging() also loads .env (via config import side-effects)
log = config.setup_logging()

# --- Constants ---------------------------------------------------------------

TICKER = "OGDC"
DPS_BASE = "https://dps.psx.com.pk"
COMPANY_URL = f"{DPS_BASE}/company/{TICKER}"

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
HTML_DUMP = CACHE_DIR / f"spike_{TICKER}.html"

# Browser-realistic headers — same pattern as psx_scraper.py
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Rupeya.ai/0.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
}

# Model resolved via rupeya/llm_models.py — Haiku for bulk extraction work.
# That module is the single source of truth for which model handles which
# task across the whole project; never hard-code a model string elsewhere.
CLAUDE_MODEL = FUNDAMENTALS_EXTRACTION_MODEL


# --- Steps -------------------------------------------------------------------


def step_1_verify_anthropic() -> bool:
    """Confirm the API key loads and the SDK can make a real request."""
    log.info("=== Step 1: Verify Anthropic API key works ===")

    try:
        import anthropic  # noqa: F401  — imported for SDK availability check
    except ImportError:
        log.error(
            "anthropic SDK not installed. Run inside the venv:\n"
            "  pip install -r requirements.txt"
        )
        return False

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY missing. Add it to scrapers/.env.")
        return False
    if not api_key.startswith("sk-ant-"):
        log.warning(
            "ANTHROPIC_API_KEY doesn't start with 'sk-ant-'. "
            "Double-check you copied the right value."
        )

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=20,
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
        )
        text = resp.content[0].text.strip()
        log.info("Anthropic API responded: %r — key works.", text)
        return True
    except Exception as e:  # noqa: BLE001
        log.exception("Anthropic API call failed: %s", e)
        return False


def step_2_fetch_company_page() -> str | None:
    """Fetch OGDC's PSX DPS company page (best-known URL pattern)."""
    log.info("=== Step 2: Fetch %s ===", COMPANY_URL)
    try:
        with httpx.Client(
            headers=HEADERS, timeout=30, follow_redirects=True, http2=False
        ) as client:
            resp = client.get(COMPANY_URL)
            log.info(
                "HTTP %s — %d bytes — content-type=%s",
                resp.status_code,
                len(resp.content),
                resp.headers.get("content-type", "?"),
            )
            resp.raise_for_status()
        html = resp.text
        HTML_DUMP.write_text(html, encoding="utf-8")
        log.info("Saved raw HTML → %s", HTML_DUMP)
        return html
    except Exception as e:  # noqa: BLE001
        log.exception("Failed to fetch company page: %s", e)
        return None


def _collect_announcements(html: str) -> list[dict]:
    """Walk the announcements feed and return [{title, href, date}, ...].

    Each PDF link is wrapped in announcement context like
    "Apr 29, 2026 — FINANCIAL RESULTS FOR THE PERIOD ENDED MARCH 31 2026".
    """
    tree = HTMLParser(html)
    items: list[dict] = []
    for a in tree.css("a[href]"):
        href = (a.attributes.get("href") or "").strip()
        if ".pdf" not in href.lower():
            continue
        # Walk up to the nearest row-ish parent to capture context.
        parent = a.parent
        for _ in range(4):
            if parent is None or parent.tag in ("tr", "li", "div"):
                break
            parent = parent.parent
        ctx = parent.text(strip=True) if parent else ""
        # Best-effort date extraction (e.g. "Apr 29, 2026")
        date_match = re.search(
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}",
            ctx,
        )
        items.append({
            "href": href,
            "date_text": date_match.group(0) if date_match else "",
            "context": ctx,
        })
    return items


def _classify_announcement(ctx: str) -> str:
    """Bucket an announcement by its title/context. Drives PDF filtering."""
    c = ctx.lower()
    if "financial results for the period" in c or "financial statement for" in c:
        return "financials"
    if "transmission of" in c and "report" in c:
        return "transmission_letter"  # usually a 1-page cover; we skip these
    if "interim cash dividend" in c or "final cash dividend" in c:
        return "dividend"
    if "board meeting" in c or "annual general meeting" in c or "agm" in c:
        return "corporate_action"
    if "shariah" in c:
        return "shariah_disclosure"
    return "other"


def step_3_analyze_page(html: str) -> dict:
    """Inspect the HTML for tables, PDF links, and financial-statement hints."""
    log.info("=== Step 3: Analyze page structure ===")
    tree = HTMLParser(html)

    # How big is the HTML, and does it look JS-rendered?
    body = html.lower()
    looks_js_rendered = (
        len(html) < 50_000
        and ("enable javascript" in body or "loading" in body)
        and html.count("<table") < 2
    )
    if looks_js_rendered:
        log.warning(
            "Page looks JS-rendered (small HTML, mentions 'enable javascript' "
            "or 'loading', few tables). We may need Playwright instead of httpx."
        )

    tables = tree.css("table")
    log.info("Found %d <table> element(s)", len(tables))

    # PDF links
    pdf_links: list[str] = []
    for a in tree.css("a[href]"):
        href = (a.attributes.get("href") or "").strip()
        if ".pdf" in href.lower():
            pdf_links.append(href)
    log.info("Found %d PDF link(s) on the page", len(pdf_links))
    for href in pdf_links[:10]:
        log.info("  → %s", href)
    if len(pdf_links) > 10:
        log.info("  ... and %d more", len(pdf_links) - 10)

    # Keyword scan to gauge whether financial content is on this page at all
    keywords = [
        "revenue", "net income", "profit after tax", "earnings per share",
        "eps", "balance sheet", "cash flow", "dividend", "filings",
        "announcements", "financials",
    ]
    keyword_counts: dict[str, int] = {}
    for kw in keywords:
        c = body.count(kw)
        if c > 0:
            keyword_counts[kw] = c
    log.info("Financial-keyword counts in page text: %s", keyword_counts)

    # Tables that contain financial-statement-shaped text
    financial_table_indexes: list[int] = []
    for i, table in enumerate(tables):
        text = table.text(strip=True).lower()
        if any(
            k in text
            for k in (
                "revenue", "eps", "net income", "profit after tax",
                "earnings per share",
            )
        ):
            financial_table_indexes.append(i)
    log.info(
        "Tables containing financial keywords: %s", financial_table_indexes
    )

    # Classify each PDF link by announcement type so we know which ones to feed
    # to Claude (only "financials" — skip transmission letters, board notices).
    announcements = _collect_announcements(html)
    by_type: dict[str, int] = {}
    for ann in announcements:
        ann["type"] = _classify_announcement(ann["context"])
        by_type[ann["type"]] = by_type.get(ann["type"], 0) + 1
    log.info("Announcements by type: %s", by_type)
    financials_anns = [a for a in announcements if a["type"] == "financials"]
    log.info("Financial-statement filings found: %d", len(financials_anns))
    for a in financials_anns[:5]:
        log.info("  • %s — %s", a["date_text"] or "?", a["context"][:90])

    return {
        "tables": len(tables),
        "pdf_links": pdf_links,
        "financial_table_indexes": financial_table_indexes,
        "looks_js_rendered": looks_js_rendered,
        "announcements": announcements,
        "financials_anns": financials_anns,
    }


EXTRACTION_PROMPT = """\
You are extracting structured fundamentals from a Pakistan Stock Exchange (PSX) \
company filing. Return ONLY valid JSON — no commentary, no markdown fences.

Extract the values reported in this filing for the SINGLE most recent period \
the document covers. Match this exact schema:

{
  "ticker": "<string, e.g. OGDC>",
  "period": "<string, e.g. 2026-Q3 — use the issuer's reported fiscal quarter>",
  "period_end_date": "<ISO date YYYY-MM-DD of period end>",
  "currency": "<e.g. PKR>",
  "units": "<e.g. thousands, millions>",
  "revenue": <number or null>,
  "net_income": <number or null>,
  "eps": <number or null>,
  "book_value": <number or null — total equity attributable to shareholders>,
  "debt": <number or null — total interest-bearing debt (short+long term)>,
  "cash": <number or null — cash and cash equivalents>,
  "fcf": <number or null — CFO minus CapEx if both disclosed, else null>,
  "dividend_per_share": <number or null — interim+final per share for this period>,
  "notes": "<short string flagging anything missing or unusual>"
}

Rules:
- If a value isn't reported on the financial statements, return null. Do NOT guess.
- Numbers must be raw numerics (no commas, no currency symbols). Use the units field to indicate the scale.
- For period, use the issuer's fiscal calendar. OGDC's fiscal year is July–June, so a quarter ending Mar 31 2026 is "2026-Q3".
- "book_value" = total equity attributable to ordinary shareholders, NOT book value per share.
- Be conservative: when in doubt, return null and explain in notes.
"""


def step_5_extract_one_pdf(financials_anns: list[dict]) -> dict | None:
    """Download the most recent financial-statement PDF, send to Claude, print JSON."""
    log.info("=== Step 5: Download one PDF + Claude extraction ===")

    if not financials_anns:
        log.warning("No financial-statement announcements identified. Skipping.")
        return None

    ann = financials_anns[0]
    pdf_url = ann["href"]
    if pdf_url.startswith("/"):
        pdf_url = DPS_BASE + pdf_url
    log.info("Selected filing: %s — %s", ann.get("date_text"), ann["context"][:100])
    log.info("Downloading: %s", pdf_url)

    try:
        with httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True) as client:
            resp = client.get(pdf_url)
            resp.raise_for_status()
        pdf_bytes = resp.content
    except Exception as e:  # noqa: BLE001
        log.exception("PDF download failed: %s", e)
        return None

    if not pdf_bytes.startswith(b"%PDF"):
        log.error(
            "Downloaded file is not a PDF (first bytes: %r). PSX may have served "
            "an HTML interstitial. Length=%d bytes.",
            pdf_bytes[:16],
            len(pdf_bytes),
        )
        (CACHE_DIR / "spike_OGDC_bad.bin").write_bytes(pdf_bytes)
        return None

    pdf_cache = CACHE_DIR / f"spike_{TICKER}_filing.pdf"
    pdf_cache.write_bytes(pdf_bytes)
    log.info("Saved PDF → %s (%d KB)", pdf_cache, len(pdf_bytes) // 1024)

    # Quick sanity check via pypdf — confirms file is parseable and has pages
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_cache)
        page_count = len(reader.pages)
        log.info("PDF has %d page(s). Sending to Claude (%s)…", page_count, CLAUDE_MODEL)
    except Exception as e:  # noqa: BLE001
        log.warning("pypdf sanity check failed (continuing anyway): %s", e)
        page_count = -1

    # --- Claude extraction ---
    try:
        from anthropic import Anthropic
    except ImportError:
        log.error("anthropic SDK missing — can't run extraction.")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY missing — can't run extraction.")
        return None

    client = Anthropic(api_key=api_key)
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": EXTRACTION_PROMPT + f"\n\nThe ticker is {TICKER}."},
                ],
            }],
        )
    except Exception as e:  # noqa: BLE001
        log.exception("Claude extraction failed: %s", e)
        return None

    usage = resp.usage
    # Haiku 4.5 pricing (approx): $1/M input, $5/M output
    cost_usd = (usage.input_tokens / 1_000_000) * 1.0 + (usage.output_tokens / 1_000_000) * 5.0
    log.info(
        "Claude usage: input=%d tokens, output=%d tokens → ~$%.4f",
        usage.input_tokens, usage.output_tokens, cost_usd,
    )

    raw_text = resp.content[0].text.strip()
    # Strip ```json fences if Haiku added them despite the instruction
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.DOTALL)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        log.error("Claude output is not valid JSON: %s\nRaw output:\n%s", e, raw_text)
        return None

    log.info("Claude extracted (formatted JSON):")
    for line in json.dumps(parsed, indent=2).splitlines():
        log.info("  %s", line)

    return parsed


def step_4_print_sample_table(html: str, indexes: list[int]) -> None:
    """If a financial table was detected, print its first 10 rows."""
    if not indexes:
        log.info("=== Step 4: No financial tables found inline — skipping ===")
        return

    log.info("=== Step 4: Sample first financial-looking table ===")
    tree = HTMLParser(html)
    tables = tree.css("table")
    sample = tables[indexes[0]]
    for row in sample.css("tr")[:10]:
        cells = [c.text(strip=True)[:50] for c in row.css("th, td")]
        log.info("  | %s |", " | ".join(cells))


# --- Main --------------------------------------------------------------------


def main() -> int:
    log.info("=== Rupeya B3a spike — discovery for %s ===", TICKER)

    # Step 1 is now non-blocking: an Anthropic failure (no credits, etc.)
    # doesn't stop the more valuable PSX-discovery work below. We still
    # log the failure so it's visible.
    anthropic_ok = step_1_verify_anthropic()
    if not anthropic_ok:
        log.warning(
            "Anthropic check failed — continuing anyway. The PSX discovery "
            "below doesn't need it. We'll only need a working API key when "
            "(and if) the page analysis shows we need to extract PDFs."
        )

    html = step_2_fetch_company_page()
    if not html:
        log.error("Bailing — couldn't fetch PSX DPS page.")
        return 2

    findings = step_3_analyze_page(html)
    step_4_print_sample_table(html, findings["financial_table_indexes"])

    # Step 5: only run if the Anthropic check earlier succeeded, AND we
    # actually found at least one financial-statement filing to extract.
    if anthropic_ok and findings["financials_anns"]:
        step_5_extract_one_pdf(findings["financials_anns"])
    elif not anthropic_ok:
        log.info("=== Step 5: Skipped (Anthropic API not reachable) ===")
    else:
        log.info("=== Step 5: Skipped (no financial-statement filings identified) ===")

    # ---- Summary ----
    log.info("================ SPIKE SUMMARY ================")
    log.info("Tables on page          : %d", findings["tables"])
    log.info("PDF links               : %d", len(findings["pdf_links"]))
    log.info("Financial-looking tables: %d", len(findings["financial_table_indexes"]))
    log.info("Looks JS-rendered       : %s", findings["looks_js_rendered"])
    log.info("Raw HTML dump           : %s", HTML_DUMP)
    log.info("================================================")

    # Interpretation hint for the human
    if findings["looks_js_rendered"]:
        log.info(
            "→ Next step: DPS likely needs Playwright (JS-rendered SPA). "
            "We'll either switch to Playwright OR try the older PSX site "
            "(psx.com.pk/announcements), which historically serves static HTML."
        )
    elif findings["financial_table_indexes"]:
        log.info(
            "→ Next step: financial tables exist inline. We can parse them "
            "from HTML directly without PDFs or Claude — much cheaper and faster."
        )
    elif findings["pdf_links"]:
        log.info(
            "→ Next step: PDFs are available. Download one and run it through "
            "Claude for structured extraction."
        )
    else:
        log.info(
            "→ Next step: page doesn't expose financials at this URL. Open the "
            "HTML dump in a browser to see what's actually here, and consider "
            "the announcements feed (https://dps.psx.com.pk/announcements) "
            "or the older psx.com.pk site."
        )

    log.info("=== Spike complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
