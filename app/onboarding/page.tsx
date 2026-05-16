// Rupeya.ai — Onboarding page (/onboarding)
// Auth-gated. Renders the 9-question wizard from prototype/onboarding.html.
// Saves the resulting InvestorProfile to public.investor_profiles on submit.

import type { Metadata } from "next";
import { redirect } from "next/navigation";
import Container from "@/components/Container";
import { getCurrentUser } from "@/lib/supabase/server";
import OnboardingWizard from "./OnboardingWizard";

export const metadata: Metadata = {
  title: "Tell us about you",
  description:
    "Answer 9 quick questions about your goals, horizon, and risk comfort. Takes under three minutes.",
};

export default async function OnboardingPage() {
  const user = await getCurrentUser();
  if (!user) {
    // Bounce to sign-in, come back here after success.
    redirect("/sign-in");
  }

  return (
    <section className="py-12">
      <Container>
        <OnboardingWizard />
      </Container>
    </section>
  );
}
