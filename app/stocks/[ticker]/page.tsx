// Rupeya.ai — Stock detail (/stocks/[ticker])
// -----------------------------------------------------------
// Wired to the deterministic B4 scores in public.stock_scores.
// Everything shown is computed from filings — the page never
// fabricates a number. Sections that depend on the (not-yet-built)
// LLM narration / news layer are shown as honest "coming soon".
// -----------------------------------------------------------

import { type ReactNode } from "react";
import Link from "next/link";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import VerdictBadge from "@/components/ui/VerdictBadge";
import ScoreBar from "@/components/ui/ScoreBar";
import { getScoredStock, type ScoredStock } from "@/lib/scores";

export const dynamic = "force-dynamic";

const STYLE_CHIP: Record<string, string> = {
  dividend: "💰 Dividend",
  growth: "🚀 Growth",
  both: "⚖️ Growth + Dividend",
  cyclical: "🔄 Cyclical",
  speculative: "🎲 Speculative",
};

const PILLAR_DESC = {
  bq: "Earnings durability, industry attractiveness & competitive moat.",
  fh: "Real growth, return on equity, leverage & cash generation.",
  val: "Earnings yield, sector-relative multiples & earnings-power fair value.",
  cat: "Earnings momentum, macro-regime fit & corporate actions.",
};

const RISK_MEANING: Record<string, string> = {
  limited_data: "Limited data — scored on partial financials; signal capped at BUY.",
  no_valuation: "No reliable fair value (losses or missing data); signal capped at HOLD.",
  value_trap: "Possible value trap — statistically cheap but weak fundamentals.",
  high_leverage_de5: "Very high leverage — net debt above 5× equity.",
};

function fmtPct(n: number | null): string {
  if (n === null) return "—";
  const v = Math.round(n * 100);
  return `${v > 0 ? "+" : ""}${v}%`;
}

function buildSummary(s: ScoredStock): string {
  const name = s.name ?? s.ticker;
  const v = s.verdict ?? "a research";
  if (
    s.riskFlags.includes("no_valuation") ||
    s.marginOfSafety === null ||
    s.intrinsicValuePkr === null
  ) {
    return `${name} is rated ${v} on the strength of its business quality and financial health; its earnings aren’t stable enough to anchor a reliable fair value.`;
  }
  const m = Math.round(s.marginOfSafety * 100);
  if (m >= 0) {
    return `${name} is rated ${v} — it trades roughly ${m}% below Rupeya’s earnings-power fair value, a positive margin of safety for a long-term holder.`;
  }
  return `${name} is rated ${v} — it trades roughly ${Math.abs(
    m
  )}% above Rupeya’s earnings-power fair value, so the margin of safety is negative at today’s price.`;
}

export async function generateMetadata({
  params,
}: {
  params: { ticker: string };
}) {
  return { title: `${params.ticker.toUpperCase()} · Rupeya research signal` };
}

export default async function StockPage({
  params,
}: {
  params: { ticker: string };
}) {
  const ticker = params.ticker.toUpperCase();

  let s: ScoredStock | null = null;
  let err: string | null = null;
  try {
    s = await getScoredStock(ticker);
  } catch (e) {
    err = e instanceof Error ? e.message : "load error";
  }

  if (err) {
    return (
      <Shell>
        <Card>
          <p className="text-danger">
            Could not load {ticker}: {err}
          </p>
        </Card>
      </Shell>
    );
  }

  if (!s) {
    return (
      <Shell>
        <Card>
          <h2>We don’t cover {ticker} yet</h2>
          <p className="mt-2 text-textMuted">
            This ticker isn’t in Rupeya’s covered universe. Browse the full signal
            list to see what we rate.
          </p>
          <Link href="/stocks" className="mt-4 inline-block font-semibold text-accent">
            ← Back to the Signal List
          </Link>
        </Card>
      </Shell>
    );
  }

  const iv = s.intrinsicValuePkr;
  const mos = s.marginOfSafety;
  const impliedPrice = iv !== null && mos !== null ? iv * (1 - mos) : null;
  const summary = buildSummary(s);
  const asOf = s.computedAt
    ? new Date(s.computedAt).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : null;

  return (
    <>
      {/* breadcrumb */}
      <section className="border-b border-border bg-surface">
        <Container>
          <p className="py-3 text-xs text-textMuted">
            <Link href="/stocks" className="hover:text-text">
              Signal List
            </Link>{" "}
            › <span className="text-text">{s.ticker}</span>
          </p>
        </Container>
      </section>

      <section className="py-10">
        <Container>
          {/* header */}
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-[32px] leading-tight">{s.ticker}</h1>
                {s.isShariah ? <Chip>☪ Shariah-compliant</Chip> : null}
                {s.sector ? <Chip>{s.sector}</Chip> : null}
                {s.style && STYLE_CHIP[s.style] ? (
                  <Chip variant="accent">{STYLE_CHIP[s.style]}</Chip>
                ) : null}
              </div>
              {s.name ? <p className="mt-2 text-textMuted">{s.name}</p> : null}
            </div>
            {impliedPrice !== null ? (
              <div className="text-right">
                <div className="text-3xl font-bold tracking-tight">
                  PKR {impliedPrice.toFixed(2)}
                </div>
                <div className="text-xs text-textMuted">
                  Price at last scoring{asOf ? ` · ${asOf}` : ""}
                </div>
              </div>
            ) : null}
          </div>

          {/* verdict bar */}
          <Card highlighted className="mt-6 !p-6">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="max-w-[560px]">
                <div className="text-xs text-textMuted">Rupeya Research Signal</div>
                <div className="mt-2 flex items-center gap-3">
                  {s.verdict ? (
                    <VerdictBadge
                      verdict={s.verdict}
                      className="!px-3 !py-1.5 !text-sm"
                    />
                  ) : null}
                  <span className="text-[22px] font-bold">
                    {s.composite?.toFixed(2) ?? "—"}{" "}
                    <span className="text-sm font-normal text-textMuted">/ 5</span>
                  </span>
                </div>
                <p className="mt-3 text-textMuted">{summary}</p>
              </div>
              <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-[230px]">
                {iv !== null ? (
                  <KV label="Earnings-power fair value" value={`PKR ${iv.toFixed(0)}`} />
                ) : (
                  <KV label="Fair value" value="Not reliable" />
                )}
                {mos !== null ? (
                  <KV
                    label="Margin of safety"
                    value={fmtPct(mos)}
                    accent={mos >= 0}
                  />
                ) : null}
                <KV
                  label="Style"
                  value={s.style ? STYLE_CHIP[s.style] ?? s.style : "—"}
                />
                <KV
                  label="Shariah"
                  value={s.isShariah ? "Compliant" : "Not compliant"}
                />
              </div>
            </div>
          </Card>

          {/* risk flags */}
          {s.riskFlags.length ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {s.riskFlags.map((r) => (
                <span
                  key={r}
                  className="rounded-md border border-border bg-trimBg px-3 py-1.5 text-xs text-warn"
                >
                  ⚠ {RISK_MEANING[r] ?? r}
                </span>
              ))}
            </div>
          ) : null}

          {/* pillars */}
          <h3 className="mb-4 mt-10">Score breakdown · 4 pillars</h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <PillarCard
              name="Business Quality"
              weight="30%"
              value={s.businessQuality}
              note={PILLAR_DESC.bq}
            />
            <PillarCard
              name="Financial Health"
              weight="30%"
              value={s.financialHealth}
              note={PILLAR_DESC.fh}
            />
            <PillarCard
              name="Valuation"
              weight="25%"
              value={s.valuation}
              note={PILLAR_DESC.val}
            />
            <PillarCard
              name="Catalysts"
              weight="15%"
              value={s.catalysts}
              note={PILLAR_DESC.cat}
            />
          </div>

          {/* fair value vs price */}
          {iv !== null && impliedPrice !== null ? (
            <Card className="mt-6 !p-7">
              <h3>Fair value vs market price</h3>
              <p className="mt-2 text-sm text-textMuted">
                Gordon earnings-power model: fair P/E = 1 / (cost of equity −
                sustainable growth), anchored to PIB yields plus a 6% equity risk
                premium.
              </p>
              <div className="relative mt-6 h-12 overflow-hidden rounded-lg bg-surfaceAlt">
                <div
                  className="absolute inset-y-0 left-0 rounded-lg bg-gradient-to-r from-accentSoft to-accent"
                  style={{
                    width: `${Math.max(
                      4,
                      Math.min(100, (impliedPrice / iv) * 100)
                    )}%`,
                  }}
                />
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-textMuted">
                <span>PKR 0</span>
                <span className="text-text">Market PKR {impliedPrice.toFixed(0)}</span>
                <span className="text-accent">Fair value PKR {iv.toFixed(0)}</span>
              </div>
            </Card>
          ) : null}

          {/* analysis coming soon */}
          <Card className="mt-6 !p-7">
            <div className="flex items-center justify-between gap-3">
              <h3>Plain-English analysis</h3>
              <Chip>Coming soon</Chip>
            </div>
            <p className="mt-3 text-textMuted">
              Every number on this page is computed deterministically from {s.ticker}’s
              filings — no black box. A written memo that narrates this score in plain
              English is on the way.
            </p>
          </Card>

          {/* footer */}
          <p className="mt-6 max-w-[680px] text-xs leading-relaxed text-textMuted">
            RupeyaScore = 0.30·Business Quality + 0.30·Financial Health +
            0.25·Valuation + 0.15·Catalysts.
            {s.modelVersion ? ` Model ${s.modelVersion}.` : ""}
            {asOf ? ` Computed ${asOf}.` : ""} Educational research signal — not
            investment advice.
          </p>
        </Container>
      </section>
    </>
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <section className="py-12">
      <Container>
        <div className="mx-auto max-w-[640px]">{children}</div>
      </Container>
    </section>
  );
}

function KV({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-xs text-textMuted">{label}</span>
      <span className={`text-sm font-semibold ${accent ? "text-accent" : "text-text"}`}>
        {value}
      </span>
    </div>
  );
}

function PillarCard({
  name,
  weight,
  value,
  note,
}: {
  name: string;
  weight: string;
  value: number | null;
  note: string;
}) {
  return (
    <Card className="!p-[18px]">
      <div className="flex items-center justify-between">
        <div className="text-[13px] uppercase tracking-wider2 text-textMuted">
          {name}
        </div>
        <span className="text-[10px] text-textMuted">{weight}</span>
      </div>
      <div className="mt-2 text-[28px] font-bold">
        {value === null ? "—" : value.toFixed(1)}
        <span className="text-sm font-normal text-textMuted">/5</span>
      </div>
      <div className="mt-4">
        <ScoreBar value={value ?? 0} showValue={false} />
      </div>
      <p className="mt-4 text-xs text-textMuted">{note}</p>
    </Card>
  );
}
