"""
Centralized Claude model selection — cost-optimized.

Per founder directive: use the cheapest model that gets the job done.
Sonnet (~20x the cost of Haiku) is reserved for tasks where the USER
sees the output and makes a decision from it. Bulk transcription /
extraction / classification work always goes through Haiku.

Cost reference (approximate, USD per 1M tokens):
  • Haiku 4.5  — $1 in / $5 out   ← bulk work
  • Sonnet 4.6 — $3 in / $15 out  ← user-facing reasoning
  • Opus 4.6   — much higher      ← currently unused

Spend map for Rupeya:
  • B3a fundamentals extraction (PDF → JSON)         → Haiku  (bulk, no reasoning)
  • B3b news summarization + sentiment scoring       → Haiku  (bulk, no reasoning)
  • B3b new-project / catalyst classification        → Haiku  (bulk, no reasoning)
  • Daily Stock Analyst memos (Tier A, per stock)    → Haiku  (bulk, low stakes)
  • Stock Comparison synthesis paragraph             → Sonnet (user-facing reasoning)
  • Portfolio Doctor verdicts (Tier B, per user)     → Sonnet (user-facing reasoning)
  • Ask Rupeya agent (Tier D, multi-tool reasoning)  → Sonnet (user-facing reasoning)

Estimated annual API spend at ~500 paying users: $20–50/month.
Estimated B3a backfill one-off:                    $60–100.
"""

from __future__ import annotations

# --- Model identifiers ------------------------------------------------------
# Pinned to specific releases so behavior is reproducible run-to-run.
# Update these intentionally when a new release is validated.

MODEL_HAIKU: str = "claude-haiku-4-5-20251001"
MODEL_SONNET: str = "claude-sonnet-4-6"
MODEL_OPUS: str = "claude-opus-4-6"  # not currently used

# --- Task → model mapping ---------------------------------------------------
# Import these constants from feature modules. Never hard-code a model name
# elsewhere — that scatters cost decisions across the codebase.

# Bulk extraction & classification — Haiku is plenty.
FUNDAMENTALS_EXTRACTION_MODEL: str = MODEL_HAIKU
NEWS_SUMMARIZATION_MODEL: str = MODEL_HAIKU
NEWS_SENTIMENT_MODEL: str = MODEL_HAIKU
CATALYST_CLASSIFICATION_MODEL: str = MODEL_HAIKU
DAILY_MEMO_MODEL: str = MODEL_HAIKU

# User-facing reasoning — Sonnet earns its keep.
PORTFOLIO_DOCTOR_MODEL: str = MODEL_SONNET
ASK_RUPEYA_AGENT_MODEL: str = MODEL_SONNET
STOCK_COMPARISON_MODEL: str = MODEL_SONNET
