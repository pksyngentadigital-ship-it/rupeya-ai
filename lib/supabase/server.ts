// Rupeya.ai — Cookie-aware Supabase client for the server
// -----------------------------------------------------------
// Use this in:
//   • React Server Components (any default `page.tsx` / `layout.tsx`)
//   • Server Actions ("use server")
//   • Route Handlers (`app/api/*/route.ts`)
//
// It reads and writes the auth cookie on the current request, so queries
// run as the signed-in user and RLS works correctly.
//
// For server-side code that should bypass RLS (cron jobs, admin scripts,
// scrapers), use `supabaseAdmin()` from `@/lib/supabase` instead.
// -----------------------------------------------------------

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export function createSupabaseServerClient() {
  const cookieStore = cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // `cookieStore.set` throws when called from a Server Component.
            // That's expected — the middleware refreshes cookies on each
            // request, so a missed write here doesn't break auth.
          }
        },
      },
    }
  );
}

/**
 * Convenience helper for the most common case — "is anyone signed in,
 * and if so, who?". Returns the auth user or null.
 *
 * Use `getUser()` (which re-validates with Supabase) over `getSession()`
 * for any decision that affects security (auth gates, RLS-trusted reads).
 */
export async function getCurrentUser() {
  const supabase = createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return user;
}
