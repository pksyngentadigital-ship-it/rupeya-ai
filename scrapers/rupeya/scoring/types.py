"""
Glass-box data types for the scoring engine.

Every score carries provenance -- inputs used, threshold graded against, data
coverage, one-line rationale -- so the narrative layer only describes audited
figures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Archetype(str, Enum):
    BANK = "bank"
    INSURANCE = "insurance"
    NON_FINANCIAL = "non_financial"


SECTOR_ARCHETYPE = {
    "Commercial Banks": Archetype.BANK,
    "Insurance": Archetype.INSURANCE,
}


class Coverage(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class Tier(str, Enum):
    RICH = "rich"
    GROWTH_ONLY = "growth_only"
    SINGLE_PERIOD = "single_period"


@dataclass
class ScoreComponent:
    name: str
    score: float | None
    weight: float = 1.0
    coverage: Coverage = Coverage.FULL
    inputs: dict = field(default_factory=dict)
    threshold: str = ""
    rationale: str = ""


@dataclass
class PillarResult:
    name: str
    score: float | None
    weight: float
    coverage: Coverage = Coverage.FULL
    components: list = field(default_factory=list)
    notes: list = field(default_factory=list)


@dataclass
class DataCoverage:
    n_periods: int = 0
    n_annual: int = 0
    tier: Tier = Tier.SINGLE_PERIOD
    has_growth: bool = False
    has_returns: bool = False
    has_leverage: bool = False
    has_cashflow: bool = False
    has_dividends: bool = False
    has_price: bool = False


@dataclass
class StockBundle:
    ticker: str
    name: str
    sector: str | None
    sub_sector: str | None
    archetype: Archetype

    is_shariah_compliant: bool | None = None
    shariah_ratios: dict | None = None
    style: str | None = None

    rows: list = field(default_factory=list)
    annual: list = field(default_factory=list)
    latest_fy: dict | None = None
    latest_row: dict | None = None

    bs_snapshot: dict | None = None
    bs_fields_present: list = field(default_factory=list)

    latest_price: float | None = None
    latest_price_date: str | None = None

    implied_shares: float | None = None
    implied_shares_series: list = field(default_factory=list)
    share_count_changed: bool = False
    share_count_change_ratio: float | None = None
    market_cap: float | None = None

    ttm_ni: float | None = None
    ttm_revenue: float | None = None
    ttm_eps: float | None = None
    ttm_basis: str = ""

    revenue_cagr: float | None = None
    revenue_cagr_years: float | None = None
    ni_cagr: float | None = None
    ni_cagr_years: float | None = None

    coverage: DataCoverage = field(default_factory=DataCoverage)
    integrity_flags: list = field(default_factory=list)


@dataclass
class StockScoreResult:
    ticker: str
    business_quality: float | None = None
    financial_health: float | None = None
    valuation: float | None = None
    catalysts: float | None = None
    composite: float | None = None
    intrinsic_value_pkr: float | None = None
    margin_of_safety: float | None = None
    flags: dict = field(default_factory=dict)
    model_version: str = ""

    def to_db_row(self):
        return {
            "ticker": self.ticker,
            "business_quality": self.business_quality,
            "financial_health": self.financial_health,
            "valuation": self.valuation,
            "catalysts": self.catalysts,
            "composite": self.composite,
            "intrinsic_value_pkr": self.intrinsic_value_pkr,
            "margin_of_safety": self.margin_of_safety,
            "flags": self.flags,
            "model_version": self.model_version,
        }
