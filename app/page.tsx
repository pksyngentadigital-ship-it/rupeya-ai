// Rupeya.ai — Landing page (B1 port)
// Faithful port of prototype/index.html into Next.js + Tailwind.
// Nav + Footer are provided by the root layout, not rendered here.
// Note: portfolio sizing copy reflects the blueprint update (6–7 stocks,
// up to 9 in qualifying special cases per Section 6.2).

import Container from "@/components/Container";
import Kicker from "@/components/ui/Kicker";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Dot from "@/components/ui/Dot";
import VerdictBadge from "@/components/ui/VerdictBadge";

export default function HomePage() {
  return (
    <>
      {/* HERO */}
      <section className="py-section">
        <Container>
          <div className="text-center">
            <Kicker>Built for Pakistan · Long-term investing</Kicker>
            <h1 className="mt-6">
              Pakistan&apos;s first <span className="text-accent">AI stock analyst</span>
              <br />
              for long-term investors.
            </h1>
            <p className="mx-auto mt-6 max-w-[620px] text-lg text-textMuted">
              Build a disciplined PSX portfolio without learning finance.
              Rupeya.ai reads filings, analyzes fundamentals, and explains
              every decision in plain English — for the price of a cup of chai
              a day.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <Button as="a" href="/stocks" variant="primary" size="lg">
                Explore the Signal List →
              </Button>
              <Button as="a" href="/stocks/ATLH" variant="ghost" size="lg">
                See a sample analysis
              </Button>
            </div>
            <p className="mt-4 text-xs text-textMuted">
              Educational research tool · Not investment advice
            </p>
          </div>
        </Container>
      </section>

      {/* TRUST BAND */}
      <section className="border-y border-border bg-surface">
        <Container>
          <div className="flex flex-wrap items-center justify-around gap-8 py-6">
            <TrustItem>~80 PSX stocks covered</TrustItem>
            <TrustItem>☪ Shariah-compliant filter</TrustItem>
            <TrustItem>Updated daily after market close</TrustItem>
            <TrustItem>Sources every claim — no black-box</TrustItem>
          </div>
        </Container>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="py-section">
        <Container>
          <div className="mb-8 text-center">
            <h2>How it works</h2>
            <p className="mt-2 text-textMuted">Three steps. Under five minutes.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <StepCard n="1" title="Tell us about you">
              Answer 9 quick questions about your goals, horizon, and risk
              comfort. Takes under three minutes.
            </StepCard>
            <StepCard n="2" title="Get your portfolio">
              Our AI builds a focused PSX portfolio of 6–7 stocks (up to 9 in
              special cases) tailored to your profile — with reasoning for
              every pick.
            </StepCard>
            <StepCard n="3" title="Watch it work">
              Daily insights, dividend tracking, and SIP guidance. We tell you
              when to act — and when to sit still.
            </StepCard>
          </div>
        </Container>
      </section>

      {/* WHAT YOU GET */}
      <section className="bg-surface py-section">
        <Container>
          <div className="mb-8 text-center">
            <h2>
              Everything a beginner needs.
              <br />
              Nothing they don&apos;t.
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <FeatureCard emoji="📊" title="AI Portfolio Builder">
              Get a focused 6–7 stock portfolio designed for Pakistani long-term
              investors — with sector caps and a margin-of-safety check.
              Runners-up go to a separate watchlist so nothing good is lost.
            </FeatureCard>
            <FeatureCard emoji="🩺" title="Portfolio Doctor">
              <span>
                Already invested? Paste your holdings and get verdicts:{" "}
                <span className="ml-1 inline-flex flex-wrap gap-1">
                  <VerdictBadge verdict="STRONG BUY" />
                  <VerdictBadge verdict="BUY" />
                  <VerdictBadge verdict="HOLD" />
                  <VerdictBadge verdict="TRIM" />
                  <VerdictBadge verdict="EXIT" />
                </span>
              </span>
            </FeatureCard>
            <FeatureCard emoji="💰" title="Dividend Tracker">
              Project your next 12 months of dividend income. Find sustainable
              yields, avoid dividend traps.
            </FeatureCard>
            <FeatureCard emoji="📈" title="Daily AI Memos">
              Plain-English summaries of new filings, results, and material
              news for stocks you own. No noise.
            </FeatureCard>
            <FeatureCard emoji="🔁" title="SIP Auto-Rebalance">
              Tell us your monthly amount. We&apos;ll tell you exactly which
              stocks to buy each month to keep your portfolio on target.
            </FeatureCard>
            <FeatureCard emoji="💬" title="Ask Rupeya">
              Have a question about a stock, ratio, or sector? Ask in plain
              English — get sourced answers.
            </FeatureCard>
          </div>
        </Container>
      </section>

      {/* FAQ */}
      <section className="bg-surface py-section">
        <Container>
          <div className="mx-auto max-w-[760px]">
            <div className="mb-8 text-center">
              <h2>Common questions</h2>
            </div>
            <div className="flex flex-col gap-3">
              <Card>
                <h4>Is Rupeya.ai a SECP-licensed advisor?</h4>
                <p className="mt-2 text-textMuted">
                  No. Rupeya.ai is an educational research tool. We surface
                  AI-generated analysis of public PSX filings and news. We
                  don&apos;t tell you what to do with your money — we help you
                  think clearly about it.
                </p>
              </Card>
              <Card>
                <h4>Will the AI hallucinate financial numbers?</h4>
                <p className="mt-2 text-textMuted">
                  No. Every number you see (intrinsic value, ROE, score) is
                  computed by deterministic Python code from filings. The AI
                  only translates numbers into plain-English narrative.
                </p>
              </Card>
              <Card>
                <h4>What stocks are covered?</h4>
                <p className="mt-2 text-textMuted">
                  The ~80 most-traded PSX-listed companies at launch, expanding
                  to the full KSE-100 and beyond.
                </p>
              </Card>
              <Card>
                <h4>Do I need a broker account?</h4>
                <p className="mt-2 text-textMuted">
                  Yes — you&apos;ll execute trades through your existing broker.
                  Rupeya.ai is research, not a brokerage. We don&apos;t touch
                  your money.
                </p>
              </Card>
            </div>
          </div>
        </Container>
      </section>
    </>
  );
}

/* ----- Local helpers (kept inline since they're only used by this page) ----- */

function TrustItem({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <Dot tone="good" />
      <span className="text-sm text-textMuted">{children}</span>
    </div>
  );
}

function StepCard({
  n,
  title,
  children,
}: {
  n: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <div className="grid h-9 w-9 place-items-center rounded-full bg-accentSoft font-bold text-accent">
        {n}
      </div>
      <h3 className="mt-4">{title}</h3>
      <p className="mt-2 text-textMuted">{children}</p>
    </Card>
  );
}

function FeatureCard({
  emoji,
  title,
  children,
}: {
  emoji: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <h3>
        <span aria-hidden="true">{emoji}</span> {title}
      </h3>
      <div className="mt-2 text-textMuted">{children}</div>
    </Card>
  );
}

