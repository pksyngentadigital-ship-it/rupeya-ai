// Rupeya.ai — Ask Rupeya (/ask)
// Faithful port of prototype/ask-rupeya.html.
// Sidebar (chat history), thread, composer. Mock data only.
// Real Claude Sonnet + tool-calling agent lands in Phase B8.

import Link from "next/link";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Kicker from "@/components/ui/Kicker";
import VerdictBadge from "@/components/ui/VerdictBadge";
import StyleTag from "@/components/ui/StyleTag";
import Button from "@/components/ui/Button";

export const metadata = { title: "Ask Rupeya — AI Research Agent" };

const HISTORY = {
  today: ["Should I invest in PSO right now?", "Compare LUCK vs DGKC"],
  thisWeek: [
    "Best Shariah dividend stocks under PKR 200",
    "Is fertilizer a good sector for 5 years?",
    "Why is HBL flagged in my doctor?",
  ],
  earlier: ["Explain margin of safety", "What is ROE?"],
};

const TRACE = [
  {
    title: "Pulled latest PSO filings & price history",
    tool: 'get_filings(ticker="PSO", years=5) · get_prices(ticker="PSO", range="5y")',
  },
  {
    title: "Verified Shariah-compliance via KMI All-Share membership",
    tool: 'check_shariah_compliance(ticker="PSO") · result: COMPLIANT (debt ratio 24%)',
  },
  {
    title: "Computed RupeyaScore using 4-pillar framework",
    tool: 'score_stock(ticker="PSO") · BQ=3.6 · FH=3.4 · VAL=4.2 · CAT=3.5 · composite=3.7',
  },
  {
    title: "Calculated DCF intrinsic value & margin of safety",
    tool: 'dcf(ticker="PSO", discount_rate=0.13, terminal_growth=0.03) · IV=PKR 312 · MoS=23%',
  },
  {
    title: "Reviewed circular-debt and FX exposure",
    tool: 'flag_macro_risks(ticker="PSO") · circular_debt=HIGH · usd_payables=MEDIUM',
  },
  {
    title: "Synthesized news from last 60 days (12 articles)",
    tool: 'get_news(ticker="PSO", days=60, sources=["BR","Dawn","Profit","Investing.com"])',
  },
];

const SOURCES = [
  "PSO Q3 FY26 filing",
  "PSO Annual Report 2025",
  "PSX KMI All-Share screen May 2026",
  "Mettis Global · OMC sector note",
  "Business Recorder · circular debt update",
  "Investing.com · PSO dividend history",
];

const EXAMPLES = [
  "Should I invest in ENGRO right now?",
  "Compare LUCK vs DGKC",
  "Best Shariah dividend stocks under PKR 200",
  "Is this a good time to buy fertilizers?",
];

export default function AskRupeyaPage() {
  return (
    <div className="grid min-h-[calc(100vh-72px)] lg:grid-cols-[260px_minmax(0,1fr)]">
      {/* Sidebar */}
      <aside className="hidden border-r border-border bg-surface px-4 py-5 lg:block">
        <button className="w-full rounded border border-borderStrong bg-surfaceAlt px-3 py-2.5 text-sm font-medium text-text transition-colors hover:bg-border">
          + New question
        </button>

        <SideSection title="Today" items={HISTORY.today} activeIdx={0} />
        <SideSection title="This week" items={HISTORY.thisWeek} />
        <SideSection title="Earlier" items={HISTORY.earlier} />
      </aside>

      {/* Main */}
      <main className="grid min-w-0 grid-rows-[1fr_auto] overflow-hidden">
        <div className="overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
          <div className="mx-auto max-w-[820px]">
            <Kicker>🤖 Ask Rupeya · AI Research Agent</Kicker>
            <h1 className="mt-4 text-[30px] leading-tight">Your personal PSX analyst</h1>
            <p className="mt-2 text-textMuted">
              Ask anything about a stock, sector, ratio, or your portfolio. Rupeya researches in
              real-time using PSX filings, news, and the 4-pillar fundamental framework. Every
              answer is sourced.
            </p>

            {/* User message */}
            <div className="mt-10 flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-accentSoft px-4 py-3.5 text-text sm:max-w-[540px]">
                Should I invest in Pakistan State Oil (PSO) right now? I want to add an OMC to my
                portfolio but only if the fundamentals are solid and it&apos;s Shariah-compliant.
              </div>
            </div>

            {/* Agent response */}
            <div className="mt-7">
              <div className="mb-3 flex items-center gap-2.5">
                <div className="grid h-8 w-8 place-items-center rounded-md bg-gradient-to-br from-accent to-[#0AA66C] font-extrabold text-[#03110A]">
                  ₨
                </div>
                <div>
                  <div className="font-semibold">Rupeya AI Agent</div>
                  <div className="text-xs text-textMuted">Used 6 tools · 18 seconds</div>
                </div>
              </div>

              {/* Trace */}
              <div className="mb-3.5 rounded-xl border border-border bg-surface px-3 py-3 sm:px-4 sm:py-3.5">
                <div className="mb-2 text-xs uppercase tracking-wider2 text-textMuted">
                  Research trace
                </div>
                {TRACE.map((t, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-[20px_minmax(0,1fr)] items-start gap-2 py-1.5 text-sm sm:grid-cols-[24px_minmax(0,1fr)] sm:gap-2.5"
                  >
                    <span className="text-accent" aria-hidden="true">✓</span>
                    <div className="min-w-0">
                      <div>{t.title}</div>
                      <div className="mt-1 break-all font-mono text-[11px] text-textMuted sm:text-xs">
                        → {t.tool}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Final response */}
              <div className="rounded-xl border border-l-[3px] border-border border-l-accent bg-surface p-4 sm:p-6">
                <div className="mb-4 flex flex-wrap items-center gap-3 rounded-lg bg-accentSoft px-3 py-2.5 sm:px-4 sm:py-3">
                  <VerdictBadge verdict="BUY" className="!px-3 !py-1.5 !text-sm" />
                  <span className="font-semibold">Composite 3.7 / 5 · MoS 23% · Shariah ✓</span>
                  <StyleTag style="dividend" className="!ml-0" />
                </div>

                <p className="leading-loose">
                  <strong>Short answer: Yes — but with eyes open about circular debt.</strong> PSO
                  trades at PKR 240 against an intrinsic value of PKR 312, giving you a 23% margin
                  of safety. It passes the KMI Shariah screen (debt-to-asset ratio 24%, no
                  prohibited business activities). The 4-pillar framework gives it a solid{" "}
                  <strong>3.7</strong> — not the 4.0+ of an Engro or Meezan, but reasonable for the
                  entry point. Style-wise, PSO is a <strong>💰 Dividend stock</strong> — high
                  payout, modest growth, cyclical earnings — which fits your &quot;balanced&quot;
                  preference if paired with growth-oriented holdings.
                </p>
                <p className="mt-3.5 leading-loose">
                  <strong>Why it&apos;s attractive.</strong> P/E of 4.8x against a 5Y average of
                  7.2x is a clear value setup. ROE has averaged 16% over five years even through
                  circular-debt cycles. Forward dividend yield of 9.2% is well-covered by free
                  cash flow at current oil prices.
                </p>
                <p className="mt-3.5 leading-loose">
                  <strong>What you&apos;re accepting.</strong> Circular debt is the structural risk
                  — receivables from IPPs and gas utilities have ballooned to PKR 800 Bn
                  industry-wide. Periodic government settlements unlock cash, but the timing is
                  political. A USD-strong scenario also pressures imported-product margins.
                  Position-size accordingly: I&apos;d cap PSO at{" "}
                  <strong>10–11% of your portfolio</strong>, not more.
                </p>
                <p className="mt-3.5 leading-loose">
                  <strong>The watch flag.</strong> If circular debt resolution is announced in the
                  next IMF program review, expect a 25–35% re-rating. If circular debt expands
                  without resolution by Q4 2026, score drops to 3.2 and verdict moves to{" "}
                  <strong>HOLD</strong>.
                </p>

                <div className="mt-4">
                  <div className="text-xs text-textMuted">Sources:</div>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {SOURCES.map((s) => (
                      <span
                        key={s}
                        className="rounded bg-surfaceAlt px-2 py-1 text-[11px] text-textMuted"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Inline actions */}
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="rounded border border-borderStrong bg-surface px-3 py-1.5 text-xs font-medium text-text hover:bg-surfaceAlt">
                  📌 Pin to dashboard
                </button>
                <Link
                  href="/stocks/PSO"
                  className="rounded border border-borderStrong bg-surface px-3 py-1.5 text-xs font-medium text-text hover:bg-surfaceAlt"
                >
                  📊 Open PSO page
                </Link>
                <Link
                  href="/compare"
                  className="rounded border border-borderStrong bg-surface px-3 py-1.5 text-xs font-medium text-text hover:bg-surfaceAlt"
                >
                  ⚖️ Compare with OGDC
                </Link>
                <button className="rounded border border-borderStrong bg-surface px-3 py-1.5 text-xs font-medium text-text hover:bg-surfaceAlt">
                  🔁 Add to next SIP
                </button>
              </div>
            </div>

            {/* Follow-ups */}
            <Card className="mt-10 !p-[18px]">
              <p className="text-xs uppercase tracking-wider2 text-textMuted">
                Follow-up suggestions
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <ExampleChip>How does PSO compare to OGDC for Shariah investors?</ExampleChip>
                <ExampleChip>What if oil drops to $55?</ExampleChip>
                <ExampleChip>Is now a good time vs waiting for Q4?</ExampleChip>
              </div>
            </Card>
          </div>
        </div>

        {/* Composer */}
        <div className="border-t border-border bg-surface px-4 py-4 sm:px-6">
          <div className="mx-auto max-w-[820px]">
            <div className="mb-3 flex flex-wrap gap-2">
              {EXAMPLES.map((e) => (
                <ExampleChip key={e}>{e}</ExampleChip>
              ))}
            </div>
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 rounded-xl border border-borderStrong bg-background px-3 py-2">
              <input
                type="text"
                placeholder="Ask anything about a PSX stock or your portfolio…"
                className="min-w-0 border-0 bg-transparent px-2 py-2 text-[15px] text-text placeholder:text-textMuted focus:outline-none"
              />
              <Button variant="primary" className="!px-4 !py-2">
                Ask →
              </Button>
            </div>
            <p className="mt-2 text-center text-xs text-textMuted">
              Rupeya researches PSX filings, news, and applies the 4-pillar framework to every
              answer. Educational research tool · Not investment advice.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

function SideSection({
  title,
  items,
  activeIdx,
}: {
  title: string;
  items: string[];
  activeIdx?: number;
}) {
  return (
    <div>
      <div className="my-4 text-[11px] uppercase tracking-widest text-textMuted">{title}</div>
      <div className="grid gap-1">
        {items.map((it, i) => (
          <div
            key={i}
            className={`cursor-pointer rounded-md px-3 py-2.5 text-sm ${
              activeIdx === i ? "bg-accentSoft text-accent" : "text-text hover:bg-surfaceAlt"
            }`}
          >
            {it}
          </div>
        ))}
      </div>
    </div>
  );
}

function ExampleChip({ children }: { children: React.ReactNode }) {
  return (
    <span className="cursor-pointer rounded-full border border-border bg-surfaceAlt px-3 py-2 text-xs hover:border-accent hover:text-accent">
      {children}
    </span>
  );
}
