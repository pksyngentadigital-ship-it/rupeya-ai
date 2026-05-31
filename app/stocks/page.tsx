// Rupeya.ai — Research Signal List (public screener)
// -----------------------------------------------------------
// Server component. Reads the deterministic B4 scores from
// public.stock_scores (public-read) and ranks the whole covered
// universe by RupeyaScore. No auth required. Filters (Shariah,
// verdict) are URL-driven so the page stays a pure server render
// and every filtered view is shareable.
// -----------------------------------------------------------

import { type ReactNode } from "react";
import Link from "next/link";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import VerdictBadge from "@/components/ui/VerdictBadge";
import {
  getScoredUniverse,
  VERDICTS,
  type ScoredStock,
  type Verdict,
} from "@/lib/scores";

export const metadata = {
  title: "Research Signal List — Rupeya.ai",
  description:
    "Every PSX stock Rupeya covers, scored 0-5 across four pillars (Business Quality, Financial Health, Valuation, Catalysts) and ranked by RupeyaScore.",
};

// Always render fresh from stock_scores (updated after each scoring run).
export const dynamic = "force-dynamic";

const STYLE_LABEL: Record<string, string> = {
  dividend: "Dividend",
  growth: "Growth",
  both: "Growth + Dividend",
  cyclical: "Cyclical",
  speculative: "Speculative",
};

function fmtPct(n: number | null): string {
  if (n === null) return "—";
  const v = Math.round(n * 100);
  return `${v > 0 ? "+" : ""}${v}%`;
}

function mosTone(n: number | null): string {
  if (n === null) return "text-textMuted";
  if (n >= 0.25) return "text-accent";
  if (n >= 0) return "text-info";
  if (n >= -0.25) return "text-warn";
  return "text-danger";
}

function pillars(s: ScoredStock): string {
  const f = (x: number | null) => (x === null ? "—" : x.toFixed(1));
  return `${f(s.businessQuality)} · ${f(s.financialHealth)} · ${f(s.valuation)} · ${f(s.catalysts)}`;
}

interface SP {
  shariah?: string;
  verdict?: string;
  sector?: string;
}

function buildHref(base: SP, patch: Partial<SP>): string {
  const merged: Record<string, string> = {};
  for (const [k, v] of Object.entries({ ...base, ...patch })) {
    if (v) merged[k] = v as string;
  }
  const qs = new URLSearchParams(merged).toString();
  return qs ? `/stocks?${qs}` : "/stocks";
}

export default async function StocksScreenerPage({
  searchParams,
}: {
  searchParams?: SP;
}) {
  const sp: SP = searchParams ?? {};

  let universe: ScoredStock[] = [];
  let loadError: string | null = null;
  try {
    universe = await getScoredUniverse();
  } catch (e) {
    loadError = e instanceof Error ? e.message : "Failed to load scores";
  }

  const fShariah = sp.shariah === "1";
  const fVerdict = (sp.verdict as Verdict) || "";
  const fSector = sp.sector || "";

  let rows = universe;
  if (fShariah) rows = rows.filter((s) => s.isShariah);
  if (fVerdict) rows = rows.filter((s) => s.verdict === fVerdict);
  if (fSector) rows = rows.filter((s) => s.sector === fSector);

  const counts: Record<string, number> = {};
  for (const s of universe) {
    if (s.verdict) counts[s.verdict] = (counts[s.verdict] ?? 0) + 1;
  }

  const asOf = universe[0]?.computedAt
    ? new Date(universe[0].computedAt).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;
  const model = universe[0]?.modelVersion ?? null;

  return (
    <>
      {/* HEADER */}
      <section className="border-b border-border bg-surface">
        <Container>
          <div className="py-8">
            <p className="text-xs font-semibold uppercase tracking-wider2 text-accent">
              Research Signal List
            </p>
            <h1 className="mt-2">The Rupeya Signal List</h1>
            <p className="mt-3 max-w-[640px] text-textMuted">
              Every PSX stock we cover, scored 0–5 across four pillars and ranked by
              RupeyaScore. Verdicts are computed deterministically from company filings —
              not by a black box.{asOf ? ` Updated ${asOf}.` : ""}
            </p>
            <p className="mt-2 text-xs text-textMuted">
              Educational research signal · Not investment advice
              {model ? ` · model ${model}` : ""}
            </p>
          </div>
        </Container>
      </section>

      <section className="py-8">
        <Container>
          {loadError ? (
            <Card>
              <p className="text-danger">Could not load scores: {loadError}</p>
            </Card>
          ) : (
            <>
              {/* FILTERS */}
              <div className="mb-5 flex flex-wrap items-center gap-2">
                <FilterChip
                  href={buildHref(sp, { shariah: fShariah ? "" : "1" })}
                  active={fShariah}
                >
                  ☪ Shariah only
                </FilterChip>
                <span className="mx-1 hidden h-5 w-px bg-border sm:inline-block" />
                <FilterChip href={buildHref(sp, { verdict: "" })} active={!fVerdict}>
                  All verdicts
                </FilterChip>
                {VERDICTS.map((v) => (
                  <FilterChip
                    key={v}
                    href={buildHref(sp, { verdict: fVerdict === v ? "" : v })}
                    active={fVerdict === v}
                  >
                    {v}
                    {counts[v] ? ` (${counts[v]})` : ""}
                  </FilterChip>
                ))}
              </div>

              <p className="mb-3 text-sm text-textMuted">
                Showing <span className="text-text">{rows.length}</span> of{" "}
                {universe.length} covered stocks
                {fSector ? ` · ${fSector}` : ""}
                {fShariah ? " · Shariah-compliant" : ""}
              </p>

              {/* TABLE */}
              <Card className="!p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-[11px] uppercase tracking-wide text-textMuted">
                        <th className="px-4 py-3 font-medium">#</th>
                        <th className="px-4 py-3 font-medium">Stock</th>
                        <th className="hidden px-4 py-3 font-medium md:table-cell">
                          Sector
                        </th>
                        <th className="px-4 py-3 font-medium">Signal</th>
                        <th className="px-4 py-3 text-right font-medium">RupeyaScore</th>
                        <th className="hidden px-4 py-3 text-center font-medium lg:table-cell">
                          BQ · FH · VAL · CAT
                        </th>
                        <th className="px-4 py-3 text-right font-medium">
                          Margin of Safety
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((s, i) => (
                        <tr
                          key={s.ticker}
                          className="border-b border-border last:border-0 hover:bg-surfaceAlt"
                        >
                          <td className="px-4 py-3 tabular-nums text-textMuted">
                            {i + 1}
                          </td>
                          <td className="px-4 py-3">
                            <Link
                              href={`/stocks/${s.ticker}`}
                              className="font-semibold text-text hover:text-accent"
                            >
                              {s.ticker}
                            </Link>
                            {s.isShariah ? (
                              <span
                                className="ml-1.5 text-accent"
                                title="Shariah-compliant"
                              >
                                ☪
                              </span>
                            ) : null}
                            <div className="mt-0.5 text-xs text-textMuted">
                              <span>{s.name ?? ""}</span>
                              {s.style && STYLE_LABEL[s.style] ? (
                                <span> · {STYLE_LABEL[s.style]}</span>
                              ) : null}
                            </div>
                          </td>
                          <td className="hidden px-4 py-3 text-textMuted md:table-cell">
                            {s.sector ?? "—"}
                          </td>
                          <td className="px-4 py-3">
                            {s.verdict ? <VerdictBadge verdict={s.verdict} /> : "—"}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="text-base font-bold tabular-nums text-text">
                              {s.composite?.toFixed(2) ?? "—"}
                            </span>
                            <span className="text-xs text-textMuted">/5</span>
                          </td>
                          <td className="hidden px-4 py-3 text-center text-xs tabular-nums text-textMuted lg:table-cell">
                            {pillars(s)}
                          </td>
                          <td
                            className={`px-4 py-3 text-right font-semibold tabular-nums ${mosTone(
                              s.marginOfSafety
                            )}`}
                          >
                            {fmtPct(s.marginOfSafety)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>

              {rows.length === 0 ? (
                <p className="mt-6 text-center text-textMuted">
                  No stocks match these filters.
                </p>
              ) : null}

              {/* methodology */}
              <div className="mt-6 max-w-[680px] text-xs leading-relaxed text-textMuted">
                <p>
                  RupeyaScore = 0.30·Business Quality + 0.30·Financial Health +
                  0.25·Valuation + 0.15·Catalysts. Margin of safety compares an
                  earnings-power fair value to the current price (positive = trading below
                  fair value). Thinly-covered names are conviction-weighted toward neutral,
                  so partial data can never overstate a signal.
                </p>
              </div>
            </>
          )}
        </Container>
      </section>
    </>
  );
}

function FilterChip({
  href,
  active,
  children,
}: {
  href: string;
  active?: boolean;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition ${
        active
          ? "border-accent bg-accentSoft text-accent"
          : "border-border bg-surface text-textMuted hover:text-text"
      }`}
    >
      {children}
    </Link>
  );
}
