// Rupeya.ai — Dashboard (STUB for auth verification only)
// -----------------------------------------------------------
// This is a placeholder so the auth flow has somewhere to land.
// Task #16 (B1) will replace it with the real dashboard: portfolio health
// card, today's insights, holdings table, Ask Rupeya right rail.
// -----------------------------------------------------------

import { redirect } from "next/navigation";
import Link from "next/link";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Button from "@/components/ui/Button";
import { getCurrentUser } from "@/lib/supabase/server";

export const metadata = {
  title: "Dashboard",
};

export default async function DashboardPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/sign-in");
  }

  return (
    <section className="py-section">
      <Container>
        <div className="mx-auto max-w-3xl">
          <Chip variant="accent">You&apos;re signed in</Chip>
          <h1 className="mt-4 text-[40px] leading-tight sm:text-[48px]">
            Welcome to Rupeya.ai 👋
          </h1>
          <p className="mt-3 text-textMuted">
            Signed in as <span className="text-text">{user.email}</span> ·
            joined{" "}
            {new Date(user.created_at).toLocaleDateString("en-PK", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}
          </p>

          <Card className="mt-8">
            <h3>This dashboard is a temporary stub</h3>
            <p className="mt-2 text-textMuted">
              The real dashboard (portfolio health, today&apos;s insights,
              holdings table, Ask Rupeya rail) lands in Task #16 of Phase B1.
              For now, this page exists so the sign-in flow has somewhere to
              land — and so we can verify auth works end-to-end.
            </p>
            <p className="mt-3 text-textMuted">
              Try refreshing the page, opening a new tab, or signing out and
              back in — your session is persisted via cookies so you stay
              logged in across navigation and reloads.
            </p>
          </Card>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button as="a" href="/onboarding" variant="primary">
              Start onboarding →
            </Button>
            <Button as="a" href="/" variant="ghost">
              Back to landing
            </Button>
          </div>
        </div>
      </Container>
    </section>
  );
}
