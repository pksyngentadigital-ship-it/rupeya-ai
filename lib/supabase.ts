// Rupeya.ai — Supabase client factories
// -----------------------------------------------------------
// Two server-side clients:
//   • supabaseAnon()  — uses the publishable (anon) key. Respects RLS.
//                       Safe for any server-side public read (stocks, prices,
//                       scores, etc.) and for any user-scoped read once auth
//                       cookies are wired in Phase B2.
//   • supabaseAdmin() — uses the service_role (secret) key. BYPASSES RLS.
//                       Only ever instantiated in trusted server contexts:
//                       cron jobs, scrapers, admin verification flows.
//                       NEVER import this from a client component.
// -----------------------------------------------------------
//
// These are deliberately thin. We will add the @supabase/ssr cookie-aware
// server client in Phase B2 when we need authenticated user sessions.

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

function assertEnv(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(
      `[supabase] Missing env var: ${name}. ` +
        `Check .env.local locally or your Vercel project settings in production.`
    );
  }
  return value;
}

/** Anon-key client. Respects RLS. Safe for public reads. */
export function supabaseAnon(): SupabaseClient {
  return createClient(
    assertEnv("NEXT_PUBLIC_SUPABASE_URL", SUPABASE_URL),
    assertEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", SUPABASE_ANON_KEY),
    { auth: { persistSession: false } }
  );
}

/** Service-role client. BYPASSES RLS. Server-only. Never expose to browser. */
export function supabaseAdmin(): SupabaseClient {
  return createClient(
    assertEnv("NEXT_PUBLIC_SUPABASE_URL", SUPABASE_URL),
    assertEnv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY),
    { auth: { persistSession: false } }
  );
}
