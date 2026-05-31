"""
B4.5 -- Composite RupeyaScore + verdict + style + Shariah.

RupeyaScore = 0.30*BusinessQuality + 0.30*FinancialHealth + 0.25*Valuation
            + 0.15*Catalysts, re-normalised over whatever pillars a stock has.

Verdict per blueprint 4.7 with MANDATORY overrides:
  * D/E>5x                 -> EXIT (always)
  * composite < 1.8        -> EXIT
  * NO valuation           -> capped at HOLD (never recommend buying what we
                             cannot price -- usually loss-makers)
  * price > fair x 1.50    -> at most TRIM. (Blueprint says x1.30, but our
                             intrinsic value is a deliberately conservative
                             no-real-growth floor, so x1.30 on it would flag
                             half the market; x1.50 captures the genuinely dear.)
  * LIMITED_DATA           -> capped at BUY (no thinly-covered STRONG BUY)
  * STRONG BUY needs composite >= 4.2 AND margin of safety >= 25%

Shariah is a HARD universe filter (boolean already in stocks); surfaced on every
result for the Builder to enforce. Style per 4.6 (None when undeterminable --
never a wrong label). Quant-First: deterministic; an LLM only narrates later.
"""

from __future__ import annotations

from .financial_health import score_financial_health
from .valuation import score_valuation
from .business_quality import score_business_quality
from .catalysts import score_catalysts
from .types import StockScoreResult

MODEL_VERSION = "b4-2026.05"
PILLAR_WEIGHTS = {"business_quality": 0.30, "financial_health": 0.30,
                  "valuation": 0.25, "catalysts": 0.15}
VERDICT_ORDER = {"EXIT": 0, "TRIM": 1, "HOLD": 2, "BUY": 3, "STRONG BUY": 4}
OVERVALUED_MOS = -0.50          # price > fair x1.5 -> genuinely dear
CYCLICAL_SECTORS = {"Cement", "Oil & Gas Marketing", "Refinery", "Automobile Assembler",
                    "Engineering", "Textile", "Auto Parts & Accessories", "Chemical"}


def compute_composite(pillars):
    present = [(p.score, PILLAR_WEIGHTS[name]) for name, p in pillars.items()
               if p is not None and p.score is not None]
    if not present:
        return None, 0
    tot = sum(w for _, w in present)
    return round(sum(s * w for s, w in present) / tot, 2), len(present)


def _component(pillar, name):
    if not pillar:
        return None
    return next((c for c in pillar.components if c.name == name), None)


def map_verdict(score, mos, flags):
    """Verdict with CONVICTION SELLS: never call TRIM/EXIT on a thin composite
    alone -- a sell must be backed by hard data (D/E>5x or clear over-valuation),
    or by a full-data low score. Thin-data weak names hold at neutral instead.
    """
    if score is None:
        return "NOT RATED"
    if score >= 4.2 and mos is not None and mos >= 0.25:
        v = "STRONG BUY"
    elif score >= 3.5:
        v = "BUY"
    elif score >= 2.5:
        v = "HOLD"
    elif score >= 1.8:
        v = "TRIM"
    else:
        v = "EXIT"

    def cap(verdict, ceiling):
        return verdict if VERDICT_ORDER[verdict] <= VERDICT_ORDER[ceiling] else ceiling

    def floor(verdict, fl):
        return verdict if VERDICT_ORDER[verdict] >= VERDICT_ORDER[fl] else fl

    limited = "limited_data" in flags
    de5 = "high_leverage_de5" in flags
    overvalued = mos is not None and mos < OVERVALUED_MOS
    data_backed_sell = de5 or overvalued

    # Conviction sells: don't sell on a thin-data composite alone.
    if limited and not data_backed_sell:
        v = floor(v, "HOLD")
    if "no_valuation" in flags:
        v = cap(v, "HOLD")
    if overvalued:                       # valuation-data-backed -> sell justified
        v = cap(v, "TRIM")
    if limited:                          # thin coverage -> no STRONG BUY
        v = cap(v, "BUY")
    if de5:                              # hard, data-backed
        v = "EXIT"
    elif score < 1.8 and not limited:    # only EXIT on a low score we can trust
        v = "EXIT"
    return v


def classify_style(b):
    nis = [r["net_income"] for r in b.annual if r.get("net_income") is not None]
    if len(nis) >= 3 and sum(1 for x in nis[-5:] if x is not None and x < 0) >= 2:
        return "speculative"
    dps = None
    for r in reversed(b.annual):
        if r.get("dividend_per_share") is not None:
            dps = r["dividend_per_share"]
            break
    yld = (dps / b.latest_price) if (dps and b.latest_price) else None
    g = b.ni_cagr
    if yld is not None and yld >= 0.04 and g is not None and g >= 0.10:
        return "both"
    if yld is not None and yld >= 0.05:
        return "dividend"
    if g is not None and g >= 0.15 and (yld is None or yld < 0.04):
        return "growth"
    if b.sector in CYCLICAL_SECTORS:
        return "cyclical"
    if g is not None:
        return "growth" if g > 0 else "cyclical"
    return None  # undeterminable (e.g. single-quarter bank) -- no wrong label


def score_pillars(b, universe):
    return {
        "business_quality": score_business_quality(b, universe),
        "financial_health": score_financial_health(b),
        "valuation": score_valuation(b, universe),
        "catalysts": score_catalysts(b),
    }


def score_stock(b, pillars):
    composite, n_pillars = compute_composite(pillars)
    val, fh = pillars.get("valuation"), pillars.get("financial_health")

    iv = mos = None
    vic = _component(val, "intrinsic")
    if vic and vic.score is not None:
        iv, mos = vic.inputs.get("fair_value"), vic.inputs.get("margin_of_safety")

    risk = []
    if val is None or val.score is None:
        risk.append("no_valuation")
    if fh and any("LIMITED_DATA" in n for n in fh.notes):
        risk.append("limited_data")
    lev = _component(fh, "leverage")
    if lev and "D/E>5x" in (lev.rationale or ""):
        risk.append("high_leverage_de5")
    if vic and "value trap" in (vic.rationale or ""):
        risk.append("value_trap")

    verdict = map_verdict(composite, mos, set(risk))
    flags = {
        "verdict": verdict,
        "style": classify_style(b),
        "is_shariah_compliant": b.is_shariah_compliant,
        "risk_flags": risk,
        "n_pillars": n_pillars,
        "archetype": b.archetype.value,
    }
    return StockScoreResult(
        ticker=b.ticker,
        business_quality=pillars["business_quality"].score if pillars.get("business_quality") else None,
        financial_health=fh.score if fh else None,
        valuation=val.score if val else None,
        catalysts=pillars["catalysts"].score if pillars.get("catalysts") else None,
        composite=composite, intrinsic_value_pkr=iv, margin_of_safety=mos,
        flags=flags, model_version=MODEL_VERSION,
    )


def score_universe(universe):
    """Return {ticker: (StockScoreResult, pillars)} for every covered stock."""
    out = {}
    for b in universe:
        pillars = score_pillars(b, universe)
        out[b.ticker] = (score_stock(b, pillars), pillars)
    return out
