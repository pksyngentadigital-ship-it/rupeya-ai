"""
Rupeya.ai B4 — deterministic, $0-API scoring engine.

Quant-First / LLM-Last: every number here is computed by audited Python from
the fundamentals + price spine. No LLM ever touches a figure in this package.

B4.0 (this commit) ships the foundation only:
  • macro    — Pakistan macro yardsticks (KIBOR/PIB/CPI)
  • periods  — cumulative→standalone, TTM, CAGR algebra
  • stats    — robust (median/MAD) cross-sectional helpers
  • types    — glass-box dataclasses (ScoreComponent / PillarResult / StockBundle …)
  • data     — load_universe(): raw rows -> analyst-ready StockBundles
Pillar scoring (B4.1–B4.5) and the orchestrator (B4.6) land in later commits.
"""

from __future__ import annotations

from .data import load_universe, Universe
from .types import (
    Archetype, Coverage, Tier, DataCoverage,
    ScoreComponent, PillarResult, StockBundle, StockScoreResult,
)

__all__ = [
    "load_universe", "Universe",
    "Archetype", "Coverage", "Tier", "DataCoverage",
    "ScoreComponent", "PillarResult", "StockBundle", "StockScoreResult",
]
