// Rupeya.ai — Landing page (MVP scaffold v0.1)
// Implements blueprint Section 7.1: hero, 3-step explainer, pricing, disclaimer.
// No backend wired yet — buttons go nowhere on purpose.

export default function HomePage() {
  return (
    <main className="min-h-screen">
      {/* Top nav */}
      <nav className="border-b border-border">
        <div className="mx-auto flex max-w-page items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-md bg-accent" aria-hidden />
            <span className="text-lg font-semibold tracking-tight">
              Rupeya<span className="text-accent">.ai</span>
            </span>
          </div>
          <div className="flex items-center gap-3 text-sm text-textMuted">
            <span className="hidden sm:inline">Pre-launch</span>
            <button className="rounded-md border border-border px-3 py-1.5 text-text hover:bg-surface">
              Sign in
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-page px-6 pt-20 pb-16 text-center">
        <span className="inline-block rounded-full border border-border bg-surface px-3 py-1 text-xs uppercase tracking-wider text-textMuted">
          Built for Pakistan · Long-term investing
        </span>
        <h1 className="mt-6 text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
          Pakistan&apos;s first <span className="text-accent">AI stock analyst</span>
          <br />
          for long-term investors.
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-lg text-textMuted">
          Build a disciplined PSX portfolio without learning finance.
          Rupeya.ai reads filings, analyzes fundamentals, and explains every
          decision in plain English — for the price of a cup of chai a day.
        </p>
        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <button className="rounded-lg bg-accent px-6 py-3 font-semibold text-background hover:opacity-90">
            Build my portfolio
          </button>
          <button className="rounded-lg border border-border px-6 py-3 font-medium hover:bg-surface">
            See a sample analysis
          </button>
        </div>
        <p className="mt-4 text-xs text-textMuted">
          Educational research tool. Not investment advice.
        </p>
      </section>

      {/* 3-step explainer */}
      <section className="mx-auto max-w-page px-6 py-16">
        <h2 className="text-center text-2xl font-semibold tracking-tight sm:text-3xl">
          How it works
        </h2>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {[
            {
              n: "1",
              title: "Tell us about you",
              body:
                "Answer 8 quick questions about your goals, horizon, and risk comfort. Takes under 3 minutes.",
            },
            {
              n: "2",
              title: "Get your portfolio",
              body:
                "Our AI builds a long-term PSX portfolio of 8–12 stocks tailored to your profile — with reasoning.",
            },
            {
              n: "3",
              title: "Watch it work",
              body:
                "Daily insights, dividend tracking, and SIP guidance. We tell you when to act — and when to sit still.",
            },
          ].map((s) => (
            <div
              key={s.n}
              className="rounded-xl border border-border bg-surface p-6"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accentSoft text-sm font-semibold text-accent">
                {s.n}
              </div>
              <h3 className="mt-4 text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-textMuted">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="mx-auto max-w-page px-6 py-16">
        <h2 className="text-center text-2xl font-semibold tracking-tight sm:text-3xl">
          Simple, fair pricing
        </h2>
        <p className="mt-3 text-center text-textMuted">
          Cancel anytime. Pricing in PKR.
        </p>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {[
            {
              name: "Monthly",
              price: "500",
              period: "per month",
              best: false,
              note: "Try it out, cancel anytime.",
            },
            {
              name: "6 Months",
              price: "2,500",
              period: "for 6 months",
              best: true,
              note: "Save PKR 500 vs monthly.",
            },
            {
              name: "Annual",
              price: "5,000",
              period: "for the year",
              best: false,
              note: "Save PKR 1,000 vs monthly.",
            },
          ].map((p) => (
            <div
              key={p.name}
              className={`rounded-xl border p-6 ${
                p.best
                  ? "border-accent bg-accentSoft/30"
                  : "border-border bg-surface"
              }`}
            >
              {p.best && (
                <span className="mb-3 inline-block rounded-full bg-accent px-2 py-0.5 text-xs font-semibold text-background">
                  Most popular
                </span>
              )}
              <h3 className="text-xl font-semibold">{p.name}</h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-sm text-textMuted">PKR</span>
                <span className="text-4xl font-bold tracking-tight">
                  {p.price}
                </span>
              </div>
              <p className="mt-1 text-sm text-textMuted">{p.period}</p>
              <p className="mt-4 text-sm">{p.note}</p>
              <button className="mt-6 w-full rounded-lg border border-border bg-surfaceAlt px-4 py-2 font-medium hover:bg-border">
                Coming soon
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Disclaimer footer */}
      <footer className="border-t border-border bg-surface">
        <div className="mx-auto max-w-page px-6 py-10 text-sm text-textMuted">
          <div className="flex flex-col items-start justify-between gap-6 sm:flex-row">
            <div>
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-md bg-accent" aria-hidden />
                <span className="font-semibold text-text">
                  Rupeya<span className="text-accent">.ai</span>
                </span>
              </div>
              <p className="mt-3 max-w-md">
                AI-powered research for Pakistani long-term investors.
                Made with care in Pakistan.
              </p>
            </div>
            <div className="text-xs leading-relaxed">
              <p className="max-w-md">
                <strong className="text-text">Important:</strong>{" "}
                Rupeya.ai is an educational research tool, not a SECP-licensed
                investment advisor. All content is generated by AI from public
                information and may contain errors. Stock prices are subject to
                market risk. Past performance does not guarantee future
                results. Please consult a SECP-registered financial advisor
                before making investment decisions. You alone are responsible
                for your trades.
              </p>
            </div>
          </div>
          <div className="mt-8 border-t border-border pt-6 text-xs">
            © {new Date().getFullYear()} Rupeya.ai · Pre-launch build
          </div>
        </div>
      </footer>
    </main>
  );
}
