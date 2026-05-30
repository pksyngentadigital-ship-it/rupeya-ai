"""
Macro yardsticks for the scoring engine (Pakistan / PSX).

In a 10-12% policy-rate economy, +12% nominal revenue can be a REAL decline, so
growth/returns are judged against these hurdles and valuation discounts off the
sovereign (PIB) curve. Constants, not a live feed (the $0-API quant rule).
FOUNDER: refresh after each SBP MPC (~6 weeks) and update AS_OF.
Sourced late May 2026 from SBP / PBS / Trading Economics.
"""

from __future__ import annotations

AS_OF = "2026-05-29"

# Pakistan FLIPPED to tightening in Apr-2026: SBP hiked +100bps to 11.5% (first
# hike since Jun-2023) as a supply/energy shock pushed CPI back to double digits.
POLICY_RATE = 0.115        # SBP policy rate, 27-Apr-2026
KIBOR_6M = 0.123           # 6M KIBOR ~11.84-12.79% band, 20-May-2026 (midpoint)
PIB_10Y_YIELD = 0.1293     # 10Y PIB yield, 22-May-2026 (risk-free)
CPI_INFLATION_YOY = 0.109  # CPI YoY, Apr-2026 (PBS)

# Premium of PSX equities over local PIBs (PIB already embeds country/FX risk).
# Cost of equity = PIB + ERP ~= 18.9%.
EQUITY_RISK_PREMIUM = 0.06

RISK_FREE = PIB_10Y_YIELD


def real_growth(nominal, inflation=None):
    """Nominal growth -> real: (1+nom)/(1+infl)-1."""
    infl = CPI_INFLATION_YOY if inflation is None else inflation
    return (1.0 + nominal) / (1.0 + infl) - 1.0


def discount_rate(beta=1.0):
    """CAPM-style required return = risk_free + beta * ERP."""
    return RISK_FREE + beta * EQUITY_RISK_PREMIUM


def earnings_yield_spread(earnings_yield):
    """Stock E/P minus 10Y PIB yield. Positive => cheap vs the sovereign bond."""
    return earnings_yield - PIB_10Y_YIELD
