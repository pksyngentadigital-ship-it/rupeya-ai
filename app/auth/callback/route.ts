// Rupeya.ai — Google OAuth callback
// -----------------------------------------------------------
// GET /auth/callback?code=...&next=/dashboard
//
// After Google → Supabase, Supabase redirects the browser here with a
// short-lived `code`. We exchange that for an actual session, set the
// cookie, then redirect onward (?next= if specified, else /dashboard).
//
// Errors are surfaced via /sign-in?error=... so the user sees a clear
// message rather than a stack trace.
// -----------------------------------------------------------

import { NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  // OAuth error params (e.g. user clicked "Cancel" in Google's consent screen)
  const oauthError = searchParams.get("error");
  if (oauthError) {
    return NextResponse.redirect(
      `${origin}/sign-in?error=${encodeURIComponent(oauthError)}`
    );
  }

  if (!code) {
    return NextResponse.redirect(`${origin}/sign-in?error=missing_code`);
  }

  const supabase = createSupabaseServerClient();
  const { error } = await supabase.auth.exchangeCodeForSession(code);

  if (error) {
    return NextResponse.redirect(
      `${origin}/sign-in?error=${encodeURIComponent(error.message)}`
    );
  }

  return NextResponse.redirect(`${origin}${next}`);
}
