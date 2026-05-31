// Rupeya.ai — Coming Soon module placeholder
// Used for modules deferred to v1.1 (LLM-powered: Builder, Doctor, Ask,
// Compare) and the portfolio Dashboard. Keeps launch API-spend at $0 and
// always points users to the live Signal List.

import { type ReactNode } from "react";
import Container from "@/components/Container";
import Button from "@/components/ui/Button";

export default function ComingSoon({
  kicker,
  title,
  children,
}: {
  kicker?: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <section className="py-section">
      <Container>
        <div className="mx-auto max-w-[640px] text-center">
          {kicker ? (
            <p className="text-xs font-semibold uppercase tracking-wider2 text-accent">
              {kicker}
            </p>
          ) : null}
          <h1 className="mt-3">{title}</h1>
          {children ? <div className="mt-4 text-textMuted">{children}</div> : null}
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button as="a" href="/stocks" variant="primary" size="lg">
              Explore the Signal List →
            </Button>
          </div>
          <p className="mt-6 text-xs text-textMuted">
            Live now: Rupeya’s full PSX research signal list. The AI-guided portfolio
            tools are rolling out next.
          </p>
        </div>
      </Container>
    </section>
  );
}
