"""
Macro yardsticks for the scoring engine (Pakistan / PSX context).

WHY THIS EXISTS
---------------
A 50-year fund manager never reads a Pakistani growth number at face value.
In a 10-20% policy-rate economy, +12% nominal revenue growth can be a REAL
decline. So every growth / return number is judged against these macro
hurdles, and valuation discounts off the sovereign (PIB) curve.

These are deliberately *constants*, set by hand and version-controlled, not a
live feed: they move slowly (quarterly at most), a live API would add cost +
a network dependency, and the $0-API rule for the quant engine forbids it.

⚠️  FOUNDER ACTION: verify these against current data and update the values +
    AS_OF date below. They are the single yardstick the whole engine grades
    against, so a stale KIBOR/PIB quietly biases every score. Only consumed
    from B4.1 onward, so B4.0 does not depend on them being exact yet.
"""

from __future__ import annotations

# As-of date for the values below. Update whenever you refresh them.
AS_OF = "2026-05-29"  # ⚠️ placeholder — founder to confirm

# --- Sovereign / rates (decimal, i.e. 0.12 == 12%) --------------------------
POLICY_RATE: float = 0.11          # SBP policy rate            ⚠️ verify
KIBOR_6M: float = 0.115            # 6-month KIBOR              ⚠️ verify
PIB_10Y_YIELD: float = 0.125       # 10-year PIB (risk-free)    ⚠️ verify
CPI_INFLATION_YOY: float = 0.06    # latest YoY CPI inflation   ⚠️ verify

# --- Equity assumptions -----------------------------------------------------
EQUITY_RISK_PREMIUM: float = 0.06  # PSX equity risk premium over PIB ⚠️ verify

# Risk-free rate the valuation pillar discounts against.
RISK_FREE: float = PIB_10Y_YIELD


def real_growth(nominal: float, inflation: float | None = None) -> float:
    """Convert a nominal growth rate to real (inflation-adjusted) terms.

    real = (1 + nominal) / (1 + inflation) - 1
    This is THE function that stops us calling 10% nominal growth 'good' when
    inflation is 8%.
    """
    infl = CPI_INFLATION_YOY if inflation is None else inflation
    return (1.0 + nominal) / (1.0 + infl) - 1.0


def discount_rate(beta: float = 1.0) -> float:
    """CAPM-style discount/required-return = risk_free + beta * ERP."""
    return RISK_FREE + beta * EQUITY_RISK_PREMIUM


def earnings_yield_spread(earnings_yield: float) -> float:
    """Stock E/P minus the 10Y PIB yield.

    Positive => equity is cheap vs the sovereign bond; negative => expensive.
    The core Pakistan-specific valuation lens (blueprint 4.3.4).
    """
    return earnings_yield - PIB_10Y_YIELD
