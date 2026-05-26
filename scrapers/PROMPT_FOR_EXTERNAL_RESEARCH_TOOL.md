# Prompt for external research tool (Gemini / Perplexity / ChatGPT with web search)

## Purpose
Use this prompt in any AI tool that has web search / browsing capability to
gather 10 years of historical fundamentals for Pakistan Stock Exchange (PSX)
stocks. Output is CSV that gets imported directly into Rupeya.ai's
`fundamentals_quarterly` table.

## How to use

1. Pick a batch of **5–10 tickers** from your covered universe (do not try
   more than 10 per query — quality drops sharply).
2. Open Gemini / Perplexity / ChatGPT with browsing.
3. Paste **everything between the `=== PROMPT START ===` and
   `=== PROMPT END ===` markers** below, then add your ticker list at the
   bottom.
4. Copy the CSV output. Save it as `fundamentals_batch_NN.csv` in
   `C:\Users\Abdullah\Documents\Claude\Projects\Rupeya.ai\scrapers\imports\`.
5. Paste 2–3 sample rows back to me in chat; I'll spot-check them against
   the actual filings before we import.

## CRITICAL: verify the data

Before sending a batch to me, open the `source_url` for **at least one
row per stock** and confirm the numbers match. Research-tool LLMs
hallucinate financial figures even when they cite a real URL. If any
spot-check fails, throw out that batch and try a different tool.

---

=== PROMPT START ===

You are a Pakistan equity research data analyst. Your job is to build a
CSV of historical fundamentals for PSX-listed companies, using ONLY
verifiable public sources.

## OUTPUT FORMAT

Return ONLY a CSV with this exact header (no markdown fences, no
commentary before or after):

```
ticker,period,period_end_date,currency,revenue,net_income,eps,book_value,debt,cash,fcf,dividend_per_share,source_url
```

One row per (ticker, period). Process all tickers I list at the end.

## PERIOD NAMING (Pakistani fiscal-year cumulative convention)

- `YYYY-Q1` = first 3 months of fiscal year (cumulative)
- `YYYY-H1` = first 6 months (cumulative half-year)
- `YYYY-9M` = first 9 months (cumulative)
- `YYYY-FY` = full fiscal year (12 months annual)

where `YYYY` is the calendar year in which the fiscal period ENDS.

Pakistani fiscal-year conventions:
- Non-bank companies (oil & gas, fertilizer, cement, food, IT, textiles):
  fiscal year is **July-June**. A 9-month report ending March 2026 is
  labelled `2026-9M`.
- Banks (HBL, MCB, UBL, ABL, NBP, BAFL, BAHL, MEBL, FABL, AKBL, SCBPL,
  SNBL, BIPL, BOK, JSBL) and DFI/insurance/some leasing companies:
  fiscal year is **calendar (January–December)**. A 9-month report ending
  September 2025 is labelled `2025-9M`.
- When unsure, check the company's annual report — the audited statements
  state the fiscal year cycle explicitly.

## TARGET HISTORY DEPTH

For each ticker, include **every fiscal-year-end (`-FY`) row from 2016
through the most recent year available**, plus the most recent
quarterly/half-yearly/9M row. That's roughly 10–11 annual rows + 1
recent interim row per stock.

If a stock has fewer than 5 years of data online, return whatever exists.
Never invent older data.

## DATA RULES (read carefully)

All monetary values must be in **ABSOLUTE PKR** (not thousands, not
millions). If a source says "Rs in millions: 1,234.56" you must
return `1234560000` for that value.

| Column | Definition |
|---|---|
| `ticker` | The PSX ticker symbol (uppercase, no suffix) |
| `period` | Canonical period code as defined above |
| `period_end_date` | ISO date YYYY-MM-DD — the LAST day of the period |
| `currency` | Always `PKR` |
| `revenue` | Total revenue / sales / turnover for the period (absolute PKR) |
| `net_income` | Profit after taxation attributable to ordinary shareholders (absolute PKR) |
| `eps` | Basic earnings per share (PKR per share — do NOT scale) |
| `book_value` | **TOTAL equity** attributable to ordinary shareholders at period end (absolute PKR). NOT book value per share. |
| `debt` | Total interest-bearing debt at period end (short-term borrowings + long-term loans + lease liabilities), absolute PKR. Excludes trade and tax payables. |
| `cash` | Cash and cash equivalents at period end (absolute PKR) |
| `fcf` | Free cash flow = Cash from Operations minus Capital Expenditure for the period (absolute PKR). Compute only if BOTH disclosed in the cash flow statement; otherwise leave blank. |
| `dividend_per_share` | Total interim + final per share declared for the period in PKR per share (do NOT scale). Leave blank if none. |
| `source_url` | A REAL, VERIFIABLE URL where you found this row's data. REQUIRED for every row. |

## ANTI-HALLUCINATION RULES (these are not optional)

1. **NEVER invent or estimate a number.** If you can't verify a value to
   a real, accessible source, leave that cell blank.
2. **`source_url` must be a real URL** you actually retrieved. Do NOT
   guess URLs that might exist. If the source you used isn't a URL
   (e.g., an offline PDF), leave the row out entirely.
3. **One row's data must come from ONE source.** Don't mix revenue from
   one filing with debt from another — that's how errors compound.
4. **If a number doesn't pass the smell test** (e.g., revenue < net_income,
   or book_value < net_income), double-check before including it. If
   still wrong, leave it blank with a note in a separate audit message.
5. **Refuse to fabricate data for periods/stocks that aren't publicly
   reported.** Better an empty cell than a confident lie.

## SOURCE PRIORITY

Use in this order. If higher-priority source has the data, use it.

1. **Company investor-relations page** (most authoritative — direct from
   the issuer). Search for `"{TICKER} annual report PDF site:{company}.com.pk"`.
2. **PSX Data Portal**: https://dps.psx.com.pk/company/{TICKER}
3. **Business Recorder**: https://www.brecorder.com
4. **Investing.com Pakistan**: https://www.investing.com/equities/pakistan
5. **Mettis**: https://mg.mettisglobal.com
6. **SECP filings**: https://eservices.secp.gov.pk

Do not use:
- Random blog posts, broker reports, or social media
- Any source you cannot link with a public URL
- Forum threads, even if they look authoritative

## EXAMPLE ROW (OGDC Q3 FY2026, real numbers, real source)

```
ticker,period,period_end_date,currency,revenue,net_income,eps,book_value,debt,cash,fcf,dividend_per_share,source_url
OGDC,2026-9M,2026-03-31,PKR,300126903000,115263205000,26.80,1407294379000,14827247000,57388339000,-11168340000,11.50,https://dps.psx.com.pk/download/document/275829.pdf
```

Note how absolute PKR values are large numbers (revenue of Rs 300 billion
= `300126903000`). Per-share values (`eps`, `dividend_per_share`) stay as
quoted (no scaling).

## YOUR JOB

For each ticker in the list below, produce one row per applicable period
(every `-FY` from 2016 onwards + the most recent quarterly/H1/9M).

Output ONLY the CSV. No introductory text, no closing summary, no
markdown code fence. The first line must be the CSV header.

If you genuinely cannot find any data for a ticker (zero verifiable
rows), DON'T include it in the CSV — at the very end, after the CSV,
add a single line: `# UNRECOVERABLE: TICKER1, TICKER2, ...`

## TICKERS

Process these tickers (replace this list before sending the prompt):

```
OGDC
ENGRO
LUCK
HBL
MCB
FFC
PSO
HUBC
MARI
MEBL
```

=== PROMPT END ===
