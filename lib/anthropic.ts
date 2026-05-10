// Rupeya.ai — Anthropic Claude client wrapper
// -----------------------------------------------------------
// Thin server-only factory for the Anthropic SDK plus the model
// constants used across the app. Per blueprint Section 3.1:
//
//   • Tier A (batch enrichment, daily memos) → CLAUDE_HAIKU (cheap, fast)
//   • Tier B (Portfolio Doctor verdicts, IC-grade memos) → CLAUDE_SONNET
//   • Tier D (Ask Rupeya agent w/ tool use) → CLAUDE_SONNET
//
// Bumping a tier's model is one line. We pin model strings here rather
// than scattering them across handlers.
//
// IMPORTANT: never import this file from a client component — the
// ANTHROPIC_API_KEY must never reach the browser bundle.
// -----------------------------------------------------------

import Anthropic from "@anthropic-ai/sdk";

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;

/** Model constants — change here, propagates everywhere. */
export const CLAUDE_HAIKU = "claude-haiku-4-5-20251001";
export const CLAUDE_SONNET = "claude-sonnet-4-6";
export const CLAUDE_OPUS = "claude-opus-4-6";

/** Tier → model mapping (blueprint Section 3.1). */
export const MODELS = {
  batch_enrichment: CLAUDE_HAIKU, // Tier A
  on_demand_reasoning: CLAUDE_SONNET, // Tier B
  conversational: CLAUDE_HAIKU, // Tier C
  agent: CLAUDE_SONNET, // Tier D
} as const;

let client: Anthropic | null = null;

/**
 * Returns a lazily-initialized Anthropic client.
 * Throws a clear error if ANTHROPIC_API_KEY is missing.
 */
export function getAnthropic(): Anthropic {
  if (!ANTHROPIC_API_KEY) {
    throw new Error(
      "[anthropic] Missing env var: ANTHROPIC_API_KEY. " +
        "Check .env.local locally or your Vercel project settings in production."
    );
  }
  if (!client) {
    client = new Anthropic({ apiKey: ANTHROPIC_API_KEY });
  }
  return client;
}

/** Returns true if the key is configured. Used by /api/health. */
export function isAnthropicConfigured(): boolean {
  return Boolean(ANTHROPIC_API_KEY);
}
