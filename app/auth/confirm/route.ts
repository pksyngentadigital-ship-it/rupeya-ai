// Rupeya.ai — Magic-link / email-confirmation callback
// -----------------------------------------------------------
// GET /auth/confirm?token_hash=...&type=...&next=/dashboard
//
// Supabase's email links land here. We verify the OTP (which establishes
// a session), then redirect onward. Used by:
//   • Magic-link sign-in (type=magiclink)
//   • Email signup confirmation (type=signup)
//   • Email change confirmation (type=email_change)
//   • Password recovery (type=recovery)
// -----------------------------------------------------------

import { type EmailOtpType } from "@supabase/supabase-js";
import { NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const token_hash = searchParams.get("token_hash");
  const type = searchParams.get("type") as EmailOtpType | null;
  const next = searchParams.get("next") ?? "/dashboard";

  if (!token_hash || !type) {
    return NextResponse.redirect(`${origin}/sign-in?error=invalid_link`);
  }

  const supabase = createSupabaseServerClient();
  const { error } = await supabase.auth.verifyOtp({ type, token_hash });

  if (error) {
    return NextResponse.redirect(
      `${origin}/sign-in?error=${encodeURIComponent(error.message)}`
    );
  }

  return NextResponse.redirect(`${origin}${next}`);
}
