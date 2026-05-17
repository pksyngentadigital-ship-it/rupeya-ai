// Rupeya.ai — Portfolio Doctor (/portfolio/doctor)
// Faithful port of prototype/portfolio-doctor.html.
// Real holdings-input parsing + analysis lands in Phase B4.

import { redirect } from "next/navigation";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Kicker from "@/components/ui/Kicker";
import Button from "@/components/ui/Button";
import VerdictBadge, { type Verdict } from "@/components/ui/VerdictBadge";
import StyleTag, { type StockStyle } from "@/components/ui/StyleTag";
import { getCurrentUser } from "@/lib/supabase/server";

export const metadata = { title: "Portfolio Doctor" };

interface UserHolding {
  ticker: string;
  qty: string;
  avgCost: string;
}

const SAMPLE_INPUTS: UserHolding[] = [
  { ticker: "OGDC", qty: "200", avgCost: "115.50" },
  { ticker: "HBL", qty: "150", avgCost: "98.20" },
  { ticker: "DGKC", qty: "80", avgCost: "135.40" },
  { ticker: "MARI", qty: "60", avgCost: "2,180" },
  { ticker: "HUMNL", qty: "500", avgCost: "9.40" },
];

interface DiagRow {
  ticker: string;
  style: StockStyle;
  reasoning: string;
  score: number;
  verdict: Verdict;
}

const SAMPLE_VERDICTS: DiagRow[] = [
  { ticker: "OGDC", style: "dividend", reasoning: "Deep value, 32% margin of safety, strong FCF.", score: 4.4, verdict: "STRONG BUY" },
  { ticker: "MARI", style: "both", reasoning: "Best ROIC in E&P; expensive but quality justifies premium.", score: 4.0, verdict: "BUY" },
  { ticker: "HBL", style: "dividend", reasoning: "Decent fundamentals but fails Shariah screen given your profile.", score: 3.6, verdict: "TRIM" },
  { ticker: "DGKC", style: "growth", reasoning: "At fair value, leverage rising, weaker than Lucky Cement.", score: 3.0, verdict: "HOLD" },
  { ticker: "HUMNL", style: "growth", reasoning: "Going-concern flag, declining ad revenue, balance-sheet strain.", score: 1.6, verdict: "EXIT" },
];

export default async function PortfolioDoctorPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/sign-in");

  return (
    <section className="py-section">
      <Container>
        <Kicker>🩺 Portfolio Doctor</Kicker>
        <h1 className="mt-4 text-[36px] leading-tight">
          Get a second opinion on your PSX portfolio
        </h1>
        <p className="mt-2 max-w-[640px] text-textMuted">
          Paste your existing holdings — even ones you bought before joining Rupeya. Our AI runs
          every position through the 4-pillar framework and gives you a clear verdict, plus a
          ranked action plan. No tips. No hype. Just analysis.
        </p>

        {/* Holdings input */}
        <Card className="mt-8 !p-7">
          <h3>Your holdings</h3>
          <p className="mt-2 text-sm text-textMuted">
            Add each stock with quantity and average cost. Or paste a CSV in the box below.
          </p>

          <div className="mt-6 grid gap-2.5">
            <div className="grid grid-cols-[90px_1fr_1fr_30px] gap-2 text-xs uppercase tracking-wider2 text-textMuted">
              <span>Ticker</span>
              <span>Quantity</span>
              <span>Avg cost (PKR)</span>
              <span></span>
            </div>
            {SAMPLE_INPUTS.map((h, i) => (
              <div key={i} className="grid grid-cols-[90px_1fr_1fr_30px] items-center gap-2">
                <input defaultValue={h.ticker} className={inputClass} />
                <input defaultValue={h.qty} className={inputClass} />
                <input defaultValue={h.avgCost} className={inputClass} />
                <button type="button" className="text-textMuted hover:text-danger" aria-label="Remove">
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button variant="ghost">+ Add another</Button>
            <Button variant="soft">📋 Paste CSV instead</Button>
            <Button variant="primary" className="ml-auto">
              Run diagnosis →
            </Button>
          </div>
        </Card>

        {/* Divider */}
        <div className="my-12 flex items-center gap-4">
          <hr className="flex-1 border-t border-border" />
          <Chip>Sample diagnosis below</Chip>
          <hr className="flex-1 border-t border-border" />
        </div>

        {/* Health summary */}
        <Card highlighted className="!p-7">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <div className="text-xs text-textMuted">
                Diagnosis · {SAMPLE_VERDICTS.length} holdings analyzed
              </div>
              <h2 className="mt-2">
                Portfolio Health: <span className="text-warn">62 / 100</span>
              </h2>
              <p className="mt-2 max-w-[540px] text-textMuted">
                Mixed quality. Two strong holdings, one over-concentrated bet, and two positions
                that should be exited. Following the action plan below could improve the score
                to ~82 within 30 days.
              </p>
            </div>
            <div className="flex w-full sm:w-auto sm:min-w-[200px] flex-col gap-2">
              <KV label="Total invested" value="PKR 2,06,800" />
              <KV label="Current value" value="PKR 2,18,200" />
              <KV label="Diversification" value="Weak" tone="warn" />
              <KV label="Shariah-compliance" value="3 of 5" />
            </div>
          </div>
        </Card>

        {/* Strengths & Weaknesses */}
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <Card>
            <h3>✅ What&apos;s working</h3>
            <ul className="mt-4 grid gap-3 text-[14.5px] leading-relaxed">
              <FindingItem tone="good">
                <strong>OGDC</strong> is a high-quality, deeply undervalued energy holding with
                32% margin of safety. Keep it.
              </FindingItem>
              <FindingItem tone="good">
                <strong>MARI Petroleum</strong> has a durable moat and best-in-class ROIC for PSX
                energy.
              </FindingItem>
              <FindingItem tone="good">
                Forward dividend yield at <strong>8.4%</strong> is attractive given a 10Y PIB of
                ~12%.
              </FindingItem>
            </ul>
          </Card>
          <Card>
            <h3>⚠️ What needs attention</h3>
            <ul className="mt-4 grid gap-3 text-[14.5px] leading-relaxed">
              <FindingItem tone="warn">
                <strong>62%</strong> of your portfolio sits in just two sectors (energy &amp;
                banking). One adverse policy change could whipsaw 60% of your wealth.
              </FindingItem>
              <FindingItem tone="bad">
                <strong>HUMNL</strong> (Hum Network) flagged for going-concern uncertainty in its
                latest audit. <strong>Exit</strong> recommended.
              </FindingItem>
              <FindingItem tone="warn">
                <strong>HBL</strong> is a conventional bank — fails Shariah screen. If your
                profile is Shariah-only, swap into <strong>MEBL</strong>.
              </FindingItem>
              <FindingItem tone="warn">
                <strong>DGKC</strong> is at fair value with stretched leverage (D/E 1.4x).
                Consider <strong>trim</strong>.
              </FindingItem>
            </ul>
          </Card>
        </div>

        {/* Verdicts table */}
        <Card className="mt-6 !p-7">
          <h3>Per-stock verdicts</h3>
          <div className="mt-4 hidden grid-cols-[80px_1fr_80px_120px] gap-2.5 border-b border-borderStrong pb-2 text-xs uppercase tracking-wider2 text-textMuted sm:grid">
            <span>Ticker</span>
            <span>Reasoning</span>
            <span>Score</span>
            <span>Verdict</span>
          </div>
          <div>
            {SAMPLE_VERDICTS.map((v) => (
              <div
                key={v.ticker}
                className="grid grid-cols-1 gap-2 border-b border-border py-3 last:border-b-0 sm:grid-cols-[80px_1fr_80px_120px] sm:items-center sm:gap-2.5"
              >
                <div className="text-sm">
                  <span className="font-bold">{v.ticker}</span>
                  <StyleTag style={v.style} />
                </div>
                <div className="text-sm text-textMuted">{v.reasoning}</div>
                <div className="text-sm">{v.score}</div>
                <div>
                  <VerdictBadge verdict={v.verdict} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Action plan */}
        <Card highlighted className="mt-6 !p-7">
          <h3>📋 Your action plan</h3>
          <p className="mt-2 text-textMuted">Five ranked moves. Do them in order.</p>

          <div className="mt-6 grid gap-5">
            <ActionStep
              n="1"
              title="Exit HUMNL position"
              body="Sell all 500 shares (~PKR 4,700). Going-concern audit qualification + 3 years of declining ad revenue. Redeploy proceeds in step 4."
            />
            <ActionStep
              n="2"
              title="Swap HBL → MEBL"
              body="Sell 150 HBL shares (~PKR 14,730), buy ~70 MEBL shares. Maintains banking exposure but moves you to Shariah-compliant Meezan Bank, which has a higher RupeyaScore (4.3 vs 3.6) and better ROE."
            />
            <ActionStep
              n="3"
              title="Trim DGKC by 50%"
              body="Sell 40 of 80 shares (~PKR 5,400). DGKC sits at fair value with rising leverage. Half-position keeps cement exposure without overstaying."
            />
            <ActionStep
              n="4"
              title="Add ENGRO and FFC"
              body="Use proceeds from steps 1 + 3 (~PKR 10,100) to add Engro and FFC. Both are Shariah-compliant, in BUY territory, and improve sector diversification (currently overweight energy)."
            />
            <ActionStep
              n="5"
              title="Add Nestle & Systems Limited (next month's SIP)"
              body="Defensive food + USD-revenue tech are missing entirely. Allocate next month's SIP (PKR 15,000) split equally to NESTLE and SYS."
            />
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button variant="primary">Apply to my portfolio</Button>
            <Button variant="ghost">Download PDF report</Button>
            <Button as="a" href="/ask" variant="soft">
              💬 Ask about any move
            </Button>
          </div>
        </Card>
      </Container>
    </section>
  );
}

const inputClass =
  "w-full rounded border border-borderStrong bg-surface px-3 py-2.5 text-sm text-text placeholder:text-textMuted focus:border-accent focus:outline-none";

function KV({ label, value, tone }: { label: string; value: string; tone?: "warn" | "accent" }) {
  const cls = tone === "warn" ? "text-warn" : tone === "accent" ? "text-accent" : "";
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-xs text-textMuted">{label}</span>
      <span className={`font-semibold ${cls}`}>{value}</span>
    </div>
  );
}

function FindingItem({
  tone,
  children,
}: {
  tone: "good" | "warn" | "bad";
  children: React.ReactNode;
}) {
  const dot = tone === "good" ? "text-accent" : tone === "warn" ? "text-warn" : "text-danger";
  return (
    <li className="flex items-start gap-3">
      <span className={dot} aria-hidden="true">●</span>
      <span>{children}</span>
    </li>
  );
}

function ActionStep({ n, title, body }: { n: string; title: string; body: string }) {
  return (
    <div className="flex items-start gap-3.5">
      <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accentSoft text-sm font-bold text-accent">
        {n}
      </span>
      <div>
        <h4>{title}</h4>
        <p className="mt-2 text-sm text-textMuted">{body}</p>
      </div>
    </div>
  );
}
