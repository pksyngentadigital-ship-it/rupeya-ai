// Rupeya.ai — Portfolio Builder result (/portfolio/build)
// -----------------------------------------------------------
// Faithful port of prototype/portfolio-builder.html.
// Sizing reflects the blueprint update: 7 default holdings with a
// Runners-up Watchlist showing 2 close-but-excluded candidates.
// Real algorithm lands in Phase B3 (quant engine + builder).
// -----------------------------------------------------------

import { redirect } from "next/navigation";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Button from "@/components/ui/Button";
import VerdictBadge, { type Verdict } from "@/components/ui/VerdictBadge";
import StyleTag, { type StockStyle } from "@/components/ui/StyleTag";
import { getCurrentUser } from "@/lib/supabase/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import Link from "next/link";

export const metadata = { title: "Your Rupeya portfolio" };

interface BuilderStock {
  ticker: string;
  name: string;
  sector: string;
  style: StockStyle;
  weight: number;
  score: number;
  verdict: Verdict;
}

interface SectorSlice {
  name: string;
  pct: number;
  color: string;
}

const MOCK_HOLDINGS: BuilderStock[] = [
  { ticker: "ENGRO", name: "Engro Corporation", sector: "Conglomerate · Fertilizer", style: "both", weight: 16, score: 4.2, verdict: "STRONG BUY" },
  { ticker: "MEBL", name: "Meezan Bank", sector: "Islamic Banking", style: "both", weight: 16, score: 4.3, verdict: "STRONG BUY" },
  { ticker: "FFC", name: "Fauji Fertilizer", sector: "Fertilizer", style: "dividend", weight: 14, score: 4.1, verdict: "BUY" },
  { ticker: "LUCK", name: "Lucky Cement", sector: "Cement", style: "both", weight: 14, score: 3.9, verdict: "BUY" },
  { ticker: "PSO", name: "Pakistan State Oil", sector: "Oil & Gas Marketing", style: "dividend", weight: 13, score: 3.8, verdict: "BUY" },
  { ticker: "HUBC", name: "Hub Power", sector: "Power", style: "dividend", weight: 13, score: 3.7, verdict: "BUY" },
  { ticker: "SYS", name: "Systems Limited", sector: "Tech", style: "growth", weight: 14, score: 3.9, verdict: "BUY" },
];

const RUNNERS_UP: { stock: BuilderStock; reason: string }[] = [
  {
    stock: { ticker: "NESTLE", name: "Nestle Pakistan", sector: "Food", style: "growth", weight: 0, score: 4.3, verdict: "BUY" },
    reason: "High-quality compounder, but Food sector cap (15%) is already filled by other proxies; revisit if portfolio expands to 8 holdings.",
  },
  {
    stock: { ticker: "EFERT", name: "Engro Fertilizers", sector: "Fertilizer", style: "dividend", weight: 0, score: 4.0, verdict: "BUY" },
    reason: "Excellent dividend stock, but Fertilizer sector is already represented by FFC + parent ENGRO — adding would breach 30% sector cap.",
  },
];

const SECTOR_MIX: SectorSlice[] = [
  { name: "Fertilizer", pct: 30, color: "#0AA66C" },
  { name: "Islamic Banking", pct: 16, color: "#4F8DF7" },
  { name: "Conglomerate", pct: 16, color: "#16C784" },
  { name: "Cement", pct: 14, color: "#F0B72F" },
  { name: "Tech", pct: 14, color: "#A66BFF" },
  { name: "Oil & Gas Marketing", pct: 13, color: "#EA3943" },
  { name: "Power", pct: 13, color: "#2A3850" },
];

export default async function PortfolioBuildPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/sign-in");

  const supabase = createSupabaseServerClient();
  const { data: profile } = await supabase
    .from("investor_profiles")
    .select("shariah_only, horizon_years, lump_sum_pkr, monthly_sip_pkr")
    .eq("user_id", user.id)
    .maybeSingle();

  const isShariah = profile?.shariah_only ?? true;
  const horizonText = profile?.horizon_years
    ? `${profile.horizon_years} year${profile.horizon_years === 1 ? "" : "s"}`
    : "5–10 years";
  const lump = profile?.lump_sum_pkr ?? 100_000;
  const sip = profile?.monthly_sip_pkr ?? 15_000;

  return (
    <section className="py-section">
      <Container>
        {/* Header */}
        <div className="flex flex-wrap gap-2">
          <Chip variant="accent">✓ Built for your profile</Chip>
          {isShariah && <Chip variant="accent">☪ Shariah-compliant only</Chip>}
        </div>
        <h1 className="mt-4 text-[40px] leading-tight sm:text-[44px]">
          Your Rupeya portfolio
        </h1>
        <p className="mt-2 max-w-[640px] text-textMuted">
          A focused {MOCK_HOLDINGS.length}-stock long-term portfolio for a {horizonText} horizon, PKR{" "}
          {lump.toLocaleString("en-PK")} starter and PKR {sip.toLocaleString("en-PK")} monthly SIP
          {isShariah && ", drawn from the KMI All-Share Shariah-compliant universe"} and screened
          for a 25%+ margin of safety.
        </p>

        {/* Key stats */}
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Holdings" value={`${MOCK_HOLDINGS.length} stocks`} note={`Across ${SECTOR_MIX.length} sectors`} />
          <StatCard label="Expected dividend yield" value="7.4%" note="Forward 12-month estimate" accent />
          <StatCard label="Avg margin of safety" value="28%" note="Discount to intrinsic value" />
          <StatCard
            label="Avg Rupeya Score"
            value={
              <>
                4.0 <span className="text-sm text-textMuted">/ 5</span>
              </>
            }
            note="Composite quality + value"
          />
        </div>

        {/* Sector allocation */}
        <Card className="mt-6 !p-7">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3>Sector allocation</h3>
              <p className="mt-1 text-sm text-textMuted">
                Diversified across {SECTOR_MIX.length} PSX sectors. No single sector exceeds 30%.
              </p>
            </div>
            <Chip>Risk profile · Balanced</Chip>
          </div>
          <div className="mt-6 flex flex-wrap items-center gap-10">
            <SectorPie slices={SECTOR_MIX} />
            <div className="grid gap-2">
              {SECTOR_MIX.map((s) => (
                <div key={s.name} className="flex items-center gap-2.5 text-sm">
                  <span className="h-3 w-3 rounded-sm" style={{ background: s.color }} aria-hidden="true" />
                  {s.name} · {s.pct}%
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Holdings */}
        <Card className="mt-6 !p-7">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3>Your holdings · {MOCK_HOLDINGS.length} stocks</h3>
            <span className="text-xs text-textMuted">
              Click any row to see Rupeya&apos;s full analysis →
            </span>
          </div>

          {/* Desktop header */}
          <div className="mt-4 hidden grid-cols-[80px_1fr_140px_70px_120px] gap-3 border-b border-borderStrong pb-2 text-xs uppercase tracking-wider2 text-textMuted sm:grid">
            <span>Ticker</span>
            <span>Name · Sector</span>
            <span>Weight</span>
            <span>Score</span>
            <span>Verdict</span>
          </div>

          <div>
            {MOCK_HOLDINGS.map((s) => (
              <HoldingRow key={s.ticker} stock={s} />
            ))}
          </div>
        </Card>

        {/* Runners-up watchlist */}
        <Card className="mt-6 !p-7">
          <div className="flex flex-wrap items-center gap-3">
            <h3>Runners-up watchlist</h3>
            <Chip>Watchlist</Chip>
          </div>
          <p className="mt-2 text-sm text-textMuted">
            Stocks that scored well but didn&apos;t make the portfolio. Here&apos;s why each was
            excluded. We&apos;ll alert you if any becomes a better fit than your current holdings.
          </p>
          <div className="mt-4 grid gap-3">
            {RUNNERS_UP.map(({ stock, reason }) => (
              <div
                key={stock.ticker}
                className="grid grid-cols-[80px_1fr] gap-3 rounded border border-border bg-surfaceAlt p-4"
              >
                <div>
                  <div className="font-bold">{stock.ticker}</div>
                  <div className="mt-1 text-xs text-textMuted">Score {stock.score}</div>
                </div>
                <div>
                  <div>
                    {stock.name} <StyleTag style={stock.style} />
                  </div>
                  <p className="mt-1 text-sm text-textMuted">{reason}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* AI narrative */}
        <Card className="mt-6 !p-7">
          <h3>Why these stocks · AI summary</h3>
          <p className="mt-4 text-textMuted leading-loose">
            Your portfolio is built around three ideas.{" "}
            <strong className="text-text">First,</strong> long-duration Pakistani compounders —
            Engro, Meezan, Lucky, FFC — that have generated double-digit ROE for over a decade and
            return cash through dividends rather than re-leveraging.{" "}
            <strong className="text-text">Second,</strong> a deliberate tilt toward sectors that
            benefit from inflation (cement, fertilizer, OMCs) which historically outperform in
            PKR-weak environments. <strong className="text-text">Third,</strong> a small position
            in Systems Limited as a USD-revenue hedge — Pakistan tech exporters earn dollars and
            pay rupees, a structural advantage for the next decade. We deliberately avoided
            high-leverage cyclicals and any name with audit qualifications in the latest annual
            report.
          </p>
          <p className="mt-4 text-xs text-textMuted">
            Sources: PSX filings · Latest quarterly results · Mettis Global · Business Recorder · Investing.com
          </p>
        </Card>

        {/* Actions */}
        <div className="mt-10 flex flex-wrap justify-center gap-3">
          <Button as="a" href="/dashboard" variant="primary" size="lg">
            Save &amp; open dashboard →
          </Button>
          <Button as="a" href="/onboarding" variant="ghost" size="lg">
            Tweak my profile
          </Button>
        </div>
      </Container>
    </section>
  );
}

function StatCard({
  label,
  value,
  note,
  accent = false,
}: {
  label: string;
  value: React.ReactNode;
  note: string;
  accent?: boolean;
}) {
  return (
    <Card className="!p-[18px]">
      <div className="text-xs text-textMuted">{label}</div>
      <div
        className={`mt-2 text-[26px] font-bold tracking-tight ${accent ? "text-accent" : ""}`}
      >
        {value}
      </div>
      <div className="mt-2 text-xs text-textMuted">{note}</div>
    </Card>
  );
}

function HoldingRow({ stock }: { stock: BuilderStock }) {
  return (
    <Link
      href={`/stocks/${stock.ticker}`}
      className="block border-b border-border last:border-b-0 transition-colors hover:bg-surfaceAlt"
    >
      {/* Desktop */}
      <div className="hidden grid-cols-[80px_1fr_140px_70px_120px] items-center gap-3 py-3.5 text-sm sm:grid">
        <span className="font-bold">{stock.ticker}</span>
        <div>
          <div>
            {stock.name} <StyleTag style={stock.style} />
          </div>
          <div className="text-xs text-textMuted">{stock.sector}</div>
        </div>
        <div>
          <div>{stock.weight}%</div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surfaceAlt">
            <div className="h-full bg-accent" style={{ width: `${stock.weight * 4}%` }} />
          </div>
        </div>
        <span>{stock.score}</span>
        <span>
          <VerdictBadge verdict={stock.verdict} />
        </span>
      </div>
      {/* Mobile */}
      <div className="grid grid-cols-[60px_minmax(0,1fr)_50px] items-center gap-2 py-3.5 text-sm sm:hidden">
        <span className="font-bold">{stock.ticker}</span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-y-0.5">
            <span className="truncate">{stock.name}</span>
            <StyleTag style={stock.style} />
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-textMuted">
            <span>{stock.weight}%</span>
            <VerdictBadge verdict={stock.verdict} className="!px-1.5 !py-0.5 !text-[10px]" />
          </div>
        </div>
        <div className="text-right text-sm">{stock.score}</div>
      </div>
    </Link>
  );
}

function SectorPie({ slices }: { slices: SectorSlice[] }) {
  // Simple SVG conic-style pie using stacked circle strokes with stroke-dasharray.
  // Circumference of r=16 ≈ 100, so dasharray values equal percentages directly.
  let offset = 0;
  return (
    <svg
      viewBox="0 0 32 32"
      className="h-[180px] w-[180px] shrink-0 sm:h-[220px] sm:w-[220px]"
      aria-label="Sector allocation chart"
    >
      <circle r="16" cx="16" cy="16" fill={slices[0]?.color ?? "#16C784"} />
      {slices.slice(1).map((s, i) => {
        offset -= slices[i].pct;
        return (
          <circle
            key={s.name}
            r="16"
            cx="16"
            cy="16"
            fill="transparent"
            stroke={s.color}
            strokeWidth="32"
            strokeDasharray={`${s.pct} 100`}
            strokeDashoffset={offset}
            transform="rotate(-90 16 16)"
          />
        );
      })}
      <circle r="8" cx="16" cy="16" fill="#0B0F14" />
    </svg>
  );
}
