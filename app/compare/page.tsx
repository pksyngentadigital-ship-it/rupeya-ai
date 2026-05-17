// Rupeya.ai — Compare (/compare)
// Faithful port of prototype/compare.html.
// Best-metric-per-row highlighting is server-computed via the `winner` flag.

import { Fragment } from "react";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Kicker from "@/components/ui/Kicker";
import Button from "@/components/ui/Button";
import VerdictBadge from "@/components/ui/VerdictBadge";
import StyleTag from "@/components/ui/StyleTag";
import Dot from "@/components/ui/Dot";

export const metadata = { title: "Compare PSX stocks" };

const TICKERS = ["ENGRO", "MEBL", "PSO", "FFC"] as const;

interface Row {
  label: string;
  values: (string | React.ReactNode)[];
  winnerIdx?: number; // index of the winning column
}

const ROWS: { section: string; rows: Row[] }[] = [
  {
    section: "Verdict & Score",
    rows: [
      {
        label: "Research signal",
        values: [
          <VerdictBadge key="1" verdict="STRONG BUY" />,
          <VerdictBadge key="2" verdict="STRONG BUY" />,
          <VerdictBadge key="3" verdict="BUY" />,
          <VerdictBadge key="4" verdict="BUY" />,
        ],
      },
      { label: "RupeyaScore composite", values: ["4.2 / 5", "4.3 / 5", "3.7 / 5", "4.1 / 5"], winnerIdx: 1 },
      {
        label: "Style classification",
        values: [
          <StyleTag key="1" style="both" className="!ml-0" />,
          <StyleTag key="2" style="both" className="!ml-0" />,
          <StyleTag key="3" style="dividend" className="!ml-0" />,
          <StyleTag key="4" style="dividend" className="!ml-0" />,
        ],
      },
      {
        label: "Shariah-compliant?",
        values: ["Yes", "Yes", "Yes", "Yes"].map((v, i) => (
          <span key={i} className="inline-flex items-center gap-1.5">
            <Dot tone="good" /> {v}
          </span>
        )),
      },
      { label: "Pillar · Business Quality", values: ["4.1", "4.4", "3.6", "4.0"], winnerIdx: 1 },
      { label: "Pillar · Financial Health", values: ["4.0", "4.5", "3.4", "4.2"], winnerIdx: 1 },
      { label: "Pillar · Valuation", values: ["4.5", "3.8", "4.6", "4.0"], winnerIdx: 2 },
      { label: "Pillar · Catalysts", values: ["4.0", "4.3", "3.5", "4.1"], winnerIdx: 1 },
    ],
  },
  {
    section: "Valuation",
    rows: [
      { label: "Current price (PKR)", values: ["295.40", "208.10", "240.80", "147.20"] },
      { label: "Intrinsic value (PKR)", values: ["387", "248", "312", "175"], winnerIdx: 2 },
      { label: "Margin of safety", values: ["+24%", "+16%", "+23%", "+16%"], winnerIdx: 2 },
      { label: "P/E (TTM)", values: ["6.2x", "7.4x", "4.8x", "5.6x"], winnerIdx: 2 },
      { label: "P/E vs 5Y avg", values: ["−26%", "−12%", "−33%", "−18%"], winnerIdx: 2 },
      { label: "EV / EBITDA", values: ["3.9x", "n/a (bank)", "3.2x", "4.1x"], winnerIdx: 2 },
    ],
  },
  {
    section: "Quality & Returns",
    rows: [
      { label: "Revenue 5Y CAGR", values: ["14.2%", "22.8%", "11.4%", "9.6%"], winnerIdx: 1 },
      { label: "EPS 5Y CAGR", values: ["12.8%", "28.4%", "10.2%", "8.1%"], winnerIdx: 1 },
      { label: "ROE (5Y avg)", values: ["19.6%", "28.5%", "16.2%", "22.4%"], winnerIdx: 1 },
      { label: "ROIC (latest)", values: ["15.3%", "21.1%", "11.6%", "17.8%"], winnerIdx: 1 },
      { label: "FCF / Net Income", values: ["94%", "n/a (bank)", "71%", "98%"], winnerIdx: 3 },
    ],
  },
  {
    section: "Income",
    rows: [
      { label: "Forward dividend yield", values: ["8.1%", "6.8%", "9.2%", "8.4%"], winnerIdx: 2 },
      { label: "5Y avg payout ratio", values: ["50%", "40%", "62%", "85%"], winnerIdx: 3 },
      { label: "5Y dividend growth", values: ["11.2%", "18.6%", "6.4%", "5.9%"], winnerIdx: 1 },
      { label: "Dividend streak", values: ["10+ yrs", "9 yrs", "10+ yrs", "25+ yrs"], winnerIdx: 3 },
    ],
  },
  {
    section: "Risk",
    rows: [
      { label: "Debt / Equity", values: ["0.6x", "n/a (bank)", "1.4x", "0.7x"], winnerIdx: 0 },
      { label: "Interest coverage", values: ["6.4x", "n/a (bank)", "3.8x", "9.1x"], winnerIdx: 3 },
      { label: "Earnings volatility", values: ["0.18", "0.22", "0.46", "0.21"], winnerIdx: 0 },
      {
        label: "Macro flags",
        values: ["None major", "None major", "⚠️ Circular debt HIGH", "⚠️ Gas-pricing risk"],
        winnerIdx: 1,
      },
    ],
  },
];

const TICKER_META: { ticker: string; name: string; sector: string }[] = [
  { ticker: "ENGRO", name: "Engro Corporation", sector: "Conglomerate" },
  { ticker: "MEBL", name: "Meezan Bank", sector: "Islamic Banking" },
  { ticker: "PSO", name: "Pakistan State Oil", sector: "OMC" },
  { ticker: "FFC", name: "Fauji Fertilizer", sector: "Fertilizer" },
];

export default function ComparePage() {
  return (
    <section className="py-section">
      <Container>
        <Kicker>⚖️ Compare</Kicker>
        <h1 className="mt-4 text-[36px] leading-tight">Compare PSX stocks side-by-side</h1>
        <p className="mt-2 max-w-[640px] text-textMuted">
          Stack 2–4 stocks against each other on the same 4-pillar framework. See exactly where
          one beats another, on which metric, and why. Best metric in each row is highlighted in
          green.
        </p>

        {/* Picker */}
        <div className="mt-6 flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface p-3">
          <span className="mr-2 text-xs uppercase tracking-wider2 text-textMuted">Comparing</span>
          {TICKERS.map((t) => (
            <span
              key={t}
              className="inline-flex items-center gap-2 rounded-full border border-accent bg-accentSoft px-3 py-1.5 text-sm font-semibold text-accent"
            >
              {t}
              <button className="opacity-70 hover:opacity-100" aria-label={`Remove ${t}`}>
                ×
              </button>
            </span>
          ))}
          <button className="rounded-full border border-dashed border-borderStrong bg-surfaceAlt px-3.5 py-1.5 text-sm text-textMuted hover:border-accent hover:text-accent">
            + Add stock
          </button>
          <div className="flex w-full flex-wrap gap-2 sm:ml-auto sm:w-auto">
            <Chip>☪ Shariah-only</Chip>
            <Chip>⚖️ All styles</Chip>
          </div>
        </div>

        {/* Comparison table — scrolls horizontally on narrow screens */}
        <div className="mt-6 max-w-full overflow-x-auto rounded-lg border border-border bg-surface">
          <table className="w-full min-w-[720px] border-collapse text-sm">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 w-[140px] border-b border-border bg-background p-2.5 text-left sm:w-[200px] sm:p-3.5"></th>
                {TICKER_META.map((t) => (
                  <th
                    key={t.ticker}
                    className="border-b border-border bg-background p-2.5 text-left align-top sm:p-3.5"
                  >
                    <div className="text-base font-bold text-text sm:text-lg">{t.ticker}</div>
                    <div className="mt-1 text-[11px] font-normal leading-tight text-textMuted sm:text-xs">
                      {t.name}
                      <br className="sm:hidden" />
                      <span className="hidden sm:inline"> · </span>
                      {t.sector}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map(({ section, rows }) => (
                <Fragment key={section}>
                  <tr>
                    <td
                      colSpan={5}
                      className="border-b border-border bg-background p-2.5 text-[11px] font-semibold uppercase tracking-widest text-accent sm:p-3.5"
                    >
                      {section}
                    </td>
                  </tr>
                  {rows.map((r) => (
                    <tr key={r.label} className="hover:bg-accent/[0.04]">
                      <td className="sticky left-0 z-10 w-[140px] border-b border-border bg-surfaceAlt p-2.5 text-xs text-textMuted sm:w-[200px] sm:p-3.5 sm:text-sm">
                        {r.label}
                      </td>
                      {r.values.map((v, i) => (
                        <td
                          key={i}
                          className={`border-b border-border p-2.5 align-top sm:p-3.5 ${
                            r.winnerIdx === i
                              ? "bg-accentSoft text-accent after:content-['_✓'] after:font-bold"
                              : ""
                          }`}
                        >
                          {v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-center text-xs text-textMuted sm:hidden">
          ← Swipe the table sideways to see all stocks →
        </p>

        {/* AI synthesis */}
        <Card className="mt-10 !p-5 sm:!p-7">
          <div className="flex flex-wrap items-center gap-3">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-accent to-[#0AA66C] font-extrabold text-[#03110A]">
              ₨
            </span>
            <h3>Rupeya&apos;s take</h3>
            <Chip>AI synthesis · 4 stocks</Chip>
          </div>

          <div className="mt-4 rounded-lg border-l-[3px] border-accent bg-surfaceAlt p-5">
            <p className="leading-loose">
              <strong className="text-text">If you can only pick one: ENGRO.</strong> It scores 4.2
              across the board with no major weakness, has the second-largest margin of safety
              (+24%), and pays a healthy 8.1% yield while still growing earnings at double-digit
              rates. It&apos;s the textbook ⚖️ Both — a long-duration compounder that also writes
              cheques to shareholders. Best fit for a &quot;balanced&quot; investor profile.
            </p>
          </div>

          <p className="mt-4 leading-loose">
            <strong className="text-text">If you want maximum quality and growth: MEBL.</strong>{" "}
            Meezan Bank wins 5 of the 10 quality &amp; growth metrics — highest ROE (28.5%),
            highest EPS growth (28.4%), best dividend growth (18.6%). It is structurally
            privileged in Pakistan&apos;s Islamic banking shift. The trade-off: smallest margin of
            safety (+16%) of the four.
          </p>
          <p className="mt-4 leading-loose">
            <strong className="text-text">If you want pure income with some risk: PSO.</strong>{" "}
            Highest yield (9.2%), cheapest valuation (P/E 4.8x), and the largest discount to its
            own 5-year average. The catch: circular debt exposure is HIGH and earnings volatility
            (0.46) is materially worse than peers. A 10–11% position cap is appropriate.
          </p>
          <p className="mt-4 leading-loose">
            <strong className="text-text">If you want a sleep-well dividend: FFC.</strong> 25+ year
            dividend streak, 85% payout, FCF coverage of 98%, lowest earnings volatility of the
            income-focused names. EPS growth is the slowest of the four (8.1%) — you&apos;re
            trading growth for predictability. A natural fit for retirees.
          </p>

          <hr className="my-6 border-border" />

          <p className="text-xs text-textMuted">
            <strong>Methodology:</strong> Composite RupeyaScore is a weighted average of Business
            Quality (30%), Financial Health (30%), Valuation (25%), Catalysts (15%). Intrinsic
            value via two-stage DCF with KIBOR + 7% equity risk premium. Shariah status from KMI
            All-Share Index.
          </p>
        </Card>

        {/* Actions */}
        <div className="mt-10 flex flex-wrap gap-3">
          <Button variant="primary">+ Add winner to my portfolio</Button>
          <Button as="a" href="/ask" variant="soft">
            💬 Ask Rupeya about this comparison
          </Button>
          <Button variant="ghost">📄 Download PDF report</Button>
          <Button variant="ghost">🔗 Share comparison</Button>
        </div>
      </Container>
    </section>
  );
}
