// Rupeya.ai — Next.js middleware
// -----------------------------------------------------------
// Runs on every matching request. Currently only refreshes the Supabase
// session cookie. Later we'll also gate /dashboard, /portfolio/*, etc.
// for unauthenticated users here.
// -----------------------------------------------------------

import { updateSession } from "@/lib/supabase/middleware";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  // Match every request EXCEPT:
  //   • Static assets (_next/static, _next/image, favicon)
  //   • Image files (svg, png, jpg, etc.)
  // We DO want middleware to run on /api/* so server route handlers can
  // read the refreshed session via cookies().
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
