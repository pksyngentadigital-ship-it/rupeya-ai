// Rupeya.ai — Data access for the deterministic stock scores (B4 engine output).
// -----------------------------------------------------------
// Reads public.stock_scores joined to public.stocks. Both tables are
// public-read (RLS allows anonymous SELECT), so the screener and stock
// pages need no auth. The `flags` JSONB carries verdict / style /
// is_shariah_compliant / risk_flags, written by the scoring engine.
// -----------------------------------------------------------

import { createSupabaseServerClient } from "@/lib/supabase/server";

export type Verdict = "STRONG BUY" | "BUY" | "HOLD" | "TRIM" | "EXIT";

export interface ScoredStock {
  ticker: string;
  name: string | null;
  sector: string | null;
  isShariah: boolean | null;
  businessQuality: number | null;
  financialHealth: number | null;
  valuation: number | null;
  catalysts: number | null;
  composite: number | null;
  intrinsicValuePkr: number | null;
  marginOfSafety: number | null; // fraction: 0.41 => +41% undervalued
  verdict: Verdict | null;
  style: string | null;
  riskFlags: string[];
  modelVersion: string | null;
  computedAt: string | null;
}

export const VERDICTS: Verdict[] = ["STRONG BUY", "BUY", "HOLD", "TRIM", "EXIT"];

export const VERDICT_RANK: Record<Verdict, number> = {
  "STRONG BUY": 0,
  BUY: 1,
  HOLD: 2,
  TRIM: 3,
  EXIT: 4,
};

const SELECT =
  "ticker, business_quality, financial_health, valuation, catalysts, composite, intrinsic_value_pkr, margin_of_safety, flags, model_version, computed_at, stocks(name, sector, is_shariah_compliant)";

function toNum(v: unknown): number | null {
  if (v === null || v === undefined) return null;
  const n = typeof v === "number" ? v : parseFloat(String(v));
  return Number.isFinite(n) ? n : null;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function mapRow(r: any): ScoredStock {
  const flags = (r?.flags ?? {}) as Record<string, unknown>;
  const stock = (Array.isArray(r?.stocks) ? r.stocks[0] : r?.stocks) ?? {};
  return {
    ticker: r.ticker,
    name: stock.name ?? null,
    sector: stock.sector ?? null,
    isShariah:
      (flags.is_shariah_compliant as boolean | undefined) ??
      (stock.is_shariah_compliant as boolean | undefined) ??
      null,
    businessQuality: toNum(r.business_quality),
    financialHealth: toNum(r.financial_health),
    valuation: toNum(r.valuation),
    catalysts: toNum(r.catalysts),
    composite: toNum(r.composite),
    intrinsicValuePkr: toNum(r.intrinsic_value_pkr),
    marginOfSafety: toNum(r.margin_of_safety),
    verdict: (flags.verdict as Verdict) ?? null,
    style: (flags.style as string) ?? null,
    riskFlags: Array.isArray(flags.risk_flags) ? (flags.risk_flags as string[]) : [],
    modelVersion: r.model_version ?? null,
    computedAt: r.computed_at ?? null,
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

/** Full scored universe, ranked by composite RupeyaScore (desc). */
export async function getScoredUniverse(): Promise<ScoredStock[]> {
  const supabase = createSupabaseServerClient();
  const { data, error } = await supabase.from("stock_scores").select(SELECT);
  if (error) throw new Error(`getScoredUniverse: ${error.message}`);
  const rows = (data ?? []).map(mapRow);
  rows.sort((a, b) => {
    const c = (b.composite ?? -1) - (a.composite ?? -1);
    return c !== 0 ? c : a.ticker.localeCompare(b.ticker);
  });
  return rows;
}

/** One scored stock by ticker, or null if not covered. */
export async function getScoredStock(ticker: string): Promise<ScoredStock | null> {
  const supabase = createSupabaseServerClient();
  const { data, error } = await supabase
    .from("stock_scores")
    .select(SELECT)
    .eq("ticker", ticker.toUpperCase())
    .maybeSingle();
  if (error) throw new Error(`getScoredStock: ${error.message}`);
  return data ? mapRow(data) : null;
}

/** Covered tickers, for generateStaticParams. */
export async function getCoveredTickers(): Promise<string[]> {
  const supabase = createSupabaseServerClient();
  const { data, error } = await supabase.from("stock_scores").select("ticker");
  if (error) throw new Error(`getCoveredTickers: ${error.message}`);
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
  return (data ?? []).map((r: any) => r.ticker as string);
}
