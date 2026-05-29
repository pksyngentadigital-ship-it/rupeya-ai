"""
Glass-box data types for the scoring engine.

Design principle (Quant-First / LLM-Last + auditability): every score carries
its own provenance — the raw inputs it used, the threshold it was graded
against, how complete the data was, and a one-line human rationale. Nothing is
a bare number. This is what lets the narrative layer describe only audited
figures and lets us defend any score to a regulator or a skeptical investor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Archetype(str, Enum):
    """Financial archetype — decides WHICH metrics are meaningful.

    A bank's 'debt' is deposits, not solvency leverage; an insurer's float is
    not industrial cash. We never apply industrial ratios across archetypes.
    """

    BANK = "bank"
    INSURANCE = "insurance"
    NON_FINANCIAL = "non_financial"


# Map PSX sector strings -> archetype. Anything unlisted => NON_FINANCIAL.
SECTOR_ARCHETYPE: dict[str, Archetype] = {
    "Commercial Banks": Archetype.BANK,
    "Insurance": Archetype.INSURANCE,
}


class Coverage(str, Enum):
    FULL = "full"        # all inputs present
    PARTIAL = "partial"  # some inputs present, score re-normalized over them
    NONE = "none"        # nothing feedable — score is None, flagged


class Tier(str, Enum):
    RICH = "rich"                  # has balance-sheet data
    GROWTH_ONLY = "growth_only"    # >=2 annual points, income statement only
    SINGLE_PERIOD = "single_period"  # one period only — no history


@dataclass
class ScoreComponent:
    """One sub-factor's graded result, with full provenance."""

    name: str
    score: float | None                      # 0-5, or None if not feedable
    weight: float = 1.0                       # weight within its pillar
    coverage: Coverage = Coverage.FULL
    inputs: dict = field(default_factory=dict)   # raw numbers used
    threshold: str = ""                       # how it was graded
    rationale: str = ""                       # one-line human explanation


@dataclass
class PillarResult:
    """A pillar's aggregate, plus the components that built it."""

    name: str            # 'business_quality' | 'financial_health' | 'valuation' | 'catalysts'
    score: float | None  # 0-5
    weight: float        # pillar weight in the composite
    coverage: Coverage = Coverage.FULL
    components: list[ScoreComponent] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class DataCoverage:
    """What the scoring engine can actually feed for one ticker."""

    n_periods: int = 0
    n_annual: int = 0
    tier: Tier = Tier.SINGLE_PERIOD
    has_growth: bool = False      # >=2 annual revenue or NI points
    has_returns: bool = False     # book_value present (=> ROE)
    has_leverage: bool = False    # debt + book_value present (non-bank only)
    has_cashflow: bool = False    # fcf present
    has_dividends: bool = False   # dividend_per_share present
    has_price: bool = False


@dataclass
class StockBundle:
    """Everything the engine needs to score ONE stock. Built by data.load_universe."""

    ticker: str
    name: str
    sector: str | None
    sub_sector: str | None
    archetype: Archetype

    is_shariah_compliant: bool | None = None
    shariah_ratios: dict | None = None
    style: str | None = None

    # Raw + ordered series
    rows: list[dict] = field(default_factory=list)     # all periods, sorted
    annual: list[dict] = field(default_factory=list)   # FY rows, sorted by year
    latest_fy: dict | None = None
    latest_row: dict | None = None                     # most recent of any kind

    # Balance sheet is a point-in-time snapshot (may be a different period than earnings)
    bs_snapshot: dict | None = None
    bs_fields_present: list[str] = field(default_factory=list)

    # Price
    latest_price: float | None = None
    latest_price_date: str | None = None

    # Derived (the veteran primitives)
    implied_shares: float | None = None           # latest NI/EPS
    implied_shares_series: list[tuple[int, float]] = field(default_factory=list)
    share_count_changed: bool = False             # bonus/split/rights detected
    share_count_change_ratio: float | None = None
    market_cap: float | None = None               # price * implied_shares

    ttm_ni: float | None = None
    ttm_revenue: float | None = None
    ttm_eps: float | None = None
    ttm_basis: str = ""                           # how TTM was derived (auditable)

    # Growth — computed from ABSOLUTE NI/revenue (split-immune), never EPS
    revenue_cagr: float | None = None
    revenue_cagr_years: float | None = None
    ni_cagr: float | None = None
    ni_cagr_years: float | None = None

    coverage: DataCoverage = field(default_factory=DataCoverage)
    integrity_flags: list[str] = field(default_factory=list)


@dataclass
class StockScoreResult:
    """Final scored output for one ticker -> upserted to public.stock_scores."""

    ticker: str
    business_quality: float | None = None
    financial_health: float | None = None
    valuation: float | None = None
    catalysts: float | None = None
    composite: float | None = None
    intrinsic_value_pkr: float | None = None
    margin_of_safety: float | None = None
    flags: dict = field(default_factory=dict)   # JSONB: provenance + overrides + coverage
    model_version: str = ""

    def to_db_row(self) -> dict:
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
