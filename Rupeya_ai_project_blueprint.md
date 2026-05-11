# Rupeya.ai — Project Blueprint
**Pakistan's First AI-Powered Long-Term Stock Analysis Platform for PSX**

Version: 1.0 (MVP Architecture)
Document owner: Founder (non-coder, AI-assisted build)
Last updated: 10 May 2026
Status: Pre-development blueprint, ready to hand to AI coding agents (Cursor / Claude Code / Lovable / v0) or to a Pakistani dev hire.

---

## 0. Founding Decisions (Locked from Discovery)

| Decision area | Choice for MVP | Rationale |
|---|---|---|
| Build approach | AI-assisted coding (Cursor + Claude + Lovable/v0 + Supabase Studio) | Founder is non-coder. AI agents write Next.js + Python; founder owns product, prompts, and review. ~$0–30/month tooling. |
| Front-end | Next.js 14 (App Router) deployed as a PWA on Vercel | Industry-standard, AI-coder-friendly, generous free tier, installable on Android home screens. |
| Backend / DB / Auth | Supabase (Postgres + Auth + Storage + Edge Functions + Row-Level Security) | One service replaces 4–5. Free tier comfortably covers 0–500 paying users. |
| AI/LLM | Hosted LLM APIs only (Claude Haiku for bulk, Claude Sonnet for high-stakes verdicts; Gemini 1.5 Flash free tier as fallback) | Zero infra. ~$0.05–0.30 per active user/month at MVP volumes. No GPU. |
| Quant engine | Pure Python (FastAPI on Render free tier OR Supabase Edge Functions) for ratios/DCF/scoring | Deterministic financial math NEVER goes through an LLM. LLM only narrates verdicts. |
| Data sourcing | Scraping-only MVP (PSX, Business Recorder, Dawn Business, Profit, Mettis public pages, company IR pages, SECP filings, **Investing.com** for historical prices/dividends) | Cheapest path to MVP. Investing.com is the primary source for clean historical price and dividend tables (better structured than PSX's own pages); however it has aggressive bot protection and requires a browser-emulating scraper. Plan to license Mettis/PSX DataPortal once paid users justify cost (~Phase 2). |
| Platform priority | Web app first (Next.js PWA, mobile-responsive). Native apps in Phase 3. | 90% feature parity at 10% cost. |
| Payments (MVP) | Bank transfer / IBFT with manual admin verification | Zero gateway fees, zero integration. Acceptable up to ~500 paying users. |
| Payments (Phase 1.5) | **Safepay** (cards + JazzCash + EasyPaisa in one integration) | Pakistani gateway, ~3% MDR, easiest single integration for PK retail. |
| Compliance posture | Educational research tool, NOT investment advice | Avoids SECP advisor licensing. Mandatory disclaimers, no explicit "Buy XYZ" wording on recommendations. Verdicts are framed as research signals. |
| Hosting cost target (MVP) | < PKR 5,000/month all-in | Vercel free + Supabase free + Render free + Cloudflare free + LLM API pay-as-you-go. |

---

## 1. Product Vision

**Vision statement.** Make smart, long-term, fundamentals-driven PSX investing accessible to every Pakistani — even those who have never read a balance sheet — through a disciplined AI analyst that thinks like a long-horizon owner-investor, not a trader.

**Mission.** Replace WhatsApp tip-sharing and "uncle ka share" culture with a structured, educational, evidence-driven research workflow priced for the Pakistani retail wallet (PKR 500/month).

**Audience.**
1. Beginners with PKR 5,000–50,000 to invest who don't know where to start.
2. SIP investors building long-term wealth through monthly contributions.
3. Dividend-focused retirees and salaried investors hunting yield.
4. Existing retail investors who want a second opinion on their KSE-100 holdings.

**Anti-audience.** Day-traders, technical-only chartists, futures speculators, anyone seeking quick tips. Rupeya.ai will explicitly turn these users away in onboarding.

**Tone.** Calm, educational, plain-Urdu-and-English, never hyped. The product should feel like a trusted older sibling who studied finance abroad — not a bro on Twitter.

**North-star metric.** *Active long-term portfolios under management* — defined as users with ≥3 holdings held for ≥90 days who logged in in the last 30 days.

---

## 2. System Architecture (High-Level)

```
┌─────────────────────────────────────────────────────────────────┐
│                           USERS                                  │
│       (Web PWA — Next.js on Vercel — installable on mobile)      │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
┌──────────────────────────┐         ┌──────────────────────────┐
│  Next.js App Router      │         │   Marketing site (same   │
│  (RSC + Server Actions)  │         │   Next.js project)       │
└──────────┬───────────────┘         └──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SUPABASE                                 │
│  • Postgres (users, portfolios, stocks, fundamentals, alerts)   │
│  • Auth (email + magic link + Google)                            │
│  • Storage (PDF filings, charts, profile pics)                   │
│  • Row-Level Security (one user = own rows only)                 │
│  • Edge Functions (lightweight TS handlers)                      │
└─────────┬─────────────────────────────────────────┬─────────────┘
          │                                         │
          ▼                                         ▼
┌──────────────────────┐             ┌─────────────────────────────┐
│  Quant Engine        │             │  Data Pipeline (Python)     │
│  (Python FastAPI on  │             │  Scrapers + Cleaners +      │
│  Render free tier)   │             │  Loaders. Runs on cron via  │
│  • Ratios            │             │  GitHub Actions (free) or   │
│  • DCF / valuation   │             │  Render cron.               │
│  • Scoring engine    │             │                             │
│  • Portfolio builder │             │  Sources: PSX, BR, Dawn,    │
│  • Rebalancer        │             │  Profit, Sarmaya, Mettis,   │
└──────────┬───────────┘             │  IR pages, Investing.com.   │
           │                         └──────────┬──────────────────┘
           │                                    │
           ▼                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LLM LAYER                                 │
│  • Claude Haiku — bulk summaries, news synthesis                 │
│  • Claude Sonnet — Portfolio Doctor verdicts, IC-grade memos     │
│  • Gemini 1.5 Flash — fallback / free tier overflow              │
│  Orchestrated via thin LangChain/Vercel AI SDK wrappers.         │
│  STRICT RULE: numbers come from Quant Engine, narrative from LLM.│
└─────────────────────────────────────────────────────────────────┘
```

**Key architectural principles**
1. **Separation of math and narrative.** Every number a user sees (intrinsic value, ROE, score) is computed by deterministic Python — never asked of an LLM. LLMs only translate numbers into plain-English verdicts.
2. **Idempotent data pipeline.** Each scrape job writes to a versioned `raw_filings` table; transforms produce `clean_fundamentals` rows. Re-runs never corrupt history.
3. **Multi-tenant by RLS, not by schema.** All user data lives in shared Postgres tables protected by Supabase Row-Level Security. Cheap and scales to 100k+ users.
4. **Cache-first AI.** Stock summaries are cached per stock per day; only ~80 PSX stocks × 1 update/day = ~80 LLM calls/day, regardless of user count. Per-user reasoning is the only on-demand inference.
5. **Stateless services.** Quant + scraper services hold no state; all state in Postgres. Lets us scale horizontally or restart freely.

---

## 3. AI Architecture

### 3.1 Three-tier AI design

| Tier | Purpose | Model | Cadence | Cost driver |
|---|---|---|---|---|
| Tier A — Batch enrichment | Daily summary per covered stock; news digest; filing extraction | Claude Haiku + Gemini Flash (cheap models) | Once daily, cron | Stock count (~80 × 1) — fixed cost, doesn't grow with users |
| Tier B — On-demand reasoning | Portfolio Doctor verdicts, intrinsic-value narratives, "Why this stock?" explanations | Claude Sonnet | Triggered by user action | Active user count |
| Tier C — Conversational | Plain education ("what is ROE?"), generic FAQ | Claude Haiku with RAG over glossary | Per user message | Engagement |
| Tier D — **Ask Rupeya AI Agent** | Multi-step research: "Should I buy PSO?" → fetch filings, compute valuation, check Shariah, synthesize, recommend | Claude Sonnet with tool-calling | Per user query | Engagement |

### 3.2 The "Quant-First, LLM-Last" rule (CRITICAL)

LLMs **never** compute valuations, ratios, scores, or portfolio weights.
- Quant Engine produces a structured JSON block (numbers + flags + signals).
- LLM receives that JSON + a tight system prompt and produces only the human narrative.
- This eliminates hallucinated financials — the #1 fintech LLM risk.

Example: a Portfolio Doctor verdict on Engro Corp is built like:
```
quant_engine.score(ENGRO) → {
  business_quality: 4.1/5,
  financial_health: 3.6/5,
  valuation: 3.9/5 (intrinsic 320 vs market 295),
  catalysts: 3/5,
  composite: 3.7/5,
  flags: ["dividend_payout_ratio_high", "circular_debt_exposure_low"]
}
→ verdict_engine.classify(3.7, flags) → "BUY"
→ LLM(prompt + JSON + verdict) → 3-paragraph plain-English explanation
```

### 3.3 Retrieval-Augmented Generation (RAG)

A Postgres `pgvector` index over:
- Latest 3 years of annual reports (PDF → chunks → embeddings)
- Last 12 months of news per covered stock
- Our own educational glossary (debt-to-equity, ROE, DCF, etc.)

Every Tier-B and Tier-C call is grounded in retrieved chunks; sources are surfaced to the user as citations. This is also the foundation for the "Daily AI Stock Analyst" memos.

### 3.4 Ask Rupeya — The AI Research Agent (the "Tier D" capability)

Ask Rupeya is not a chatbot. It is an **autonomous research agent** that, given a user question, plans a multi-step research workflow, calls deterministic tools to gather data, applies the 4-pillar fundamental framework, and returns a verdict with full sourcing and reasoning trace.

**3.4.1 Architecture.** Built on Claude Sonnet with **tool calling** (function calling). The model never invents financial numbers — every number comes from a tool result. The agent is constrained by a strict system prompt that enforces the Rupeya investment philosophy and the educational-tool framing.

**3.4.2 Available tools (the agent can call any of these).**

| Tool | Purpose | Returns |
|---|---|---|
| `get_stock_profile(ticker)` | Pull current price, sector, market cap, KMI status | Structured JSON |
| `get_filings(ticker, years)` | Recent annual + quarterly filings | List of filings + extracted text |
| `get_fundamentals(ticker, period)` | Audited financials for a period | Revenue, EPS, ROE, D/E, FCF, etc. |
| `get_prices(ticker, range)` | Price history | OHLCV time series |
| `get_news(ticker, days, sources)` | Filtered news from BR, Dawn, Profit, Sarmaya | Article snippets + URLs |
| `score_stock(ticker)` | Run the 4-pillar RupeyaScore | Pillar scores + composite + flags |
| `dcf(ticker, discount_rate, terminal_growth)` | Compute intrinsic value | IV + sensitivity table |
| `check_shariah_compliance(ticker)` | KMI + AAOIFI ratio check | Boolean + ratios + reasoning |
| `flag_macro_risks(ticker)` | Sector-specific risks (circular debt, FX, regulatory) | List of flags + severity |
| `get_user_portfolio()` | Logged-in user's current holdings (with consent) | Portfolio JSON |
| `compare_stocks(tickers[])` | Side-by-side fundamental + valuation comparison | Comparison matrix |
| `find_alternatives(ticker, criteria)` | Find stocks with similar exposure but better RupeyaScore | Ranked list |

**3.4.3 Reasoning pattern.** For a question like *"Should I buy PSO right now?"* the agent:
1. **Plans** — decides which tools to call.
2. **Calls** `get_stock_profile`, `check_shariah_compliance`, `score_stock`, `dcf`, `flag_macro_risks`, `get_news` — typically 4–7 tool calls per query.
3. **Reasons** — synthesizes the tool outputs into a verdict using the Rupeya philosophy (Section 5).
4. **Responds** with: structured verdict block (verdict badge + score + MoS) → 3–5 paragraph narrative → cited sources → suggested follow-ups.
5. **Surfaces the trace** — the user sees a collapsed "Research trace" showing every tool call (proof of work, anti-hallucination signal).

**3.4.4 Personalization.** When the user is logged in, the agent automatically:
- Respects their `shariah_only` flag — never recommends a non-compliant stock if the flag is on.
- Knows their existing portfolio (read-only via `get_user_portfolio`).
- Knows their risk tolerance, horizon, and SIP cadence — sizing recommendations match their profile.
- Knows their goal text — tone matches a retiree differently from a young professional.

**3.4.5 Sample query types Ask Rupeya can handle.**

| Query type | Example | Tools used |
|---|---|---|
| Single-stock verdict | "Should I invest in ENGRO?" | profile, score, dcf, news, shariah, macro |
| Comparison | "Compare LUCK vs DGKC" | profile×2, score×2, dcf×2, compare |
| Alternative-finder | "Better than HBL but Shariah-compliant" | profile, find_alternatives, shariah |
| Sector view | "Is fertilizer good for 5 years?" | sector aggregate, news, macro |
| Portfolio question | "Is my portfolio too cement-heavy?" | get_user_portfolio, sector analysis |
| Education | "Explain margin of safety" | RAG over glossary (Tier C, no agent) |
| Hypothetical | "What if oil drops to $55?" | scenario tool over E&P/OMC stocks |
| Action follow-through | "Add OGDC to my next SIP" | writes to `sip_proposals` after confirmation |

**3.4.6 Safety rails specific to the agent.**
- Hard refuse: "Will it go up tomorrow?" → redirect to long-term framing.
- Hard refuse: "Give me a hot tip" → "I don't do tips. Let me show you the analysis instead."
- Hard refuse: any leverage/derivatives/futures recommendation.
- Always cite. If the agent cannot cite a source for a claim, it does not make the claim.
- Always disclaim. Every agent response ends with the standard disclaimer.

**3.4.7 Cost containment.**
- Free users: 5 agent queries/day (chat-style Tier C interactions still allowed).
- Paid users: 50 agent queries/day, 500/month.
- Cache common single-stock verdicts at the daily-stock-memo layer (Tier A); agent reuses cached score/IV/news when the data is < 6h old.

### 3.5 Guardrails

- **Disclaimer interceptor.** Every AI output is post-processed to append the standard disclaimer and to scrub any phrase like "guaranteed return", "100%", "definitely buy".
- **Confidence floor.** If quant data is < 70% complete for a stock (missing latest filings), we suppress AI output and show "Insufficient data — under review."
- **Stale-data warning.** If the most recent filing or price is > 7 days old, the UI auto-shows a yellow banner.

---

## 4. Fundamental Analysis Framework — The Rupeya Score

We score every covered PSX stock on **four pillars** (each 0–5), combine into a composite (0–5), and map to a 5-class verdict. The weights are tuned for *long-term* PSX investing in a high-inflation, frontier-market context — not US large-cap textbook investing.

### 4.1 Pillar 1 — Business Quality (weight 30%)
Sub-factors (each 0–5, equal weight):
1. **Moat strength** — market share leadership in PSX sector, brand pricing power, regulatory moat (e.g., refineries, OMCs), distribution network density.
2. **Industry attractiveness** — 5-year sector revenue CAGR, sector ROE vs PSX median, structural tailwinds (digitization, demographics, energy transition).
3. **Management quality** — promoter holding stability, related-party transaction ratio, audit qualifications, history of capital allocation (buybacks, dividends, M&A discipline).
4. **Earnings durability** — EPS volatility (std-dev / mean) over 5Y, % of years with positive EPS over 10Y.

### 4.2 Pillar 2 — Financial Health (weight 30%)
Sub-factors:
1. **Growth** — 5Y revenue CAGR, 5Y EPS CAGR, latest TTM growth vs 5Y trend.
2. **Returns** — ROE (5Y average + latest), ROIC, ROA. Penalize if ROE is driven by leverage > 2x equity.
3. **Leverage** — Debt/Equity, Net Debt/EBITDA, interest coverage. PSX-specific: exposure to circular debt, currency-mismatched USD borrowings.
4. **Cash generation** — FCF / Net Income (quality of earnings), 5Y cumulative FCF, working-capital intensity trend.

### 4.3 Pillar 3 — Valuation (weight 25%)
Sub-factors:
1. **Intrinsic value vs market price** — two-stage DCF with KIBOR+risk-premium discount rate; sensitivity table on growth and discount rate. Margin of safety = (IV − Price) / IV.
2. **Multiples vs own history** — current P/E, P/B, EV/EBITDA vs 5Y average and vs sector median. Z-score.
3. **Dividend yield + sustainability** — current yield, 5Y payout ratio, FCF coverage of dividend, dividend growth streak.
4. **Earnings yield vs PIB** — Pakistan-specific. Stock earnings yield (E/P) compared to 10-year PIB yield. The risk premium tells us if equities are cheap vs sovereign bonds.

### 4.4 Pillar 4 — News & Catalysts (weight 15%)
Sub-factors:
1. Recent earnings surprise (% beat/miss vs consensus or vs prior year).
2. Sector regulatory news (SECP, SBP, FBR, OGRA, NEPRA changes).
3. Material corporate actions (rights issue, buyback, M&A, dividend changes).
4. Macro catalysts (KIBOR moves, FX, IMF program status — applied as sector-level multipliers).

### 4.5 Shariah-Compliance Screening (CRITICAL for PK retail)

A material share of Pakistani retail investors will only invest in Shariah-compliant equities. Rupeya treats this as a **hard universe filter**, not a soft preference. The screen runs on every stock in the covered universe and produces a boolean `is_shariah_compliant` flag plus the underlying ratios for transparency.

**4.5.1 Source of truth.**
- Primary: **KMI All-Share Index** membership, published by PSX in collaboration with Meezan Bank's Shariah Advisory Board. Updated semi-annually (May and November). Approximately 200+ companies are listed; only ~50–80 are actively traded.
- Secondary: **AAOIFI Shariah Standards** for ratio screens (where KMI doesn't disclose its math we apply AAOIFI ourselves as a sanity check).

**4.5.2 Business activity screen** — exclude any company whose primary business is:
- Riba-based banking (conventional banks)
- Conventional insurance
- Alcohol, tobacco, gambling, casinos, conventional pornography
- Pork-related products
- Conventional asset management or brokerage
- Hotels with predominant non-halal F&B / entertainment exposure

Mixed-business companies are evaluated on revenue purity (impure revenue must be < 5% of total).

**4.5.3 Financial ratio screen** (AAOIFI thresholds — applied semi-annually using latest audited financials):
| Ratio | Test | Threshold |
|---|---|---|
| Interest-bearing debt / total assets | Must be less than | **33%** (some scholars 37%) |
| Non-Shariah-compliant investments / total assets | Less than | **33%** |
| Illiquid assets / total assets | Greater than or equal to | **25%** (asset-backing rule) |
| Interest income / total revenue | Less than | **5%** |

Companies that pass both screens get `is_shariah_compliant = true`. We store the ratios so the UI can show *why* a stock passed or failed.

**4.5.4 Purification (informational).** For users who want it, we surface the recommended *purification amount* — the small portion of dividends/gains that came from incidental non-compliant income, which strict scholars suggest donating to charity. We do not compute zakat, but we show the inputs needed.

**4.5.5 Implementation.**
- Schema: `stocks.is_shariah_compliant` (boolean, indexed) + `stocks.shariah_ratios` (JSONB).
- Refreshed: weekly cron pulls KMI index membership + recomputes ratios from latest filings.
- UI: a ☪ chip on every Shariah-compliant stock; a banner in Portfolio Builder/Doctor when `shariah_only = true` is active; a "Why was this excluded?" tooltip when filtering hides results.
- Edge case: if a held stock loses Shariah compliance mid-year (rare), trigger a soft alert ("Shariah status change") with a 30-day grace period suggestion before forced trim.

### 4.6 Stock Style Classification (Dividend / Growth / Both)

Beyond the score and verdict, every covered stock is classified by **investment style** so users can match holdings to their preference (Section 6.1, question 6: dividend / growth / balanced). The classification is computed deterministically from financials — never assigned by an LLM — and surfaced as a chip everywhere a stock is listed.

**Definitions** (computed from latest 5 years of audited data):

| Style | Tag | Criteria (must satisfy ALL) |
|---|---|---|
| **Dividend** | 💰 Dividend | Forward div yield ≥ 5%, 5Y dividend payout ratio ≥ 50%, 5Y EPS CAGR < 12%, FCF coverage of dividend ≥ 1.2x |
| **Growth** | 🚀 Growth | 5Y EPS CAGR ≥ 15%, dividend yield < 4%, ROIC ≥ 15%, reinvestment rate ≥ 60% |
| **Both** | ⚖️ Both | Dividend yield ≥ 4% AND 5Y EPS CAGR ≥ 10% AND payout ratio ≤ 70% — the rare "compounder" profile |
| **Cyclical** | 🔄 Cyclical | Earnings volatility coefficient > 0.4, sector ∈ (cement, OMC, refineries) — surfaced as supplementary tag, not primary |
| **Speculative** | ⚠️ Speculative | Negative FCF or losses in 2+ of last 5 years — auto-excluded from Builder unless user opts in |

**How it's used.**
- **Portfolio Builder:** the user's question-6 answer sets the target mix. *Dividend* preference biases ≥60% of the portfolio toward 💰 stocks; *Growth* biases ≥60% toward 🚀; *Balanced* targets ~⅓ each of 💰, 🚀, and ⚖️.
- **Portfolio Doctor:** if a held stock's style doesn't match the user's stated preference, the report flags it ("This is a Growth stock but you said you prefer dividend income — consider trimming and adding FFC instead").
- **Ask Rupeya:** the agent always names the style in its verdicts and explicitly addresses fit ("PSO is a Dividend stock; given your balanced preference, this would tilt your portfolio toward income").
- **UI:** style chip appears next to the company name on Portfolio, Dashboard, Doctor, Stock detail, and in agent verdicts.
- **Schema:** `stocks.style ENUM('dividend','growth','both','cyclical','speculative')`, recomputed weekly by the quant engine.

**Examples on PSX (illustrative — refreshed weekly):**
- ⚖️ **Both** (compounders that pay): ENGRO, MEBL, LUCK, MARI
- 💰 **Dividend** (high yield, modest growth): FFC, EFERT, HUBC, PSO, OGDC, FATIMA
- 🚀 **Growth** (reinvestment-heavy): SYS, NESTLE, AVN, GTYR, AIRLINK
- 🔄 **Cyclical** (supplementary tag, paired with primary style): cement, OMC, refineries

### 4.7 Composite & Verdict

```
RupeyaScore = 0.30·BQ + 0.30·FH + 0.25·VAL + 0.15·CAT      (range 0–5)
```

Verdict mapping (with mandatory flag overrides):

| Score | Default verdict | Override conditions |
|---|---|---|
| ≥ 4.2 AND margin of safety ≥ 25% | **STRONG BUY** | Force HOLD if going-concern/audit-qualified flag |
| 3.5 – 4.19 | **BUY** | Force HOLD if leverage flag triggered |
| 2.5 – 3.49 | **HOLD** | — |
| 1.8 – 2.49 OR price > IV × 1.30 | **TRIM** | — |
| < 1.8 OR going-concern flag OR D/E > 5x | **EXIT** | Always |

**Note on regulatory framing:** verdicts are presented in the UI as *"Rupeya Research Signal"* (e.g., "Research Signal: BUY"), never as "Rupeya recommends you buy." This wording, plus disclaimers, is what keeps us in the educational / research bucket and out of SECP advisory licensing.

---

## 5. Long-Term Investment Philosophy

The AI is opinionated. Its prompts and scoring weights enforce a single worldview:

1. **Own businesses, don't trade tickers.** A stock is a fractional claim on a real company's future cash flows.
2. **Time horizon is the edge.** PSX retail is dominated by short-term thinking. A 5–10 year horizon is structurally underpriced.
3. **Quality compounds; junk decays.** Better to overpay slightly for a great PSX business than to "bargain hunt" in structurally broken sectors.
4. **Margin of safety is non-negotiable.** Pakistan's macro is volatile (currency, inflation, politics). We require a wider margin of safety (≥25%) than a US value investor would.
5. **Cash is truth.** Earnings can be massaged; free cash flow is harder to fake. We weight FCF heavily.
6. **Dividends are discipline.** Companies that consistently pay rising dividends from real cash flow are self-policing for capital allocation.
7. **Diversify, but don't dilute.** **6–7 stocks across 4–5 sectors** is the sweet spot for Pakistani retail. A retail investor cannot meaningfully follow 12+ names; concentration forces conviction and makes every pick matter. We expand to **8–9 only when** an additional candidate carries RupeyaScore ≥ 4.2 AND opens a sector the portfolio doesn't already cover. Hard cap is **9**. Excellent runners-up go to the watchlist, not the portfolio. Index funds don't really exist meaningfully for KSE-100 retail; we partially fill that gap with a tightly curated active book.
8. **Boring beats brilliant.** Cement, fertilizer, banks, OMCs, food — boring PSX compounders are usually better than the latest "tech IPO."
9. **Know what you own.** Every recommendation comes with a 1-paragraph "Owner's Manual" the user can re-read in 60 seconds.
10. **Sit on your hands.** Default action is "do nothing." The platform actively *discourages* over-trading.

These principles become literal text in every system prompt to the LLM, and literal weights in the scoring engine. They are not decoration.

---

## 6. Core Features — Functional Specs

### 6.1 Investor Profiling (Onboarding Questionnaire)
**Questions (all multi-choice, 9 total — finishable in < 3 minutes):**
1. *What is your investment horizon?* < 1y / 1–3y / 3–5y / 5–10y / 10y+
2. *How would you react if your portfolio fell 30% in 6 months?* Sell everything / Sell some / Hold / Buy more
3. *Do you want to invest a lump sum, monthly SIP, or both?*
4. *Approximate portfolio size today?* < 50k / 50k–200k / 200k–1M / 1M–5M / 5M+
5. *How much can you invest each month?* < 5k / 5k–25k / 25k–100k / 100k+ / Variable
6. *Do you prefer dividend income or capital growth?*
7. *Have you invested in PSX before?* Never / 1–2 years / 3+ years
8. *Do you want only Shariah-compliant stocks?* Yes / No / Explain it to me first  ←  **NEW**
9. *Goal in your own words.* (free text — used by LLM to personalize tone)

**Output:** an Investor Profile object stored on the user record:
```json
{ "horizon_years": 7, "risk_score": 0.62, "income_vs_growth": "balanced",
  "monthly_sip_pkr": 15000, "lump_sum_pkr": 100000, "experience": "novice",
  "shariah_only": true,
  "goal_text": "House down-payment in 8 years" }
```

The `shariah_only` flag is **the most important filter in the entire system** — it determines the eligible universe for every Portfolio Builder run, every alternative-suggestion in the Doctor, every SIP allocation, and every Ask-Rupeya recommendation. See Section 4.6 for the screening framework.

### 6.2 AI Portfolio Builder
Inputs: Investor Profile.

**Sizing target (concentrated by design).** Rupeya recommends **6–7 holdings** by default. The optimizer expands to **8–9 only when** an additional candidate clears RupeyaScore ≥ 4.2 AND opens a sector not already represented. **Hard cap: 9 holdings.** Runners-up go to the watchlist. The rationale is in Section 5, principle 7: a retail investor cannot meaningfully follow 12+ names, and concentration forces conviction.

Algorithm:
1. **Universe filter** — start from the ~80 covered PSX stocks, filter out those failing minimum quality thresholds (e.g., RupeyaScore < 3.0, going-concern flags). **If `shariah_only = true`, hard-filter to KMI All-Share Index members only (~50 PSX stocks).**
2. **Sector caps** — apply max-per-sector rule (default 30% per sector for balanced profile, 35% for aggressive, 25% for conservative). Caps are slightly higher than the previous 8–12 sizing because position counts are smaller.
3. **Risk-tier mix** — split target capital between three buckets (% varies by user risk score):
   - *Anchor tier* (large-cap dividend payers — banks, OMCs, fertilizers)
   - *Compounder tier* (high-quality mid-caps)
   - *Opportunity tier* (special situations / undervalued cyclicals)
4. **Optimizer** — pick the top-N (where N starts at 7) maximizing composite RupeyaScore, subject to sector caps and a minimum-position-size rule (no position < 10% of portfolio — concentration means each position must matter). Then apply the **expansion rule**: scan ranks 8–10 and add any candidate that BOTH scores ≥ 4.2 AND opens a new sector. Stop at 9 holdings even if more candidates qualify.
5. **Output** — 6–9 stocks with target weights, expected dividend yield, blended margin of safety, and a 1-page narrative explaining sector logic. **A separate "Watchlist runners-up" section** lists the next 3–5 stocks that scored well but didn't make the portfolio, with one-line reasoning on why each was excluded (sector full, slightly lower score, etc.).

User can accept, swap any stock for the next-best alternative, or save and revisit.

### 6.3 Portfolio Doctor
Input: user pastes/uploads existing holdings (ticker, qty, avg cost). CSV import too.

Output report:
- Per-stock verdict (STRONG BUY / BUY / HOLD / TRIM / EXIT) with 3-paragraph reasoning.
- **Strengths** section — what's working (e.g., "65% of portfolio is in companies with ROE > 18%").
- **Weaknesses** section (e.g., "42% concentrated in one sector — cement").
- **Diversification map** — sector pie + concentration risk score.
- **Overvalued holdings** list (price > IV × 1.20).
- **Undervalued opportunities** — stocks NOT in the user's portfolio that would improve the risk-adjusted RupeyaScore most.
- **Action plan** — ranked list of 3–5 specific moves, each with rupee amounts.

### 6.4 Daily AI Stock Analyst (Phase 1.5)
Each evening at 19:00 PKT, after PSX close:
1. Scraper pipeline pulls new prices, filings, news.
2. Quant Engine recomputes scores for any stock with new data.
3. LLM generates a ≤200-word memo per stock that changed materially (score Δ > 0.3 or new filing).
4. Per-user "alert digest" composed: only stocks the user owns or has watchlisted, only material changes.
5. Delivery: in-app inbox + email + (Phase 2) WhatsApp Business message.

### 6.5 SIP Investing Engine
- User sets monthly amount + auto-debit reminder day.
- On reminder day, the engine proposes that month's allocation:
  - If portfolio is on-target → buy more of best-RupeyaScore underweight holding.
  - If portfolio is drifted (any position > target ±20%) → buy only underweight names until rebalanced.
  - If a held name has dropped to EXIT → propose redeploy to nearest replacement.
- User executes manually with their broker; we record the trade.
- Quarterly rebalance health check shows drift heatmap.

### 6.6 Alerts & Notifications
Trigger types:
- Price below IV × 0.80 → "Margin of safety expanded"
- Quarterly result published → "New financials available"
- Score drop ≥ 0.5 → "Watch this name"
- Dividend declared → "Dividend incoming"
- Better alternative emerges (RupeyaScore > held score by ≥0.7) → "Consider swap"

Channels: in-app, email (Resend free tier 3k/mo), push (Phase 2), WhatsApp (Phase 3).

### 6.6.1 Stock Comparison Module

A dedicated side-by-side comparison tool that lets users stack 2–4 PSX stocks across the same fundamental framework. This is the most-used feature on every quality investor platform globally; for PSX retail it's a critical confidence-builder before committing capital.

**Inputs.** 2–4 tickers. Optional filters: Shariah-only on/off, style (dividend/growth/both/all).

**Output.** A comparison matrix with the best value in each row visually highlighted, plus an AI-generated synthesis paragraph naming the "best pick for X" across the candidates.

**Comparison sections (each row contains all selected stocks side-by-side):**
1. **Verdict & Score** — research signal, RupeyaScore composite + 4 pillars (mini bars), style classification, Shariah status
2. **Valuation** — current price, intrinsic value (DCF), margin of safety, P/E TTM, P/E vs 5Y avg, EV/EBITDA
3. **Quality & Returns** — Revenue/EPS 5Y CAGR, 5Y avg ROE, ROIC, FCF/Net Income
4. **Income** — forward div yield, 5Y avg payout, 5Y dividend growth, dividend streak
5. **Risk** — Debt/Equity, interest coverage, earnings volatility, macro flags

**AI synthesis prompt template** (Tier B — Sonnet):
```
System: You are Rupeya, a Pakistani long-term equity research analyst. You will receive
a JSON comparison block of 2–4 PSX stocks with computed metrics. Produce a synthesis
that names the "best pick" for 3–4 different investor types from this set, in 3–4 short
paragraphs. Always cite specific metrics. Never invent numbers. Always end with the
education-not-advice disclaimer.

Input: {comparison_block_json}

Output requirements:
- Lead paragraph: "If you can only pick one: <TICKER>" with reasoning.
- Per-archetype paragraphs: best for income, best for growth, best for value, etc.
- Methodology footnote.
```

**UX behavior.**
- Best metric per row gets a green ✓ highlight (server-side computed — never asked of LLM).
- "n/a" handled cleanly for sector-inapplicable metrics (e.g., D/E for banks).
- Mobile: horizontal scroll on the table, sticky leftmost column.
- Sharable URL: `/compare?tickers=ENGRO,MEBL,PSO,FFC&shariah=1`.
- "Add winner to portfolio" CTA wired to Portfolio Builder's swap flow.

**Schema:** uses existing `stock_scores` and `fundamentals_quarterly` — no new tables needed.

### 6.7 Analytics Dashboard
Five widgets, all explainable to a beginner:
1. **Portfolio Health** — single 0–100 score with traffic-light color and 1-line "what to do."
2. **Dividend Projections** — next 12 months expected dividend rupees, by stock, by month.
3. **Intrinsic Value vs Market Price** — bar chart per holding, color-coded.
4. **Sector Allocation** — donut + concentration warning if any sector > 35%.
5. **Risk Score** — beta, drawdown estimate, leverage exposure rolled into one 0–10 number.

Every widget has a "Why does this matter?" tooltip in plain Urdu/English.

---

## 7. Product Workflow (UX)

### 7.1 Landing page
- Headline: *"Pakistan's first AI stock analyst for long-term investors."*
- 3-step explainer: Tell us about you → Get a portfolio → Watch it work.
- Live "Stock of the Day" preview (no login needed).
- Pricing card. PKR 500/2,500/5,000.
- Bilingual EN/UR toggle.
- Big disclaimer footer.

### 7.2 Onboarding (≤ 3 minutes)
Sign up (email magic link or Google) → 8-question quiz → Profile summary → "Build my portfolio" CTA → AI Portfolio Builder result page → save & move to dashboard.

### 7.3 Returning-user dashboard
Top: Portfolio Health card.
Middle: Today's Insights (≤3 cards — the only place we surface AI calls to action).
Bottom: Holdings table with mini-verdicts.
Right rail: "Ask Rupeya" chat.

### 7.4 Portfolio Doctor flow (one-time and on-demand)
Paste/upload → analysis runs in < 30s → report page with downloadable PDF → "Apply suggested changes" wizard.

### 7.5 SIP flow
Set monthly amount → choose auto-allocation rule → on the day, in-app card shows "This month, buy X PKR of Y" → user clicks "Mark as bought" → we record the trade.

### 7.6 UX principles
- One primary action per screen.
- Numbers shown with rupee formatting (`PKR 1,25,000` South-Asian numerals as a toggle).
- Every chart has a one-sentence summary above it.
- Education is *embedded*, not in a separate "Learn" tab — every term in the UI is a hover-glossary link.
- Mobile-first responsive; targets 380px width as primary.
- Dark mode default (lower power, looks premium).
- Bilingual (Urdu + English) UI strings via i18n.

---

## 8. Database Design (Postgres / Supabase)

```sql
-- USERS & PROFILES
users (id, email, created_at, plan, plan_renews_at, role)
investor_profiles (user_id PK, horizon_years, risk_score, income_vs_growth,
                   monthly_sip_pkr, lump_sum_pkr, experience, goal_text, updated_at)

-- STOCKS UNIVERSE
stocks (ticker PK, name, sector, sub_sector, listed_date, market_cap_pkr,
        is_covered, last_priced_at)
prices_daily (ticker, date, open, high, low, close, volume, PRIMARY KEY (ticker, date))
fundamentals_quarterly (ticker, period, revenue, net_income, eps, book_value,
                        debt, cash, fcf, dividend_per_share, ...,
                        PRIMARY KEY (ticker, period))
filings (id, ticker, type, period, source_url, raw_pdf_path, parsed_at)
news_items (id, ticker, source, url, headline, body_excerpt, published_at,
            sentiment_score, embedding vector(1536))

-- AI / ANALYSIS
stock_scores (ticker PK, business_quality, financial_health, valuation,
              catalysts, composite, intrinsic_value_pkr, margin_of_safety,
              flags JSONB, computed_at, model_version)
ai_summaries (id, ticker, kind, text, sources JSONB, generated_at, llm_model)
embeddings (id, source_type, source_id, chunk_text, embedding vector(1536))

-- USER PORTFOLIOS
portfolios (id, user_id, name, type ENUM('builder','manual','imported'), created_at)
holdings (id, portfolio_id, ticker, quantity, avg_cost_pkr, target_weight, added_at)
trades (id, portfolio_id, ticker, action, qty, price_pkr, executed_at, source)

-- SIP
sip_plans (id, user_id, monthly_amount_pkr, day_of_month, active, created_at)
sip_proposals (id, sip_plan_id, for_month, allocation JSONB, generated_at, executed)

-- ALERTS
alerts (id, user_id, ticker, type, payload JSONB, created_at, read_at,
        delivered_channels JSONB)
watchlist (user_id, ticker, added_at, PRIMARY KEY (user_id, ticker))

-- BILLING
subscriptions (id, user_id, plan, started_at, ends_at, status, gateway,
               last_invoice_id)
payments (id, user_id, amount_pkr, method, gateway_ref, receipt_url, status,
          verified_by, created_at)

-- AUDIT / OPS
audit_log (id, actor, action, entity_type, entity_id, payload JSONB, at)
scrape_runs (id, source, started_at, finished_at, rows_written, errors JSONB)
```

**RLS (Row-Level Security) policies** — every user-owned table has:
```sql
CREATE POLICY "owner can read"   ON portfolios FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "owner can write"  ON portfolios FOR ALL    USING (auth.uid() = user_id);
```

**Indexes (priority):**
- `prices_daily (ticker, date DESC)`
- `news_items (ticker, published_at DESC)`
- HNSW index on `embeddings.embedding` for RAG.
- `holdings (portfolio_id)` for fast dashboard load.

---

## 9. API Surface

### 9.1 Public (read-only, rate-limited)
- `GET /api/stocks` — paged universe with latest score
- `GET /api/stocks/:ticker` — full profile (price, fundamentals, score, latest summary)
- `GET /api/insights/today` — 3 cards for landing page

### 9.2 Authenticated user
- `POST /api/profile` — create/update Investor Profile
- `POST /api/portfolio/build` — run Portfolio Builder against current profile
- `POST /api/portfolio/doctor` — analyze submitted holdings
- `GET  /api/portfolio/:id` — fetch a saved portfolio
- `POST /api/portfolio/:id/holdings` — add/edit a holding
- `POST /api/sip/plan` / `GET /api/sip/proposal/:month`
- `POST /api/watchlist/:ticker`
- `GET  /api/alerts` / `POST /api/alerts/:id/read`
- `POST /api/ask` — Ask-Rupeya chat (RAG-grounded)

### 9.3 Internal (cron + admin)
- `POST /internal/scrape/psx` — refresh prices
- `POST /internal/scrape/news` — pull news from configured sources
- `POST /internal/score/recompute?ticker=` — recompute one or all
- `POST /internal/ai/dailymemos` — generate Tier-A daily memos
- `POST /admin/payments/verify` — manual bank-transfer verification

### 9.4 Webhooks
- `Safepay → /webhooks/safepay/payment` (Phase 1.5)
- `Resend → /webhooks/resend/email-event` (delivery tracking)

All endpoints: JSON, JWT-bearer auth via Supabase, per-user rate limits via Upstash Redis (free tier).

---

## 10. Recommended Tech Stack

| Layer | Choice | Why | MVP cost |
|---|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui | Best AI-coder support; PWA-ready; great free tier | $0 |
| Hosting (web) | Vercel | One-click Next.js deploy, generous free tier | $0 |
| DB + Auth + Storage | Supabase (Postgres + Auth + Storage + RLS + pgvector) | Replaces 4 services; founder can use Studio GUI | $0 → $25/mo |
| Backend API | Next.js Route Handlers + Supabase Edge Functions | No separate server needed for most CRUD | $0 |
| Quant Engine | Python 3.11 + FastAPI + pandas + numpy + numpy-financial | Financial libs are Python-native | $0 (Render free) |
| Quant hosting | Render free tier OR Railway $5 credit | Auto-deploy from GitHub | $0–5/mo |
| Scrapers | Python + httpx + selectolax + playwright (only when JS needed) | Fast and cheap | $0 |
| Cron | GitHub Actions (free 2,000 mins/mo) | No infra, version-controlled | $0 |
| LLMs | Anthropic Claude (Haiku + Sonnet), Google Gemini Flash (free overflow) | Best cost/quality at MVP scale | $5–30/mo |
| Vector DB | Supabase pgvector | Same DB; no extra service | $0 |
| Email | Resend free tier (3k/mo) → paid | Best-in-class DX | $0 → $20/mo |
| Push (Phase 2) | OneSignal free | PWA + future native | $0 |
| Payments (MVP) | Manual bank transfer | Zero cost, zero friction for founder | $0 |
| Payments (1.5) | Safepay | Cards + JazzCash + EasyPaisa, single integration | ~3% MDR |
| Analytics | PostHog free tier | Product analytics + funnels + replays | $0 |
| Error monitoring | Sentry free tier | 5k events/mo | $0 |
| CDN / WAF | Cloudflare free | Defense + caching | $0 |
| Domain | rupeya.ai (~$50/yr) | Brand | $5/mo |
| **Total MVP infra** | | | **~$10–50/month** |

---

## 11. AI-Coder Workflow for a Non-Coder Founder

Because the founder is not a developer, the build process is structured to maximize AI leverage:

1. **Spec-first.** Each feature begins as a Markdown spec (this blueprint is the master spec). Specs go into `/docs/specs/` in the repo.
2. **One feature, one branch, one AI session.** Use Cursor or Claude Code to implement one spec at a time. Never let the AI work on two features at once.
3. **Vercel preview deployments.** Every branch auto-deploys to a preview URL. Founder reviews UX visually; AI iterates from screenshots.
4. **Supabase Studio for data.** Founder can read tables, run SQL safely, edit RLS in the GUI. No need to learn psql.
5. **Tested by an evaluator agent.** A separate "QA agent" runs end-to-end Playwright tests after each merge.
6. **Lovable/v0 for UI scaffolding only.** First-pass UI from v0; refine in Cursor.
7. **Daily backup.** Supabase auto-backups + a weekly `pg_dump` to Cloudflare R2.
8. **Read-only first, write later.** Ship read-only flows (browsing stocks, viewing scores) before any write flow (saving portfolios). De-risks data corruption.

---

## 12. Development Roadmap

### Phase 1 — MVP (Weeks 1–14)
**Goal:** A founder + AI-agent team ships a paid product with first 50–100 users.

| Wk | Workstream | Deliverable |
|---|---|---|
| 1 | Foundation | Repo, Vercel, Supabase, domain, design system, bilingual scaffold, legal/disclaimer copy, Privacy Policy, ToS |
| 2 | Data spine | Schema + RLS + first scrape of PSX prices (~80 tickers) + nightly cron |
| 3 | Fundamentals scrape | Annual/quarterly results scrape from PSX + Business Recorder + company IR; dump into `fundamentals_quarterly` |
| 4 | Quant engine v0 | Ratios + intrinsic value (DCF) + composite score for the universe |
| 5 | Public site | Landing, pricing, public stock pages, "Stock of the Day" |
| 6 | Auth + onboarding | Sign-up, magic link, 8-question profiling, profile summary |
| 7 | Portfolio Builder | Algorithm + result page + save flow |
| 8 | Portfolio Doctor | Holdings input + analysis + report + PDF export |
| 9 | Dashboard | 5 widgets + watchlist + Ask-Rupeya v1 (Haiku RAG) |
| 10 | Subscription paywall | Bank-transfer flow + admin verification + plan gates |
| 11 | Alerts v1 | Email digest + in-app inbox |
| 12 | Closed beta | 20–30 invited testers, daily fixes |
| 13 | Polish | Performance, copy, edge-cases, RTL polish for Urdu |
| 14 | **Public launch** | Press: Profit Pakistan, Sarmaya, LinkedIn, Twitter, WhatsApp groups |

**Phase 1 success criteria:** ≥100 signups, ≥30 paying users, churn < 15%, no data corruption incidents, AI verdict accuracy spot-checked on 30 stocks by founder.

### Phase 1.5 — Activation (Weeks 15–22)
- Safepay integration (cards + JazzCash + EasyPaisa).
- Daily AI Stock Analyst (Tier A pipeline live for top-50 PSX).
- WhatsApp opt-in alerts via Business API.
- Onboarding tutorial videos in Urdu + English.
- Referral program (1 month free for each paid referral).

### Phase 2 — Advanced AI Analyst (Months 6–12)
- License Mettis or PSX DataPortal (move off scraping for prices).
- Backtesting module — show historical performance of RupeyaScore.
- Sector deep-dives (cement, banks, OMC, fertilizer, IPP, food) — long-form AI memos.
- Earnings-call summarization (audio-to-text + LLM digest).
- Compare tool — side-by-side fundamentals/valuation.
- Native Android app (React Native) wrapping core flows.
- Hire 1 full-stack engineer + 1 PSX research analyst.

### Phase 3 — Market Intelligence Platform (Year 2)
- Pursue SECP Investment Advisor licensing OR partner with a licensed entity.
- Institutional / advisor tier (PKR 25,000–50,000/month) — multi-client portfolios, white-label.
- API access for fintechs and brokers.
- Mutual-fund and ETF coverage.
- Roboadvisor with broker tie-in (auto-execute via partner brokers).
- Expand to Dhaka Stock Exchange and Sri Lanka CSE (similar frontier-markets thesis).

---

## 13. Monetization

### 13.1 Pricing (locked)
- **Monthly:** PKR 500
- **6-month:** PKR 2,500 (saves PKR 500 — equivalent to 17%)
- **Annual:** PKR 5,000 (saves PKR 1,000 — equivalent to 17%)

### 13.2 Free vs Paid (freemium ladder)
| Capability | Free | Paid |
|---|---|---|
| Browse public stock pages with score + 1-paragraph summary | ✅ | ✅ |
| Investor Profile + saved portfolio (1) | ✅ (read-only on builder) | ✅ |
| AI Portfolio Builder (full result with weights & narrative) | Locked | ✅ |
| Portfolio Doctor full report | First analysis free, then locked | ✅ unlimited |
| Daily AI memos for held stocks | Locked | ✅ |
| Ask Rupeya chat | 5 messages/day | Unlimited |
| Watchlist size | 5 | 50 |
| Alerts via email | ✅ | ✅ |
| Alerts via WhatsApp (Phase 1.5) | Locked | ✅ |
| Multiple portfolios | 1 | up to 5 |
| Export PDF reports | Locked | ✅ |

### 13.3 Unit economics (target by month 12)
- ARPU: PKR 420/month (mix of monthly + discounted annual)
- COGS per active user: ~PKR 80/month (LLM + infra + payment fees)
- Gross margin: ~80%
- Break-even: ~600 paying users
- Year-1 target: 1,500 paying users → PKR ~7.5M ARR

### 13.4 Future monetization (Phase 3)
- Institutional/advisor tier
- Affiliate revenue from partnered SECP-licensed brokers (clearly disclosed)
- White-label deals with banks/brokers wanting an in-house "AI analyst"
- Sponsored research deeply disclaimed (avoid this — brand-damaging)

---

## 14. Scaling Strategy

### 14.1 Compute scaling
- Up to ~10,000 active users: current stack with paid Supabase ($25–$60/mo) and Vercel Pro ($20/mo) handles it.
- 10k–50k users: upgrade Supabase to Team tier; move quant engine to dedicated container (Fly.io/Railway $20–80/mo); add read-replica.
- 50k+: separate hot path (RSC + edge cache) from quant batch path; CDN-cache public stock pages aggressively (60% of traffic).

### 14.2 LLM cost containment
1. **Cache aggressively.** Tier-A summaries cached per stock per day → cost grows with stock count, not user count.
2. **Tiered models.** Default Haiku, escalate to Sonnet only for Portfolio Doctor and high-stakes outputs.
3. **Prompt compression.** Score JSON, not raw filings, into prompts. Average prompt < 1k tokens.
4. **Per-user quotas.** Free = 5 chat msgs/day, Paid = 100/day. Hard cap.
5. **Negotiate Anthropic startup credits / Gemini free tier** for first 12 months.

### 14.3 Data-pipeline scaling
- Move from scraping to licensed feed when paying users > 500 (cost per user falls below PKR 50).
- Backfill historical data into a dedicated `prices_intraday` table only if charts/backtesting demand it.
- Use Cloudflare Queues + Durable Objects for distributed scraping if rate-limited.

### 14.4 Team scaling
- Months 0–6: Founder + AI agents.
- Months 6–12: +1 senior full-stack engineer (Pakistan, ~PKR 250k/mo) + 1 PSX research analyst (part-time, PKR 80k/mo).
- Months 12–24: +1 designer, +1 ML engineer, +1 customer success.

### 14.5 Geographic & product scaling
- Diaspora payments (Phase 2) unlock GCC + UK + US Pakistanis (3–5x ARPU willing).
- Replicate to other frontier markets in Year 3+ where PSX-style data scarcity creates the same retail pain.

---

## 15. Security & Privacy

1. **Auth.** Supabase Auth (email + magic link + Google). MFA optional in Phase 1.5; mandatory for admin accounts now.
2. **Authorization.** RLS on every user-owned table. Verified by an automated test suite.
3. **Secrets.** All keys in Vercel + Supabase env vars; nothing in repo. Rotated quarterly.
4. **PII minimization.** We do NOT store CNIC, account numbers, broker creds. Holdings are typed in by user; no broker integration in MVP (huge risk reduction).
5. **Payments.** Bank receipts stored in Supabase Storage with a 90-day retention; access logged. Phase 1.5: PCI burden lives with Safepay (we never see card data).
6. **Data residency.** Supabase Singapore region for closest latency to PK; document this clearly.
7. **Backups.** Daily Supabase backup + weekly `pg_dump` to Cloudflare R2 with 30-day retention.
8. **Disclaimers + audit trail.** Every AI verdict is stored with model version, prompt hash, and quant inputs — so we can reconstruct any output if challenged.
9. **Rate limiting & abuse.** Upstash Redis per-IP and per-user limits on AI endpoints. Cloudflare WAF.
10. **Vulnerability hygiene.** Dependabot + `npm audit` + Snyk free tier. Pen-test before Phase 2 launch.
11. **Right to delete.** "Delete my account" is one click; cascades via FK, holdings purged immediately, backups expire in 30 days.
12. **Compliance hooks.** Even though we are positioned as educational, we maintain:
    - Investor Profile suitability log (so we can argue advice was not blanket).
    - Bilingual standardized disclaimer on every recommendation surface.
    - Annual review with a Pakistani securities lawyer (~PKR 150k/yr budgeted).

---

## 16. Legal & Compliance Posture

**Position:** Rupeya.ai is an *educational and research-tool platform*. We provide AI-generated analysis, scoring, and research signals based on publicly available information about PSX-listed companies. **We do NOT provide personalized investment advice as defined under the SECP (Securities Advisors) Regulations.** Verdicts are framed as "Research Signals," not buy/sell orders.

**Mandatory disclaimers** (must appear on every page that shows a verdict, intrinsic value, or portfolio):
> *Rupeya.ai is an educational research tool, not a SECP-licensed investment advisor. All content is generated by AI from public information and may contain errors. Stock prices are subject to market risk. Past performance does not guarantee future results. Please consult a SECP-registered financial advisor before making investment decisions. You alone are responsible for your trades.*

**Operational rules baked into prompts and UI:**
- Never use phrases like "guaranteed return," "definitely buy," "you should buy now."
- "Strong Buy" is rendered as "Research Signal: Strong Buy" with an explicit "research only" badge.
- AI cannot answer "Should I buy XYZ?" with a yes/no — it returns the score + the reasoning + the disclaimer.
- Onboarding includes a click-through ToS checkbox acknowledging the educational nature.

**Roadmap:**
- Year 1: Operate as educational tool. Engage securities lawyer for annual review.
- Year 2: Either pursue SECP Investment Advisor registration OR partner with a licensed entity to white-label "personal advice" tier. Decide based on user demand and capital.

**Other legal items:**
- Pakistani private limited company (SMC-Pvt-Ltd) for liability shielding.
- Tax registration with FBR; NTN; quarterly sales-tax filing on subscription revenue.
- Trademark "Rupeya.ai" (~PKR 25k filing).
- Standard ToS, Privacy Policy, Refund Policy, Cookie Policy — drafted by lawyer, bilingual.

---

## 17. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Scraping breaks (PSX/source changes layout) | Multi-source redundancy; alerting on scrape failures; license real feed by Phase 2. |
| Investing.com scraper blocked by Cloudflare / captchas | Use Playwright with browser-realistic fingerprints, slow request pacing (1 req / 3 sec), residential-IP fallback if needed; treat investing.com as a *secondary* source for cross-validation, with PSX/BR as primary; gracefully degrade if blocked. Reconsider paid API tier if free path becomes unreliable. |
| LLM hallucination on financials | Quant-First/LLM-Last rule; numbers never come from LLM; outputs cite sources. |
| SECP regulatory action | Educational positioning + disclaimers + lawyer on retainer + roadmap to licensing. |
| Payment fraud / chargebacks (Phase 1.5) | Safepay handles. Manual KYC for high-tier subs. |
| Founder burnout / single point of failure | AI-agent leverage; document everything in repo; hire by Month 6. |
| Currency volatility hits LLM costs (PKR ↔ USD) | Cache aggressively; secure annual prepay deals with Anthropic; price-tested PKR plans hold ≥75% gross margin even at PKR 350/USD. |
| Bear market kills retail interest | Lean cost base; Phase-1 break-even at 600 users; diaspora subscribers smooth volatility. |
| Competitor (e.g., a broker) copies | Speed; brand; community; data moat from longitudinal user portfolios. |

---

## 18. Open Questions (Defer or Confirm)

These are the questions I'd still want explicit answers to before locking detailed sprint planning. **None of them block MVP build.**

1. **Stock universe size at launch** — should MVP cover full ~520 PSX stocks, KSE-100 only, or top-80 most-traded? *Recommendation: top-80 most-traded with ≥3 years of filings.*
2. **Bilingual depth** — do AI-generated narratives need to be available in Urdu from day one, or English first + Urdu in Phase 1.5? *Recommendation: English first, professional Urdu in Phase 1.5.*
3. **Founder time commitment** — full-time or evenings/weekends? Roadmap above assumes full-time founder by Week 1.
4. **Initial capital available** — for legal incorporation, lawyer, domain, and 6 months of paid-tier infra (~PKR 500k–1M is comfortable). Confirm so we can phase spend.
5. **Co-founder?** Highly recommend a technical or research co-founder with PSX domain experience by Phase 1.5.
6. **Brand identity** — does the founder have a logo, brand voice, type system? If not, we can scaffold via v0 in Week 1.
7. **First-100 users channel** — will the founder use existing networks (LinkedIn, WhatsApp, university alumni), influencer partnerships (Profit/Sarmaya), or paid acquisition? *Recommendation: warm + influencer for first 200, paid only after retention proven.*

---

## 19. Acceptance Criteria for "MVP Ready"

The MVP is ready to launch publicly when **all** of the following are true:

- 80 PSX stocks covered with up-to-date prices (< 24h), latest 8 quarterly fundamentals, and a current RupeyaScore.
- Onboarding completes in < 3 minutes; profile saved.
- Portfolio Builder returns 6–7 stocks (up to 9 in qualifying special cases per Section 6.2 expansion rule) with weights, narrative, and a "Runners-up Watchlist" in < 30 seconds.
- Portfolio Doctor accepts ≥10 holdings and produces a report with verdicts in < 60 seconds.
- Subscription paywall blocks gated features; manual bank-transfer verification works end-to-end.
- All disclaimers visible on all gated surfaces.
- RLS policies pass automated test suite.
- Daily scrape + score-recompute cron runs unattended for 7 consecutive days.
- Founder has spot-checked 30 random verdicts and agrees with reasoning.
- Privacy Policy + ToS + Refund Policy reviewed by Pakistani securities lawyer.
- Status page, support inbox (`support@rupeya.ai`), and a written runbook exist.

---

## 20. Quick-Start: Week 1 Concrete Actions for the Founder

Day-by-day for Week 1, assuming AI-assisted coding:

1. **Day 1.** Buy `rupeya.ai` domain. Create GitHub org. Spin up Vercel + Supabase projects. Install Cursor.
2. **Day 2.** Use `v0.dev` to scaffold landing page from this blueprint's Section 7.1; deploy to Vercel.
3. **Day 3.** In Supabase Studio, create the schema from Section 8 by pasting the SQL. Enable RLS; add policies.
4. **Day 4.** In Cursor, prompt Claude to build the auth flow against Supabase. Deploy preview.
5. **Day 5.** Draft and publish ToS, Privacy Policy, Refund Policy, Disclaimer footer (lawyer review scheduled in parallel).
6. **Day 6.** Write the Python scraper for PSX daily prices (top-80 tickers); set up GitHub Actions cron.
7. **Day 7.** Founder review: landing live, auth working, schema in place, scraper running. Public stock-page MVP starts Week 2.

---

*End of blueprint. This document is the single source of truth for engineering, design, and business decisions. All deviations should be proposed as PRs against this file.*
