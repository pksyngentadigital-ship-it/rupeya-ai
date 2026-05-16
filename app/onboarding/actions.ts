// Rupeya.ai — Onboarding server actions
// -----------------------------------------------------------
// saveInvestorProfile maps wizard answers → public.investor_profiles row.
// Uses the cookie-aware Supabase server client so the insert is scoped
// to the signed-in user automatically via RLS.
// -----------------------------------------------------------

"use server";

import { createSupabaseServerClient } from "@/lib/supabase/server";

export interface OnboardingAnswers {
  horizon: string;
  riskReaction: string;
  fundingStyle: string;
  portfolioSize: string;
  monthlyInvestment: string;
  incomeVsGrowth: string;
  experience: string;
  shariahOnly: string;
  goalText: string;
}

export type SaveProfileResult =
  | { ok: true }
  | { ok: false; message: string };

/* -------- Mapping helpers -------- */

const HORIZON_YEARS: Record<string, number> = {
  "lt1": 0.5,
  "1to3": 2,
  "3to5": 4,
  "5to10": 7,
  "gt10": 12,
};

// 0–1 scale (higher = more tolerant)
const RISK_SCORE: Record<string, number> = {
  "sell_all": 0.15,
  "sell_some": 0.4,
  "hold": 0.65,
  "buy_more": 0.9,
};

const PORTFOLIO_SIZE_MIDPOINT: Record<string, number> = {
  "lt50k": 25_000,
  "50k_200k": 125_000,
  "200k_1m": 600_000,
  "1m_5m": 3_000_000,
  "gt5m": 7_500_000,
};

const MONTHLY_MIDPOINT: Record<string, number> = {
  "lt5k": 2_500,
  "5k_25k": 15_000,
  "25k_100k": 60_000,
  "gt100k": 150_000,
};

const INCOME_GROWTH_MAP: Record<string, "income" | "growth" | "balanced"> = {
  "dividend": "income",
  "growth": "growth",
  "both": "balanced",
};

const EXPERIENCE_MAP: Record<string, string> = {
  "none": "novice",
  "1_2y": "1-2y",
  "3plus": "3+y",
};

export async function saveInvestorProfile(
  answers: OnboardingAnswers
): Promise<SaveProfileResult> {
  const supabase = createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { ok: false, message: "You must be signed in to save your profile." };
  }

  // Map "Both" funding style to use both lump sum + SIP; "Lump sum only" zeros SIP.
  const usesLumpSum = answers.fundingStyle !== "sip_only";
  const usesSip = answers.fundingStyle !== "lump_only";

  const profile = {
    user_id: user.id,
    horizon_years: HORIZON_YEARS[answers.horizon] ?? null,
    risk_score: RISK_SCORE[answers.riskReaction] ?? null,
    income_vs_growth: INCOME_GROWTH_MAP[answers.incomeVsGrowth] ?? null,
    monthly_sip_pkr: usesSip
      ? MONTHLY_MIDPOINT[answers.monthlyInvestment] ?? null
      : 0,
    lump_sum_pkr: usesLumpSum
      ? PORTFOLIO_SIZE_MIDPOINT[answers.portfolioSize] ?? null
      : 0,
    experience: EXPERIENCE_MAP[answers.experience] ?? null,
    // "explain_first" defaults to false; user can update later in Settings.
    shariah_only: answers.shariahOnly === "yes",
    goal_text: answers.goalText.trim() || null,
    updated_at: new Date().toISOString(),
  };

  const { error } = await supabase
    .from("investor_profiles")
    .upsert(profile, { onConflict: "user_id" });

  if (error) {
    return { ok: false, message: error.message };
  }

  return { ok: true };
}
