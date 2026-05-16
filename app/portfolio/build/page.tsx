// Rupeya.ai — Portfolio Builder result (STUB)
// -----------------------------------------------------------
// Placeholder so onboarding has somewhere to land on submit.
// Task #17 (B1) replaces this with the real builder result:
// 6–7 recommended holdings, sector mix, blended margin of safety,
// runners-up watchlist, accept/swap CTAs.
// -----------------------------------------------------------

import { redirect } from "next/navigation";
import Link from "next/link";
import Container from "@/components/Container";
import Card from "@/components/ui/Card";
import Chip from "@/components/ui/Chip";
import Button from "@/components/ui/Button";
import { getCurrentUser } from "@/lib/supabase/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const metadata = {
  title: "Your Rupeya portfolio",
};

export default async function PortfolioBuildPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/sign-in");
  }

  // Read the saved investor profile so we can confirm it persisted.
  const supabase = createSupabaseServerClient();
  const { data: profile } = await supabase
    .from("investor_profiles")
    .select("horizon_years, risk_score, income_vs_growth, shariah_only, goal_text, updated_at")
    .eq("user_id", user.id)
    .maybeSingle();

  return (
    <section className="py-section">
      <Container>
        <div className="mx-auto max-w-3xl">
          <Chip variant="accent">Profile saved ✓</Chip>
          <h1 className="mt-4 text-[40px] leading-tight sm:text-[48px]">
            Your portfolio is being designed
          </h1>
          <p className="mt-3 text-textMuted">
            The AI Portfolio Builder lands in Task #17 of Phase B1. For now,
            this page confirms your onboarding answers were saved to the
            database (RLS-scoped to you only).
          </p>

          {profile ? (
            <Card className="mt-8">
              <h3>Saved profile (from Supabase)</h3>
              <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                <ProfileField label="Horizon" value={`${profile.horizon_years} years`} />
                <ProfileField
                  label="Risk score"
                  value={profile.risk_score?.toFixed(2) ?? "—"}
                />
                <ProfileField
                  label="Income vs growth"
                  value={profile.income_vs_growth ?? "—"}
                />
                <ProfileField
                  label="Shariah-only"
                  value={profile.shariah_only ? "Yes" : "No"}
                  accent={profile.shariah_only}
                />
                <div className="sm:col-span-2">
                  <ProfileField label="Goal" value={profile.goal_text ?? "—"} />
                </div>
                <div className="sm:col-span-2 text-xs text-textMuted">
                  Updated {new Date(profile.updated_at).toLocaleString("en-PK")}
                </div>
              </dl>
            </Card>
          ) : (
            <Card className="mt-8">
              <p className="text-textMuted">
                No profile saved yet.{" "}
                <Link href="/onboarding" className="text-accent underline">
                  Start onboarding →
                </Link>
              </p>
            </Card>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <Button as="a" href="/dashboard" variant="primary">
              Go to dashboard
            </Button>
            <Button as="a" href="/onboarding" variant="ghost">
              Edit answers
            </Button>
          </div>
        </div>
      </Container>
    </section>
  );
}

function ProfileField({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs text-textMuted">{label}</dt>
      <dd className={`mt-1 font-semibold ${accent ? "text-accent" : "text-text"}`}>
        {value}
      </dd>
    </div>
  );
}
