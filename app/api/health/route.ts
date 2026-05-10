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
      return NextResponse.json(
        {
          ok: false,
          stage: "supabase_query",
          message: error.message,
          hint: error.hint ?? null,
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
