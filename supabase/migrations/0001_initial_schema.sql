-- Rupeya.ai — Initial schema migration (v0.1)
-- Implements blueprint Section 8 (database design) + Section 15 (RLS).
--
-- Run this in Supabase Studio → SQL Editor → paste → Run.
-- Idempotent where reasonable; safe to re-run on a fresh project.
--
-- ============================================================
--  EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for embeddings

-- ============================================================
--  USERS & PROFILES
--  Supabase Auth manages auth.users. We mirror with public.profiles
--  so app code never touches the auth schema directly.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email           TEXT NOT NULL,
  plan            TEXT NOT NULL DEFAULT 'free'
                    CHECK (plan IN ('free','monthly','six_month','annual')),
  plan_renews_at  TIMESTAMPTZ,
  role            TEXT NOT NULL DEFAULT 'user'
                    CHECK (role IN ('user','admin')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.investor_profiles (
  user_id           UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
  horizon_years     INT,
  risk_score        NUMERIC(3,2),
  income_vs_growth  TEXT CHECK (income_vs_growth IN ('income','growth','balanced')),
  monthly_sip_pkr   NUMERIC(12,2),
  lump_sum_pkr      NUMERIC(14,2),
  experience        TEXT,                 -- 'novice' | '1-2y' | '3+y'
  shariah_only      BOOLEAN NOT NULL DEFAULT FALSE,
  goal_text         TEXT,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
--  STOCKS UNIVERSE
-- ============================================================

CREATE TABLE IF NOT EXISTS public.stocks (
  ticker                TEXT PRIMARY KEY,
  name                  TEXT NOT NULL,
  sector                TEXT,
  sub_sector            TEXT,
  listed_date           DATE,
  market_cap_pkr        NUMERIC(20,2),
  is_covered            BOOLEAN NOT NULL DEFAULT FALSE,
  is_shariah_compliant  BOOLEAN,
  shariah_ratios        JSONB,
  style                 TEXT CHECK (style IN ('dividend','growth','both','cyclical','speculative')),
  last_priced_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_stocks_shariah ON public.stocks (is_shariah_compliant);
CREATE INDEX IF NOT EXISTS idx_stocks_covered ON public.stocks (is_covered);

CREATE TABLE IF NOT EXISTS public.prices_daily (
  ticker  TEXT NOT NULL REFERENCES public.stocks(ticker) ON DELETE CASCADE,
  date    DATE NOT NULL,
  open    NUMERIC(12,4),
  high    NUMERIC(12,4),
  low     NUMERIC(12,4),
  close   NUMERIC(12,4),
  volume  BIGINT,
  PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_prices_daily_ticker_date
  ON public.prices_daily (ticker, date DESC);

CREATE TABLE IF NOT EXISTS public.fundamentals_quarterly (
  ticker             TEXT NOT NULL REFERENCES public.stocks(ticker) ON DELETE CASCADE,
  period             TEXT NOT NULL,           -- e.g. '2025-Q1'
  revenue            NUMERIC(20,2),
  net_income         NUMERIC(20,2),
  eps                NUMERIC(12,4),
  book_value         NUMERIC(20,2),
  debt               NUMERIC(20,2),
  cash               NUMERIC(20,2),
  fcf                NUMERIC(20,2),
  dividend_per_share NUMERIC(12,4),
  PRIMARY KEY (ticker, period)
);

CREATE TABLE IF NOT EXISTS public.filings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker        TEXT REFERENCES public.stocks(ticker) ON DELETE CASCADE,
  type          TEXT,                          -- 'annual' | 'quarterly' | 'corporate_action'
  period        TEXT,
  source_url    TEXT,
  raw_pdf_path  TEXT,
  parsed_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.news_items (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker          TEXT REFERENCES public.stocks(ticker) ON DELETE CASCADE,
  source          TEXT,
  url             TEXT,
  headline        TEXT,
  body_excerpt    TEXT,
  published_at    TIMESTAMPTZ,
  sentiment_score NUMERIC(4,3),
  embedding       vector(1536)
);
CREATE INDEX IF NOT EXISTS idx_news_items_ticker_published
  ON public.news_items (ticker, published_at DESC);

-- ============================================================
--  AI / ANALYSIS ARTIFACTS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.stock_scores (
  ticker              TEXT PRIMARY KEY REFERENCES public.stocks(ticker) ON DELETE CASCADE,
  business_quality    NUMERIC(3,2),
  financial_health    NUMERIC(3,2),
  valuation           NUMERIC(3,2),
  catalysts           NUMERIC(3,2),
  composite           NUMERIC(3,2),
  intrinsic_value_pkr NUMERIC(12,4),
  margin_of_safety    NUMERIC(5,4),
  flags               JSONB,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  model_version       TEXT
);

CREATE TABLE IF NOT EXISTS public.ai_summaries (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker        TEXT REFERENCES public.stocks(ticker) ON DELETE CASCADE,
  kind          TEXT,                          -- 'daily_memo' | 'verdict' | 'compare'
  text          TEXT NOT NULL,
  sources       JSONB,
  generated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  llm_model     TEXT
);

CREATE TABLE IF NOT EXISTS public.embeddings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type TEXT NOT NULL,                   -- 'filing' | 'news' | 'glossary'
  source_id   TEXT NOT NULL,
  chunk_text  TEXT NOT NULL,
  embedding   vector(1536)
);
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
  ON public.embeddings USING hnsw (embedding vector_cosine_ops);

-- ============================================================
--  USER PORTFOLIOS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.portfolios (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  type        TEXT NOT NULL CHECK (type IN ('builder','manual','imported')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_portfolios_user ON public.portfolios (user_id);

CREATE TABLE IF NOT EXISTS public.holdings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id  UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
  ticker        TEXT NOT NULL REFERENCES public.stocks(ticker) ON DELETE RESTRICT,
  quantity      NUMERIC(18,4) NOT NULL DEFAULT 0,
  avg_cost_pkr  NUMERIC(12,4),
  target_weight NUMERIC(5,4),
  added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_holdings_portfolio ON public.holdings (portfolio_id);

CREATE TABLE IF NOT EXISTS public.trades (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
  ticker       TEXT NOT NULL REFERENCES public.stocks(ticker),
  action       TEXT NOT NULL CHECK (action IN ('buy','sell')),
  qty          NUMERIC(18,4) NOT NULL,
  price_pkr    NUMERIC(12,4) NOT NULL,
  executed_at  TIMESTAMPTZ NOT NULL,
  source       TEXT
);

-- ============================================================
--  SIP
-- ============================================================

CREATE TABLE IF NOT EXISTS public.sip_plans (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  monthly_amount_pkr NUMERIC(12,2) NOT NULL,
  day_of_month       INT NOT NULL CHECK (day_of_month BETWEEN 1 AND 28),
  active             BOOLEAN NOT NULL DEFAULT TRUE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.sip_proposals (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sip_plan_id  UUID NOT NULL REFERENCES public.sip_plans(id) ON DELETE CASCADE,
  for_month    TEXT NOT NULL,                   -- e.g. '2026-05'
  allocation   JSONB NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  executed     BOOLEAN NOT NULL DEFAULT FALSE
);

-- ============================================================
--  ALERTS & WATCHLIST
-- ============================================================

CREATE TABLE IF NOT EXISTS public.alerts (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  ticker             TEXT REFERENCES public.stocks(ticker),
  type               TEXT,
  payload            JSONB,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  read_at            TIMESTAMPTZ,
  delivered_channels JSONB
);

CREATE TABLE IF NOT EXISTS public.watchlist (
  user_id   UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  ticker    TEXT NOT NULL REFERENCES public.stocks(ticker) ON DELETE CASCADE,
  added_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, ticker)
);

-- ============================================================
--  BILLING
-- ============================================================

CREATE TABLE IF NOT EXISTS public.subscriptions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  plan            TEXT NOT NULL,
  started_at      TIMESTAMPTZ NOT NULL,
  ends_at         TIMESTAMPTZ NOT NULL,
  status          TEXT NOT NULL,
  gateway         TEXT,
  last_invoice_id TEXT
);

CREATE TABLE IF NOT EXISTS public.payments (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  amount_pkr   NUMERIC(12,2) NOT NULL,
  method       TEXT NOT NULL,
  gateway_ref  TEXT,
  receipt_url  TEXT,
  status       TEXT NOT NULL,
  verified_by  UUID REFERENCES public.profiles(id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
--  AUDIT / OPS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor       UUID REFERENCES public.profiles(id),
  action      TEXT NOT NULL,
  entity_type TEXT,
  entity_id   TEXT,
  payload     JSONB,
  at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.scrape_runs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source       TEXT NOT NULL,
  started_at   TIMESTAMPTZ NOT NULL,
  finished_at  TIMESTAMPTZ,
  rows_written INT,
  errors       JSONB
);

-- ============================================================
--  ROW-LEVEL SECURITY
--  Pattern: enable RLS on every table, then add policies.
--    User-owned tables → owner-only ALL.
--    Public reference tables (stocks, prices, etc.) → anyone-read,
--    writes only via service_role (which bypasses RLS by default).
-- ============================================================

-- User-owned tables
ALTER TABLE public.profiles            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investor_profiles   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.holdings            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sip_plans           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sip_proposals       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments            ENABLE ROW LEVEL SECURITY;

-- Public-readable reference tables
ALTER TABLE public.stocks                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prices_daily           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fundamentals_quarterly ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stock_scores           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_summaries           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_items             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.filings                ENABLE ROW LEVEL SECURITY;

-- Internal tables (no anon/authenticated access; service_role only)
ALTER TABLE public.audit_log    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scrape_runs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.embeddings   ENABLE ROW LEVEL SECURITY;

-- ---- Owner policies on user-owned tables ----

CREATE POLICY "profiles_owner_read"    ON public.profiles
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_owner_update"  ON public.profiles
  FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "profiles_owner_insert"  ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "ip_owner_all" ON public.investor_profiles
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "portfolios_owner_all" ON public.portfolios
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "holdings_owner_all" ON public.holdings
  FOR ALL USING (
    EXISTS (SELECT 1 FROM public.portfolios p
            WHERE p.id = holdings.portfolio_id AND p.user_id = auth.uid())
  ) WITH CHECK (
    EXISTS (SELECT 1 FROM public.portfolios p
            WHERE p.id = holdings.portfolio_id AND p.user_id = auth.uid())
  );

CREATE POLICY "trades_owner_all" ON public.trades
  FOR ALL USING (
    EXISTS (SELECT 1 FROM public.portfolios p
            WHERE p.id = trades.portfolio_id AND p.user_id = auth.uid())
  ) WITH CHECK (
    EXISTS (SELECT 1 FROM public.portfolios p
            WHERE p.id = trades.portfolio_id AND p.user_id = auth.uid())
  );

CREATE POLICY "sip_plans_owner_all" ON public.sip_plans
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "sip_proposals_owner_all" ON public.sip_proposals
  FOR ALL USING (
    EXISTS (SELECT 1 FROM public.sip_plans sp
            WHERE sp.id = sip_proposals.sip_plan_id AND sp.user_id = auth.uid())
  ) WITH CHECK (
    EXISTS (SELECT 1 FROM public.sip_plans sp
            WHERE sp.id = sip_proposals.sip_plan_id AND sp.user_id = auth.uid())
  );

CREATE POLICY "alerts_owner_all" ON public.alerts
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "watchlist_owner_all" ON public.watchlist
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "subscriptions_owner_read" ON public.subscriptions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "payments_owner_read" ON public.payments
  FOR SELECT USING (auth.uid() = user_id);

-- ---- Public-read policies on reference tables ----

CREATE POLICY "stocks_public_read"
  ON public.stocks                FOR SELECT USING (TRUE);
CREATE POLICY "prices_daily_public_read"
  ON public.prices_daily          FOR SELECT USING (TRUE);
CREATE POLICY "fundamentals_quarterly_public_read"
  ON public.fundamentals_quarterly FOR SELECT USING (TRUE);
CREATE POLICY "stock_scores_public_read"
  ON public.stock_scores          FOR SELECT USING (TRUE);
CREATE POLICY "ai_summaries_public_read"
  ON public.ai_summaries          FOR SELECT USING (TRUE);
CREATE POLICY "news_items_public_read"
  ON public.news_items            FOR SELECT USING (TRUE);
CREATE POLICY "filings_public_read"
  ON public.filings               FOR SELECT USING (TRUE);

-- audit_log, scrape_runs, embeddings: no policy = no anon/auth access.
-- Only the service_role key bypasses RLS, so backend cron jobs can write.

-- ============================================================
--  TRIGGER: auto-create a public.profiles row on auth signup
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
--  SANITY-CHECK SEED
--  One row in `stocks` so the /api/health endpoint can prove
--  end-to-end DB read works through the anon key.
--  Will be replaced by the real scraper in Phase B3.
-- ============================================================

INSERT INTO public.stocks (ticker, name, sector, sub_sector, is_covered, is_shariah_compliant)
VALUES ('OGDC', 'Oil & Gas Development Co.', 'Oil & Gas Exploration', 'Upstream', TRUE, TRUE)
ON CONFLICT (ticker) DO NOTHING;

-- Done.
