# Rupeya.ai — Scrapers

Python services that populate the Supabase database with PSX market data.
This is the *data spine* of the product — without it, every score and verdict
in the Next.js app shows mock data.

---

## What lives here

| Phase | Script | What it does |
|---|---|---|
| B2 | `scrape_prices.py` | Daily PSX prices for the covered universe (KSE-100) → `prices_daily` |
| B2 | `seed_universe.py` | One-time: load the KSE-100 ticker list → `stocks` |
| B3+ | (later) | Fundamentals, filings, news, embeddings |

## Local setup (one time)

```cmd
cd C:\Users\Abdullah\Documents\Claude\Projects\Rupeya.ai\scrapers
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then open `.env` in Notepad and paste your `SUPABASE_SERVICE_ROLE_KEY`
(the `sb_secret_...` value — same one in your Next.js `.env.local`).

## Running a scrape locally

Activate the virtual environment first:

```cmd
.venv\Scripts\activate
```

Then:

```cmd
python seed_universe.py     # one-time, populates the stocks table
python scrape_prices.py     # daily, populates prices_daily
```

## Production (GitHub Actions cron)

The scraper runs automatically every weekday at 18:00 PKT via
`.github/workflows/scrape-prices.yml`. Secrets are injected from
GitHub repo settings (Settings → Secrets and variables → Actions).

---

## Architecture notes

- **Idempotent.** `scrape_prices` upserts on `(ticker, date)`. Re-running
  it 100 times for the same trading day overwrites the same rows — never
  corrupts history.
- **Polite.** 1 request per second to PSX by default (`SCRAPE_DELAY_SECONDS=1`).
  Bumps up if PSX rate-limits, never down.
- **Observable.** Every run writes a row to `scrape_runs` with start/end
  timestamps, rows written, and any errors caught.
- **Service-role.** Scrapers use the Supabase service-role key, which
  bypasses RLS. This is the only context that key is allowed to live in
  besides the Next.js server-side admin paths.
