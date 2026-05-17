// Rupeya.ai — Stock detail (/stocks/[ticker])
// Faithful port of prototype/stock.html. Dynamic ticker route.
// Mock data keyed off the route param. Real data lands when scrapers
// + quant engine populate the DB (Phase B3).

import { notFound } from "next/navigation";
import Link from "next/link";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Button from "@/components/ui/Button";
import VerdictBadge, { type Verdict } from "@/components/ui/VerdictBadge";
import StyleTag, { type StockStyle } from "@/components/ui/StyleTag";
import ScoreBar from "@/components/ui/ScoreBar";
import Dot from "@/components/ui/Dot";

interface StockMock {
  ticker: string;
  name: string;
  sector: string;
  marketCap: string;
  listedSince: string;
  price: number;
  priceChange: number;
  priceChangePct: number;
  isShariah: boolean;
  style: StockStyle;
  intrinsicValue: number;
  marginOfSafety: number;
  forwardYield: number;
  fiveYAvgRoe: number;
  verdict: Verdict;
  composite: number;
  description: string;
  pillars: {
    businessQuality: number;
    financialHealth: number;
    valuation: number;
    catalysts: number;
  };
  pillarNotes: {
    businessQuality: string;
    financialHealth: string;
    valuation: string;
    catalysts: string;
  };
  financials: { label: string; value: string }[];
  news: { date: string; headline: string; excerpt: string; source: string }[];
  catalysts: { tone: "good" | "warn" | "bad"; label: string; when: string }[];
}

const MOCK_STOCKS: Record<string, StockMock> = {
  ENGRO: {
    ticker: "ENGRO",
    name: "Engro Corporation Limited",
    sector: "Conglomerate",
    marketCap: "PKR 168 Bn",
    listedSince: "1965",
    price: 295.40,
    priceChange: 2.40,
    priceChangePct: 0.82,
    isShariah: true,
    style: "both",
    intrinsicValue: 387,
    marginOfSafety: 24,
    forwardYield: 8.1,
    fiveYAvgRoe: 19.6,
    verdict: "STRONG BUY",
    composite: 4.2,
    description:
      "High-quality conglomerate trading at a 24% discount to intrinsic value, with durable cash flows and a credible capital-allocation track record.",
    pillars: { businessQuality: 4.1, financialHealth: 4.0, valuation: 4.5, catalysts: 4.0 },
    pillarNotes: {
      businessQuality: "Diversified moat across fertilizer, foods, telecom; durable management.",
      financialHealth: "19.6% 5Y avg ROE, FCF/Net Income 0.94, D/E 0.6 — investment-grade.",
      valuation: "P/E 6.2x vs 5Y avg 8.4x, +24% margin of safety vs DCF.",
      catalysts: "Q1 beat, gas-pricing reform, potential Engro Foods listing.",
    },
    financials: [
      { label: "Revenue 5Y CAGR", value: "14.2%" },
      { label: "EPS 5Y CAGR", value: "12.8%" },
      { label: "ROE (5Y avg)", value: "19.6%" },
      { label: "ROIC (latest)", value: "15.3%" },
      { label: "Debt / Equity", value: "0.6x" },
      { label: "Interest coverage", value: "6.4x" },
      { label: "FCF / Net Income", value: "94%" },
      { label: "P/E (TTM)", value: "6.2x" },
      { label: "P/E (5Y avg)", value: "8.4x" },
      { label: "EV / EBITDA", value: "3.9x" },
      { label: "Dividend yield", value: "8.1%" },
      { label: "Payout ratio", value: "50%" },
    ],
    news: [
      { date: "8 May", headline: "Engro Corp posts 18% YoY rise in Q1 net profit", excerpt: "Driven by stronger fertilizer offtake and stable input costs. Management guides for steady payout.", source: "Business Recorder" },
      { date: "2 May", headline: "PSX filing: Board approves PKR 12 interim dividend", excerpt: "Ex-date 18 May 2026 · payable 5 June 2026 · 8.1% annualized yield at current price.", source: "PSX" },
      { date: "28 Apr", headline: "Sarmaya: Why Engro remains a \"boring brilliance\" Pakistan compounder", excerpt: "Independent analyst notes the holding-company discount has widened to 18%.", source: "Sarmaya" },
    ],
    catalysts: [
      { tone: "good", label: "Q2 FY26 results", when: "Aug 2026" },
      { tone: "good", label: "Engro Foods listing decision", when: "FY26-FY27" },
      { tone: "warn", label: "Gas-pricing reform clarification", when: "Q3 2026" },
      { tone: "good", label: "Annual dividend", when: "Mar 2027" },
    ],
  },
  OGDC: {
    ticker: "OGDC",
    name: "Oil & Gas Development Co.",
    sector: "Oil & Gas Exploration",
    marketCap: "PKR 524 Bn",
    listedSince: "2003",
    price: 132.80,
    priceChange: 1.20,
    priceChangePct: 0.91,
    isShariah: true,
    style: "dividend",
    intrinsicValue: 195,
    marginOfSafety: 32,
    forwardYield: 9.6,
    fiveYAvgRoe: 22.4,
    verdict: "STRONG BUY",
    composite: 4.4,
    description:
      "Deeply undervalued state-owned E&P with 32% margin of safety, double-digit ROE through cycles, and dominant PSX reserves base.",
    pillars: { businessQuality: 4.2, financialHealth: 4.5, valuation: 4.8, catalysts: 3.9 },
    pillarNotes: {
      businessQuality: "PSX's largest E&P by reserves; regulated tariff structure provides moat.",
      financialHealth: "Net cash balance sheet, 22.4% 5Y avg ROE, FCF/NI 91%.",
      valuation: "P/E 3.8x vs 5Y avg 6.2x — extreme value setup.",
      catalysts: "Tight oil discovery upside; circular debt resolution dependent.",
    },
    financials: [
      { label: "Revenue 5Y CAGR", value: "11.8%" },
      { label: "EPS 5Y CAGR", value: "9.4%" },
      { label: "ROE (5Y avg)", value: "22.4%" },
      { label: "Debt / Equity", value: "0.0x" },
      { label: "FCF / Net Income", value: "91%" },
      { label: "P/E (TTM)", value: "3.8x" },
      { label: "Dividend yield", value: "9.6%" },
      { label: "Payout ratio", value: "47%" },
      { label: "EV / EBITDA", value: "2.1x" },
    ],
    news: [
      { date: "10 May", headline: "OGDC reports new gas find in Sindh block", excerpt: "Estimated 30 MMscfd initial production; reserves report due Q3.", source: "Business Recorder" },
      { date: "5 May", headline: "Circular debt receivables cross PKR 800Bn industry-wide", excerpt: "Government working on partial settlement plan; OGDC the largest creditor.", source: "Dawn" },
    ],
    catalysts: [
      { tone: "good", label: "Q4 FY26 results", when: "Aug 2026" },
      { tone: "warn", label: "Circular debt resolution", when: "IMF review" },
      { tone: "good", label: "Annual dividend", when: "Sep 2026" },
    ],
  },
};

export function generateStaticParams() {
  return Object.keys(MOCK_STOCKS).map((ticker) => ({ ticker }));
}

export function generateMetadata({ params }: { params: { ticker: string } }) {
  const s = MOCK_STOCKS[params.ticker.toUpperCase()];
  if (!s) return { title: params.ticker };
  return {
    title: `${s.ticker} · ${s.name}`,
    description: s.description,
  };
}

export default function StockPage({ params }: { params: { ticker: string } }) {
  const ticker = params.ticker.toUpperCase();
  const s = MOCK_STOCKS[ticker];
  if (!s) notFound();

  const priceUp = s.priceChange >= 0;

  return (
    <>
      {/* Breadcrumb */}
      <section className="border-b border-border bg-surface">
        <Container>
          <p className="py-3 text-xs text-textMuted">
            <Link href="/dashboard" className="hover:text-text">Dashboard</Link>{" "}
            ›{" "}
            Stocks{" "}
            ›{" "}
            <span className="text-text">{s.ticker}</span>
          </p>
        </Container>
      </section>

      <section className="py-10">
        <Container>
          {/* Header */}
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-[32px] leading-tight">{s.ticker}</h1>
                {s.isShariah && <Chip>☪ Shariah-compliant</Chip>}
                <Chip>{s.sector}</Chip>
                <Chip variant="accent">
                  {s.style === "both" ? "⚖️ Dividend + Growth" : s.style === "dividend" ? "💰 Dividend" : "🚀 Growth"}
                </Chip>
              </div>
              <p className="mt-2 text-textMuted">
                {s.name} · Listed since {s.listedSince} · Market cap {s.marketCap}
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold tracking-tight">PKR {s.price.toFixed(2)}</div>
              <div className={`text-sm font-semibold ${priceUp ? "text-accent" : "text-danger"}`}>
                {priceUp ? "+" : ""}{s.priceChange.toFixed(2)} ({priceUp ? "+" : ""}{s.priceChangePct}%) today
              </div>
            </div>
          </div>

          {/* Verdict bar */}
          <Card highlighted className="mt-6 !p-6">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <div className="text-xs text-textMuted">Rupeya Research Signal</div>
                <div className="mt-2 flex items-center gap-3">
                  <VerdictBadge verdict={s.verdict} className="!px-3 !py-1.5 !text-sm" />
                  <span className="text-[22px] font-bold">
                    {s.composite} <span className="text-sm font-normal text-textMuted">/ 5</span>
                  </span>
                </div>
                <p className="mt-2 max-w-[520px] text-textMuted">{s.description}</p>
              </div>
              <div className="flex w-full sm:w-auto sm:min-w-[200px] flex-col gap-2">
                <KV label="Intrinsic value" value={`PKR ${s.intrinsicValue}`} />
                <KV label="Margin of safety" value={`+${s.marginOfSafety}%`} accent />
                <KV label="Forward div yield" value={`${s.forwardYield}%`} />
                <KV label="5Y avg ROE" value={`${s.fiveYAvgRoe}%`} />
              </div>
            </div>
          </Card>

          {/* 4 pillars */}
          <h3 className="mb-4 mt-10">Score breakdown · 4 pillars</h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <PillarCard name="Business Quality" value={s.pillars.businessQuality} note={s.pillarNotes.businessQuality} />
            <PillarCard name="Financial Health" value={s.pillars.financialHealth} note={s.pillarNotes.financialHealth} />
            <PillarCard name="Valuation" value={s.pillars.valuation} note={s.pillarNotes.valuation} />
            <PillarCard name="Catalysts" value={s.pillars.catalysts} note={s.pillarNotes.catalysts} />
          </div>

          {/* Intrinsic value bar */}
          <Card className="mt-6 !p-7">
            <h3>Intrinsic value vs market price</h3>
            <p className="mt-2 text-sm text-textMuted">
              Two-stage DCF using KIBOR + 7% equity risk premium · 10-year explicit + terminal.
            </p>
            <div className="relative mt-6 h-14 overflow-hidden rounded-lg bg-surfaceAlt">
              <div
                className="absolute inset-y-0 left-0 rounded-lg bg-gradient-to-r from-accentSoft to-accent"
                style={{ width: `${(s.price / s.intrinsicValue) * 100}%` }}
              />
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-textMuted">
              <span>PKR 0</span>
              <span className="text-text">Market PKR {s.price.toFixed(0)}</span>
              <span className="text-accent">Intrinsic PKR {s.intrinsicValue}</span>
            </div>
            <p className="mt-6 text-sm">
              Sensitivity: at 11% discount rate &amp; 4% terminal growth, fair value is{" "}
              <strong>PKR {s.intrinsicValue}</strong>. Worst-case (13% discount, 2% terminal){" "}
              <strong>PKR {Math.round(s.intrinsicValue * 0.81)}</strong>. Best-case (10% discount, 5% terminal){" "}
              <strong>PKR {Math.round(s.intrinsicValue * 1.18)}</strong>.
            </p>
          </Card>

          {/* AI memo */}
          <Card className="mt-6 !p-7">
            <div className="flex items-center justify-between">
              <h3>🤖 Rupeya&apos;s analysis</h3>
              <Chip>Updated today</Chip>
            </div>
            <p className="mt-4 text-textMuted leading-loose">
              <strong className="text-text">The thesis.</strong> {s.name} is one of a small
              handful of Pakistani companies that has compounded book value at &gt;15% per year
              through multiple political and currency cycles. Multiple uncorrelated cash-flow
              streams, all Shariah-compliant under KMI screens.
            </p>
            <p className="mt-4 text-textMuted leading-loose">
              <strong className="text-text">What&apos;s working.</strong> Latest quarter net income
              +18% YoY on better realizations and stable PKR. Free cash flow tracks net income;
              earnings are real, not accruals. Net debt within long-term tolerance. Dividend
              payout is sustainable with healthy FCF coverage.
            </p>
            <p className="mt-4 text-textMuted leading-loose">
              <strong className="text-text">What to watch.</strong> Regulatory reform timing risk
              + sub-conglomerate discount risk. We&apos;d flip from{" "}
              <strong className="text-accent">STRONG BUY</strong> to <strong>BUY</strong> if the
              price re-rates without commensurate earnings growth.
            </p>
            <p className="mt-4 text-xs text-textMuted">
              Sources: Latest Q filing · Latest Annual Report · Mettis Global · Business Recorder · Investing.com
            </p>
          </Card>

          {/* Key financials */}
          <Card className="mt-6 !p-7">
            <h3>Key financials</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-3">
              {s.financials.map((f) => (
                <div key={f.label} className="rounded bg-surfaceAlt p-3.5">
                  <div className="text-xs text-textMuted">{f.label}</div>
                  <div className="mt-1 text-xl font-bold">{f.value}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* News */}
          <Card className="mt-6 !p-7">
            <h3>Recent news &amp; filings</h3>
            <div className="mt-4 divide-y divide-border">
              {s.news.map((n, i) => (
                <div key={i} className="grid grid-cols-[60px_1fr] gap-3 py-3.5 sm:grid-cols-[70px_1fr_140px]">
                  <span className="text-xs text-textMuted">{n.date}</span>
                  <div>
                    <div className="font-semibold">{n.headline}</div>
                    <p className="mt-1 text-xs text-textMuted">{n.excerpt}</p>
                  </div>
                  <span className="hidden self-start rounded bg-surfaceAlt px-2 py-1 text-center text-[11px] text-textMuted sm:inline-block">
                    {n.source}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Catalysts */}
          <Card className="mt-6 !p-7">
            <h3>Upcoming catalysts</h3>
            <div className="mt-4 grid gap-3">
              {s.catalysts.map((c, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <Dot tone={c.tone} /> {c.label}
                  </span>
                  <span className="text-xs text-textMuted">{c.when}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Action bar */}
          <Card className="mt-6 !p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h4>Take action</h4>
                <p className="mt-1 text-xs text-textMuted">
                  Rupeya never executes trades. You&apos;ll buy/sell through your existing broker.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button as="a" href="/ask" variant="soft">💬 Ask about {s.ticker}</Button>
                <Button variant="ghost">+ Add to watchlist</Button>
                <Button variant="primary">Already own this →</Button>
              </div>
            </div>
          </Card>
        </Container>
      </section>
    </>
  );
}

function KV({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-xs text-textMuted">{label}</span>
      <span className={`font-semibold ${accent ? "text-accent" : ""}`}>{value}</span>
    </div>
  );
}

function PillarCard({ name, value, note }: { name: string; value: number; note: string }) {
  return (
    <Card className="!p-[18px]">
      <div className="text-[13px] uppercase tracking-wider2 text-textMuted">{name}</div>
      <div className="mt-2 text-[28px] font-bold">
        {value.toFixed(1)}
        <span className="text-sm font-normal text-textMuted">/5</span>
      </div>
      <div className="mt-4">
        <ScoreBar value={value} showValue={false} />
      </div>
      <p className="mt-4 text-xs text-textMuted">{note}</p>
    </Card>
  );
}
