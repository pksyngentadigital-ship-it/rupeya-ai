// Rupeya.ai — Dashboard (B1 port)
// -----------------------------------------------------------
// Faithful port of prototype/dashboard.html. Layout:
//   • Greeting strip (market status, chips)
//   • Portfolio Health card (ring + summary + key stats)
//   • Today's Insights (3 cards)
//   • Two-column: Holdings table | Right rail (SIP, Ask Rupeya, Alerts)
// All data is mocked for B1. Real wiring lands when the portfolio
// engine ships (Phase B3+).
// -----------------------------------------------------------

import { redirect } from "next/navigation";
import Link from "next/link";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import VerdictBadge, { type Verdict } from "@/components/ui/VerdictBadge";
import StyleTag, { type StockStyle } from "@/components/ui/StyleTag";
import Dot from "@/components/ui/Dot";
import Button from "@/components/ui/Button";
import { getCurrentUser } from "@/lib/supabase/server";

export const metadata = { title: "Dashboard" };

interface Holding {
  ticker: string;
  name: string;
  style: StockStyle;
  weight: number; // %
  price: number;
  dayChangePct: number;
  totalReturnPct: number;
  verdict: Verdict;
}

const MOCK_HOLDINGS: Holding[] = [
  { ticker: "ENGRO", name: "Engro Corp", style: "both", weight: 14, price: 295.40, dayChangePct: 0.8, totalReturnPct: 22, verdict: "STRONG BUY" },
  { ticker: "MEBL", name: "Meezan Bank", style: "both", weight: 13, price: 208.10, dayChangePct: 1.4, totalReturnPct: 31, verdict: "STRONG BUY" },
  { ticker: "FFC", name: "Fauji Fertilizer", style: "dividend", weight: 13, price: 147.20, dayChangePct: -0.3, totalReturnPct: 15, verdict: "BUY" },
  { ticker: "LUCK", name: "Lucky Cement", style: "both", weight: 13, price: 682.50, dayChangePct: 2.1, totalReturnPct: 19, verdict: "BUY" },
  { ticker: "PSO", name: "Pakistan State Oil", style: "dividend", weight: 12, price: 240.80, dayChangePct: 0.5, totalReturnPct: 8, verdict: "BUY" },
  { ticker: "HUBC", name: "Hub Power", style: "dividend", weight: 12, price: 158.30, dayChangePct: 0.2, totalReturnPct: 25, verdict: "TRIM" },
  { ticker: "SYS", name: "Systems Limited", style: "growth", weight: 12, price: 1082, dayChangePct: 1.8, totalReturnPct: 34, verdict: "BUY" },
];

export default async function DashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/sign-in");

  const firstName = friendlyName(user.email ?? "investor");
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <>
      {/* GREETING STRIP */}
      <section className="border-b border-border bg-surface">
        <Container>
          <div className="flex flex-wrap items-center justify-between gap-3 py-4">
            <div>
              <h3 className="text-lg font-semibold">
                {greeting}, {firstName} 👋
              </h3>
              <p className="mt-1 text-xs text-textMuted">
                Markets closed · KSE-100 <span className="text-accent">+1.2%</span> · Last update 4:15 PM PKT
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Chip>☪ Shariah-compliant</Chip>
              <Chip>Balanced profile</Chip>
            </div>
          </div>
        </Container>
      </section>

      <section className="py-10">
        <Container>
          {/* PORTFOLIO HEALTH (full width, highlighted) */}
          <Card highlighted className="!p-7">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="flex flex-wrap items-center gap-6">
                <HealthRing score={78} max={100} />
                <div>
                  <div className="text-xs text-textMuted">Portfolio Health</div>
                  <h2 className="mt-1">Healthy &amp; on track</h2>
                  <p className="mt-2 max-w-[520px] text-textMuted">
                    Your {MOCK_HOLDINGS.length}-stock portfolio is well-diversified with a strong margin of safety.
                    One holding (Hub Power) is approaching trim territory; the rest remain in BUY or HOLD.
                  </p>
                </div>
              </div>
              <div className="flex w-full sm:w-auto sm:min-w-[200px] flex-col gap-2">
                <KeyValue label="Total value" value="PKR 1,18,420" />
                <KeyValue label="Total return" value="+18.4%" tone="accent" />
                <KeyValue label="Forward div yield" value="7.4%" />
                <KeyValue label="Risk score" value="5.2 / 10" />
              </div>
            </div>
          </Card>

          {/* TODAY'S INSIGHTS */}
          <h3 className="mb-4 mt-10">Today&apos;s insights</h3>
          <div className="grid gap-6 md:grid-cols-3">
            <InsightCard
              tone="accent"
              icon="💰"
              title="Dividend incoming"
              body={
                <>
                  FFC declared PKR 5.0/share interim dividend. Payable to your 80 shares:{" "}
                  <strong className="text-text">PKR 400</strong>, ex-date 22 May.
                </>
              }
              link={{ href: "/stocks/FFC", label: "View FFC →" }}
            />
            <InsightCard
              tone="info"
              icon="📊"
              title="Score change · MEBL"
              body="Meezan Bank's RupeyaScore moved from 4.1 → 4.3 after Q1 results. Strong deposits growth and expanded ROE."
              link={{ href: "/stocks/MEBL", label: "Read memo →" }}
            />
            <InsightCard
              tone="warn"
              icon="⚠️"
              title="Watch · HUBC"
              body="Price approaching intrinsic value. If it crosses PKR 165, Rupeya will suggest trimming half the position."
              link={{ href: "/stocks/HUBC", label: "View thresholds →" }}
            />
          </div>

          {/* TWO COLUMN: HOLDINGS + RIGHT RAIL */}
          <div className="mt-10 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
            {/* HOLDINGS */}
            <Card>
              <div className="flex items-center justify-between">
                <h3>Your holdings</h3>
                <Link href="/portfolio/doctor" className="text-xs text-textMuted hover:text-text">
                  Run Portfolio Doctor →
                </Link>
              </div>

              {/* Desktop column header */}
              <div className="mt-4 hidden grid-cols-[80px_1fr_90px_90px_120px] gap-2.5 border-b border-borderStrong pb-2 text-xs uppercase tracking-wider2 text-textMuted sm:grid">
                <span>Ticker</span>
                <span>Name</span>
                <span>Price</span>
                <span>P/L</span>
                <span>Verdict</span>
              </div>
              {/* Mobile column header */}
              <div className="mt-4 grid grid-cols-[70px_1fr_90px] gap-2.5 border-b border-borderStrong pb-2 text-xs uppercase tracking-wider2 text-textMuted sm:hidden">
                <span>Ticker</span>
                <span>Name</span>
                <span>Price</span>
              </div>

              <div>
                {MOCK_HOLDINGS.map((h) => (
                  <HoldingRow key={h.ticker} h={h} />
                ))}
              </div>
            </Card>

            {/* RIGHT RAIL */}
            <div className="flex flex-col gap-4">
              <SipCard />
              <AskRupeyaCard />
              <AlertsCard />
            </div>
          </div>
        </Container>
      </section>
    </>
  );
}

/* -------- Sub-components -------- */

function HealthRing({ score, max }: { score: number; max: number }) {
  const r = 60;
  const circumference = 2 * Math.PI * r; // ≈ 377
  const offset = circumference - (score / max) * circumference;

  return (
    <div className="relative h-[140px] w-[140px] shrink-0">
      <svg width="140" height="140" viewBox="0 0 140 140" className="-rotate-90">
        <circle cx="70" cy="70" r={r} stroke="#1F2A3A" strokeWidth="12" fill="none" />
        <circle
          cx="70"
          cy="70"
          r={r}
          stroke="#16C784"
          strokeWidth="12"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="text-4xl font-bold leading-none tracking-tight">{score}</div>
          <div className="text-xs text-textMuted">/ {max}</div>
        </div>
      </div>
    </div>
  );
}

function KeyValue({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "accent" | "danger";
}) {
  const valueClass = tone === "accent" ? "text-accent" : tone === "danger" ? "text-danger" : "";
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-xs text-textMuted">{label}</span>
      <span className={`font-semibold ${valueClass}`}>{value}</span>
    </div>
  );
}

function InsightCard({
  tone,
  icon,
  title,
  body,
  link,
}: {
  tone: "accent" | "info" | "warn";
  icon: string;
  title: string;
  body: React.ReactNode;
  link: { href: string; label: string };
}) {
  const iconBg =
    tone === "accent"
      ? "bg-accentSoft text-accent"
      : tone === "info"
        ? "bg-holdBg text-info"
        : "bg-trimBg text-warn";

  return (
    <Card className="!p-[18px]">
      <div className={`grid h-9 w-9 place-items-center rounded text-base ${iconBg}`} aria-hidden="true">
        {icon}
      </div>
      <h4 className="mt-4">{title}</h4>
      <p className="mt-2 text-sm text-textMuted">{body}</p>
      <Link href={link.href} className="mt-4 inline-block text-xs text-textMuted hover:text-text">
        {link.label}
      </Link>
    </Card>
  );
}

function HoldingRow({ h }: { h: Holding }) {
  const dayPosNeg = h.dayChangePct >= 0 ? "text-accent" : "text-danger";
  const totalPosNeg = h.totalReturnPct >= 0 ? "text-accent" : "text-danger";

  return (
    <Link
      href={`/stocks/${h.ticker}`}
      className="block border-b border-border last:border-b-0 transition-colors hover:bg-surfaceAlt"
    >
      {/* Desktop layout */}
      <div className="hidden grid-cols-[80px_1fr_90px_90px_120px] items-center gap-2.5 py-3.5 text-sm sm:grid">
        <span className="font-bold">{h.ticker}</span>
        <div>
          <div>
            {h.name} <StyleTag style={h.style} />
          </div>
          <div className="text-xs text-textMuted">{h.weight}% weight</div>
        </div>
        <div>
          <div>{formatPrice(h.price)}</div>
          <div className={`text-xs ${dayPosNeg}`}>
            {h.dayChangePct >= 0 ? "+" : ""}
            {h.dayChangePct.toFixed(1)}%
          </div>
        </div>
        <span className={totalPosNeg}>
          {h.totalReturnPct >= 0 ? "+" : ""}
          {h.totalReturnPct}%
        </span>
        <span>
          <VerdictBadge verdict={h.verdict} />
        </span>
      </div>

      {/* Mobile layout */}
      <div className="grid grid-cols-[60px_minmax(0,1fr)_80px] items-center gap-2 py-3.5 text-sm sm:hidden">
        <span className="font-bold">{h.ticker}</span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-y-0.5">
            <span className="truncate">{h.name}</span>
            <StyleTag style={h.style} />
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-textMuted">{h.weight}%</span>
            <VerdictBadge verdict={h.verdict} className="!px-1.5 !py-0.5 !text-[10px]" />
          </div>
        </div>
        <div className="text-right">
          <div>{formatPrice(h.price)}</div>
          <div className={`text-xs ${dayPosNeg}`}>
            {h.dayChangePct >= 0 ? "+" : ""}
            {h.dayChangePct.toFixed(1)}%
          </div>
        </div>
      </div>
    </Link>
  );
}

function SipCard() {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <h4>Your SIP this month</h4>
        <Chip variant="accent">15 May</Chip>
      </div>
      <p className="mt-2 text-sm text-textMuted">PKR 15,000 · Rupeya recommends:</p>
      <div className="mt-4 grid gap-2">
        <SipRow ticker="EFERT" amount="5,500" note="underweight" />
        <SipRow ticker="FFC" amount="5,500" note="underweight" />
        <SipRow ticker="SYS" amount="4,000" note="underweight" />
      </div>
      <Button variant="primary" className="mt-4 w-full">
        Mark as bought
      </Button>
      <p className="mt-3 text-xs text-textMuted">Execute via your broker, then mark complete.</p>
    </Card>
  );
}

function SipRow({ ticker, amount, note }: { ticker: string; amount: string; note: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span>
        + PKR {amount} to <strong>{ticker}</strong>
      </span>
      <span className="text-xs text-textMuted">{note}</span>
    </div>
  );
}

function AskRupeyaCard() {
  return (
    <Card>
      <h4>💬 Ask Rupeya</h4>
      <p className="mt-2 text-sm text-textMuted">
        Got a question? Your AI analyst is on call.
      </p>
      <input
        type="text"
        placeholder="e.g., Should I add OGDC to my portfolio?"
        className="mt-4 w-full rounded border border-borderStrong bg-surface px-4 py-3 text-sm text-text placeholder:text-textMuted focus:border-accent focus:outline-none"
      />
      <Button as="a" href="/ask" variant="soft" className="mt-3 w-full">
        Open Ask Rupeya →
      </Button>
    </Card>
  );
}

function AlertsCard() {
  return (
    <Card>
      <h4>🔔 Recent alerts</h4>
      <div className="mt-4 grid gap-3 text-sm">
        <AlertRow tone="good" ticker="MEBL" text="Q1 results filed" when="2h ago" />
        <AlertRow tone="warn" ticker="HUBC" text="approaching trim threshold" when="1d ago" />
        <AlertRow tone="good" ticker="FFC" text="dividend declared" when="2d ago" />
        <AlertRow tone="good" ticker="OGDC" text="better-than-MoS opportunity" when="3d ago" />
      </div>
      <Link href="#" className="mt-4 inline-block text-xs text-textMuted hover:text-text">
        View all alerts →
      </Link>
    </Card>
  );
}

function AlertRow({
  tone,
  ticker,
  text,
  when,
}: {
  tone: "good" | "warn" | "bad";
  ticker: string;
  text: string;
  when: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <Dot tone={tone} />
      <strong>{ticker}</strong>
      <span>{text}</span>
      <span className="ml-auto text-xs text-textMuted">{when}</span>
    </div>
  );
}

/* -------- Helpers -------- */

function formatPrice(n: number): string {
  if (n >= 1000) {
    return new Intl.NumberFormat("en-PK", { maximumFractionDigits: 0 }).format(n);
  }
  return n.toFixed(2);
}

function friendlyName(email: string): string {
  // "khalid.ahmed@gmail.com" → "Khalid"
  const localPart = email.split("@")[0];
  const first = localPart.split(/[.\-_]/)[0];
  if (!first) return "there";
  return first.charAt(0).toUpperCase() + first.slice(1);
}
