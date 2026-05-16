// Rupeya.ai — Sign-in / sign-up server actions
// -----------------------------------------------------------
// All auth mutations happen here. Three paths supported:
//   1. signInWithPassword     — existing user, password account
//   2. signUpWithPassword     — new account with password (Supabase emails
//                                a confirmation link; user clicks → session)
//   3. signInWithGoogle       — OAuth redirect; resumes via /auth/callback
//
// All actions return a structured result the client can render. We never
// throw — auth errors are normal UX events, not exceptions.
// -----------------------------------------------------------

"use server";

import { createSupabaseServerClient } from "@/lib/supabase/server";
import { headers } from "next/headers";

export type AuthResult =
  | { ok: true; redirectTo?: string; message?: string }
  | { ok: false; message: string };

/** Resolve the absolute site URL for redirect destinations. */
function getSiteOrigin(): string {
  // Prefer the actual request origin (handles preview deployments too)
  const h = headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host");
  if (host) return `${proto}://${host}`;
  // Fallback
  return process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
}

/* -------- Password sign-in -------- */

export async function signInWithPassword(formData: FormData): Promise<AuthResult> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return { ok: false, message: "Email and password are both required." };
  }

  const supabase = createSupabaseServerClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) {
    // Supabase returns a deliberately vague message to avoid email enumeration.
    return { ok: false, message: error.message };
  }

  return { ok: true, redirectTo: "/dashboard" };
}

/* -------- Password sign-up -------- */

export async function signUpWithPassword(formData: FormData): Promise<AuthResult> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return { ok: false, message: "Email and password are both required." };
  }

  if (password.length < 8) {
    return {
      ok: false,
      message: "Password must be at least 8 characters.",
    };
  }

  const supabase = createSupabaseServerClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      // After clicking the confirmation email, land here.
      emailRedirectTo: `${getSiteOrigin()}/auth/confirm`,
    },
  });

  if (error) {
    return { ok: false, message: error.message };
  }

  // If the project requires email confirmation (we enabled it in Supabase),
  // there's no session yet — the user must click the link in their inbox.
  if (data.user && !data.session) {
    return {
      ok: true,
      message:
        "Check your inbox — we sent a confirmation link to your email. Click it to activate your account.",
    };
  }

  // Otherwise, user is signed in immediately
  return { ok: true, redirectTo: "/dashboard" };
}

/* -------- Google OAuth start -------- */

export async function signInWithGoogle(): Promise<AuthResult> {
  const supabase = createSupabaseServerClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: `${getSiteOrigin()}/auth/callback`,
    },
  });

  if (error) {
    return { ok: false, message: error.message };
  }

  // Supabase returns a URL we redirect the browser to (Google's consent screen).
  return { ok: true, redirectTo: data.url };
}
