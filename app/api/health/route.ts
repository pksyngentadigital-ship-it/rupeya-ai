// Rupeya.ai — Health check endpoint (with raw-fetch diagnostic)
// -----------------------------------------------------------
// GET /api/health
//
// Returns a JSON status object proving the full chain works:
//   browser → Next.js route handler → Supabase REST → Postgres → back.
//
// In addition to the supabase-js client probe, this version also runs
// a raw fetch() against Supabase's REST endpoint. Comparing the two
// tells us whether failures are in the network/auth layer or in the
// supabase-js wrapper.
// -----------------------------------------------------------

import { NextResponse } from "next/server";
import { supabaseAnon } from "@/lib/supabase";
import { isAnthropicConfigured } from "@/lib/anthropic";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  const startedAt = Date.now();

  const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  const envCheck = {
    NEXT_PUBLIC_SUPABASE_URL: SUPABASE_URL ? "set" : "missing",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: SUPABASE_ANON_KEY
      ? `set (prefix: ${SUPABASE_ANON_KEY.slice(0, 20)}..., length: ${SUPABASE_ANON_KEY.length})`
      : "missing",
    SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY
      ? "set"
      : "missing",
  };

  // ---------------- Probe 1: raw fetch to PostgREST ----------------
  let rawProbe: Record<string, unknown> = { skipped: true };
  if (SUPABASE_URL && SUPABASE_ANON_KEY) {
    try {
      const rawStart = Date.now();
      const url = `${SUPABASE_URL}/rest/v1/stocks?select=ticker&limit=1`;
      const resp = await fetch(url, {
        method: "GET",
        headers: {
          apikey: SUPABASE_ANON_KEY,
          Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
          Accept: "application/json",
        },
        cache: "no-store",
      });
      const bodyText = await resp.text();
      rawProbe = {
        status: resp.status,
        statusText: resp.statusText,
        contentType: resp.headers.get("content-type"),
        bodyLength: bodyText.length,
        bodyPreview: bodyText.slice(0, 500),
        latencyMs: Date.now() - rawStart,
      };
    } catch (err) {
      rawProbe = {
        error: true,
        message: err instanceof Error ? err.message : String(err),
        name: err instanceof Error ? err.name : null,
      };
    }
  }

  // ---------------- Probe 2: supabase-js client ----------------
  let clientProbe: Record<string, unknown> = { skipped: true };
  try {
    const supabase = supabaseAnon();
    const clientStart = Date.now();
    const { count, error, status, statusText } = await supabase
      .from("stocks")
      .select("*", { count: "exact", head: true });

    clientProbe = {
      ok: !error,
      count: count ?? null,
      status,
      statusText,
      error: error
        ? {
            message: error.message || "(empty)",
            code: error.code ?? null,
            details: error.details ?? null,
            hint: error.hint ?? null,
            raw: JSON.parse(JSON.stringify(error)),
          }
        : null,
      latencyMs: Date.now() - clientStart,
    };
  } catch (err) {
    clientProbe = {
      exception: true,
      message: err instanceof Error ? err.message : String(err),
    };
  }

  const overallOk =
    rawProbe && (rawProbe.status === 200 || rawProbe.status === 206);

  return NextResponse.json(
    {
      ok: overallOk,
      service: "rupeya-ai",
      env: process.env.VERCEL_ENV ?? "local",
      anthropic: isAnthropicConfigured() ? "configured" : "missing",
      envCheck,
      rawProbe,
      clientProbe,
      totalLatencyMs: Date.now() - startedAt,
      timestamp: new Date().toISOString(),
    },
    { status: overallOk ? 200 : 500 }
  );
}
