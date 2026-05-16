// Rupeya.ai — Supabase client for the browser
// -----------------------------------------------------------
// Use this in:
//   • Client Components ("use client")
//   • Hooks that subscribe to auth state changes
//
// Lazily created singleton per browser tab. Reads/writes the auth cookie
// through `document.cookie` so the session stays in sync with the server.
// -----------------------------------------------------------

"use client";

import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

export function createSupabaseBrowserClient(): SupabaseClient {
  if (!client) {
    client = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
  }
  return client;
}
