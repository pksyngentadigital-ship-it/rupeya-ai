"""Rupeya.ai B4 scoring engine -- deterministic, $0-API. Quant-First / LLM-Last.

Foundation (B4.0): macro, periods, stats, scale, types, data.load_universe().
Pillars: financial_health (B4.1), valuation (B4.2), business_quality (B4.3),
catalysts (B4.4).
"""

from __future__ import annotations

from .data import load_universe, Universe
from .financial_health import score_financial_health
from .valuation import score_valuation
from .business_quality import score_business_quality, build_sector_context
from .catalysts import score_catalysts
from .types import (
    Archetype, Coverage, Tier, DataCoverage,
    ScoreComponent, PillarResult, StockBundle, StockScoreResult,
)

__all__ = [
    "load_universe", "Universe",
    "score_financial_health", "score_valuation", "score_business_quality",
    "score_catalysts", "build_sector_context",
    "Archetype", "Coverage", "Tier", "DataCoverage",
    "ScoreComponent", "PillarResult", "StockBundle", "StockScoreResult",
]
