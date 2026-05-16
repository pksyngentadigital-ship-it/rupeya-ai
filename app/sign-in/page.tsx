// Rupeya.ai — Sign-in page (/sign-in)
// Server-component wrapper around the interactive form.

import type { Metadata } from "next";
import { redirect } from "next/navigation";
import Container from "@/components/Container";
import { getCurrentUser } from "@/lib/supabase/server";
import SignInForm from "./SignInForm";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in or create your Rupeya.ai account.",
};

export default async function SignInPage() {
  // Already signed in? Go straight to the dashboard.
  const user = await getCurrentUser();
  if (user) {
    redirect("/dashboard");
  }

  return (
    <section className="min-h-[calc(100vh-64px)] py-section">
      <Container>
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="mb-8 text-center">
            <h1 className="text-[36px] leading-tight sm:text-[40px]">
              Sign in or sign up
            </h1>
            <p className="mt-3 text-textMuted">
              One account, three ways to get in. Same email works whether
              you&apos;re new or returning.
            </p>
          </div>
          <SignInForm />
        </div>
      </Container>
    </section>
  );
}
