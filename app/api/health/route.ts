// Rupeya.ai — Health check endpoint
// -----------------------------------------------------------
// GET /api/health
//
// Returns a JSON status object proving the full chain works:
//   browser → Next.js route handler → Supabase REST → Postgres → back.
//
// We hit this after every deploy as the first smoke test. If it returns
// `ok: true` with a non-zero `stockCount`, the foundation is healthy.
// If `ok: false`, the response body tells us where the chain broke.
// -----------------------------------------------------------

import { NextResponse } from "next/server";
import { supabaseAnon } from "@/lib/supabase";
import { isAnthropicConfigured } from "@/lib/anthropic";

// Always run on the server, never cache — health checks must be live.
export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  const startedAt = Date.now();

  try {
    const supabase = supabaseAnon();

    // Probe 1: count rows in `stocks`. Uses the public-read RLS policy,
    // so this works without any user session.
    const { count, error } = await supabase
      .from("stocks")
      .select("*", { count: "exact", head: true });

    if (error) {
      // Surface the full error shape so we can debug production failures.
      // Supabase errors carry { message, details, hint, code } — at least one
      // is almost always populated. We also report whether each env var is
      // present (NOT the values — never leak secrets through an HTTP response).
      return NextResponse.json(
        {
          ok: false,
          stage: "supabase_query",
          message: error.message || "(empty message from supabase client)",
          code: error.code ?? null,
          details: error.details ?? null,
          hint: error.hint ?? null,
          envCheck: {
            NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL
              ? "set"
              : "missing",
            NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env
              .NEXT_PUBLIC_SUPABASE_ANON_KEY
              ? `set (prefix: ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY.slice(0, 20)}...)`
              : "missing",
            SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY
              ? "set"
              : "missing",
          },
          rawError: JSON.parse(JSON.stringify(error)),
          latencyMs: Date.now() - startedAt,
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      ok: true,
      service: "rupeya-ai",
      env: process.env.VERCEL_ENV ?? "local",
      supabase: "connected",
      stockCount: count ?? 0,
      anthropic: isAnthropicConfigured() ? "configured" : "missing",
      latencyMs: Date.now() - startedAt,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      {
        ok: false,
        stage: "exception",
        message,
        latencyMs: Date.now() - startedAt,
      },
      { status: 500 }
    );
  }
}
