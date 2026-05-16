// Rupeya.ai — Session-refresh middleware utility
// -----------------------------------------------------------
// Called from /middleware.ts on every request. Its job is to:
//   1. Read the current session cookie
//   2. Refresh the access token if it's expired (Supabase auto-handles)
//   3. Forward the (possibly updated) cookie on the response
//
// This is what keeps a user logged in across navigations without a
// full sign-in flow each time. Without this, every page load could lose
// the session if the access token has rolled over.
// -----------------------------------------------------------

import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // IMPORTANT: do NOT replace this with `getSession()` — that reads from
  // the cookie without validating against the auth server, and is unsafe
  // for security-sensitive decisions.
  await supabase.auth.getUser();

  return supabaseResponse;
}
