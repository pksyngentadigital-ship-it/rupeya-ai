"""
Pillar 2 -- Financial Health (composite weight 30%).

Blueprint 4.2: Growth, Returns, Leverage, Cash generation. Growth judged in
REAL terms from split-immune NI/revenue; ROE anchored to the cost of equity
(moves with the macro regime); applicability is archetype-aware (a bank is not
graded on industrial D/E).

CONVICTION WEIGHTING (the key discipline): a raw pillar score is shrunk toward
a neutral prior in proportion to how little we actually know --
    final = NEUTRAL + confidence * (raw - NEUTRAL),  confidence = data coverage.
So a stock scored on 1 of 4 sub-factors can't claim a 5.0 and outrank a fully
analysed peer; thin data pulls toward the middle. Plus hard sanity guards on
implausible ROE and single-quarter annualisations. Nothing fabricated -- absent
inputs score None, not zero.
"""

from __future__ import annotations

from . import macro
from .scale import piecewise, clamp
from .types import Archetype, Coverage, ScoreComponent, PillarResult
from .periods import parse_period

PILLAR_WEIGHT = 0.30
SUBFACTOR_WEIGHTS = {"growth": 0.30, "returns": 0.30, "leverage": 0.20, "cashflow": 0.20}
APPLICABLE = {
    Archetype.NON_FINANCIAL: ["growth", "returns", "leverage", "cashflow"],
    Archetype.BANK: ["growth", "returns"],
    Archetype.INSURANCE: ["growth", "returns"],
}
GROWTH_ANCHORS = [(-0.15, 0.5), (-0.05, 1.5), (0.0, 2.5), (0.05, 3.5), (0.10, 4.5), (0.20, 5.0)]
GROWTH_REAL_CAP = 0.25
EXTREME_NOMINAL = 0.40
LEVERAGE_ANCHORS = [(-0.20, 5.0), (0.0, 4.5), (0.5, 3.5), (1.0, 2.5), (2.0, 1.5), (3.0, 0.5), (5.0, 0.0)]
CASH_ANCHORS = [(-0.5, 0.5), (0.0, 1.5), (0.5, 3.0), (0.8, 4.0), (1.0, 4.7), (1.5, 5.0)]
CIRCULAR_DEBT_SECTORS = {"Power", "Oil & Gas Marketing", "Refinery"}

NEUTRAL_PRIOR = 2.5          # what we assume in the absence of evidence
IMPLAUSIBLE_ROE = 0.60       # data-error guard; genuine high-ROE payers (e.g. FFC ~54%) are real -- annualised-quarter artifacts are caught separately by the confidence haircut
ANNUALIZED_CONFIDENCE = 0.5  # extra confidence haircut when TTM is a single annualised quarter


def _growth(b):
    rev_r = macro.real_growth(b.revenue_cagr) if b.revenue_cagr is not None else None
    ni_r = macro.real_growth(b.ni_cagr) if b.ni_cagr is not None else None
    if rev_r is None and ni_r is None:
        return ScoreComponent("growth", None, SUBFACTOR_WEIGHTS["growth"], Coverage.NONE,
                              rationale="no multi-year revenue or net-income history")
    blended = 0.6 * ni_r + 0.4 * rev_r if (rev_r is not None and ni_r is not None) \
        else (ni_r if ni_r is not None else rev_r)
    nominals = [x for x in (b.revenue_cagr, b.ni_cagr) if x is not None]
    flag = ""
    if nominals and max(nominals) > EXTREME_NOMINAL:
        flag = "nominal CAGR %.0f%% likely M&A/low-base/rate-cycle -- credit capped" % (max(nominals) * 100)
    score = piecewise(min(blended, GROWTH_REAL_CAP), GROWTH_ANCHORS)
    years = b.ni_cagr_years or b.revenue_cagr_years
    cov = Coverage.FULL if (years or 0) >= 4 else Coverage.PARTIAL
    rat = "real growth ~%.1f%%/yr over %sy" % (blended * 100, ("%g" % years) if years else "?")
    if flag:
        rat += "; " + flag
    return ScoreComponent("growth", score, SUBFACTOR_WEIGHTS["growth"], cov,
                          inputs={"revenue_cagr": b.revenue_cagr, "ni_cagr": b.ni_cagr,
                                  "real_blended": round(blended, 4), "years": years},
                          threshold="real blended CAGR (NI 60/rev 40) vs CPI; 0%=2.5,+10%=4.5",
                          rationale=rat)


def _returns(b):
    snap = b.bs_snapshot or {}
    bv = snap.get("book_value")
    if not bv or not b.ttm_ni:
        return ScoreComponent("returns", None, SUBFACTOR_WEIGHTS["returns"], Coverage.NONE,
                              rationale="no book value / earnings")
    roe = b.ttm_ni / bv
    coe = macro.discount_rate(1.0)
    rf = macro.RISK_FREE
    anchors = [(0.0, 0.5), (0.05, 1.0), (rf, 2.0), (coe, 3.0), (coe + 0.06, 4.0), (coe + 0.12, 4.8), (0.40, 5.0)]
    score = piecewise(roe, anchors)
    extra = []
    cov = Coverage.FULL
    if b.archetype == Archetype.NON_FINANCIAL and snap.get("debt"):
        de = snap["debt"] / bv
        if de > 2.0:
            score = min(score, 3.5)
            extra.append("ROE may be leverage-inflated (D/E %.1f)" % de)
    if roe > IMPLAUSIBLE_ROE:
        score = min(score, 3.5)
        cov = Coverage.PARTIAL
        extra.append("ROE %.0f%% implausible (one-off/annualisation/data) -- capped" % (roe * 100))
    stale = 0
    if b.latest_row and snap.get("period"):
        stale = parse_period(b.latest_row["period"])[0] - parse_period(snap["period"])[0]
        if stale >= 2:
            cov = Coverage.PARTIAL
    rat = "ROE %.1f%%" % (roe * 100)
    if stale >= 2:
        rat += ", equity %dy stale" % stale
    if extra:
        rat += "; " + "; ".join(extra)
    return ScoreComponent("returns", round(score, 2), SUBFACTOR_WEIGHTS["returns"], cov,
                          inputs={"roe": round(roe, 4), "cost_of_equity": round(coe, 4), "risk_free": rf,
                                  "equity_period": snap.get("period"), "equity_stale_years": stale},
                          threshold="ROE vs cost of equity (%.1f%%)=3.0, vs PIB (%.1f%%)=2.0" % (coe * 100, rf * 100),
                          rationale=rat)


def _leverage(b):
    if b.archetype != Archetype.NON_FINANCIAL:
        return ScoreComponent("leverage", None, SUBFACTOR_WEIGHTS["leverage"], Coverage.NONE,
                              rationale="not applicable to %s" % b.archetype.value)
    snap = b.bs_snapshot or {}
    debt, bv, cash = snap.get("debt"), snap.get("book_value"), snap.get("cash")
    if debt is None or not bv:
        return ScoreComponent("leverage", None, SUBFACTOR_WEIGHTS["leverage"], Coverage.NONE,
                              rationale="no debt / equity data")
    net_debt = debt - (cash or 0)
    nde = net_debt / bv
    score = piecewise(nde, LEVERAGE_ANCHORS)
    notes = []
    if debt / bv > 5.0:
        notes.append("D/E>5x (EXIT-flag candidate)")
    if b.sector in CIRCULAR_DEBT_SECTORS:
        notes.append("circular-debt-exposed sector")
    rat = "Net Debt/Equity %.2fx" % nde
    if notes:
        rat += "; " + ", ".join(notes)
    return ScoreComponent("leverage", round(score, 2), SUBFACTOR_WEIGHTS["leverage"], Coverage.FULL,
                          inputs={"debt": debt, "cash": cash, "equity": bv,
                                  "net_debt_to_equity": round(nde, 3), "gross_de": round(debt / bv, 3)},
                          threshold="Net Debt/Equity: net-cash=5.0, 1.0x=2.5, 3.0x=0.5",
                          rationale=rat)


def _cashflow(b):
    if b.archetype != Archetype.NON_FINANCIAL:
        return ScoreComponent("cashflow", None, SUBFACTOR_WEIGHTS["cashflow"], Coverage.NONE,
                              rationale="not applicable to %s" % b.archetype.value)
    fcf = fcf_period = None
    for r in reversed(b.rows):
        if r.get("fcf") is not None:
            fcf, fcf_period = r["fcf"], r["period"]
            break
    if fcf is None or not b.ttm_ni:
        return ScoreComponent("cashflow", None, SUBFACTOR_WEIGHTS["cashflow"], Coverage.NONE,
                              rationale="no free-cash-flow data")
    ratio = fcf / b.ttm_ni
    return ScoreComponent("cashflow", round(piecewise(ratio, CASH_ANCHORS), 2),
                          SUBFACTOR_WEIGHTS["cashflow"], Coverage.FULL,
                          inputs={"fcf": fcf, "fcf_period": fcf_period, "ttm_ni": b.ttm_ni,
                                  "fcf_to_ni": round(ratio, 3)},
                          threshold="FCF/NI: >=1.0 high quality, 0.5=3.0, negative<=0.5",
                          rationale="FCF/NI %.2f (%s)" % (ratio, fcf_period))


def score_financial_health(b):
    comps = {c.name: c for c in (_growth(b), _returns(b), _leverage(b), _cashflow(b))}
    applicable = APPLICABLE[b.archetype]
    present = [comps[n] for n in applicable if comps[n].score is not None]
    n_app = len(applicable)
    if not present:
        return PillarResult("financial_health", None, PILLAR_WEIGHT, Coverage.NONE,
                            list(comps.values()),
                            notes=["no feedable financial-health inputs (archetype=%s)" % b.archetype.value])

    wsum = sum(c.weight for c in present)
    raw = sum(c.score * c.weight for c in present) / wsum

    coverage_ratio = len(present) / n_app
    confidence = coverage_ratio
    annualized = "annualized" in (b.ttm_basis or "")
    if annualized:
        confidence *= ANNUALIZED_CONFIDENCE
    final = round(clamp(NEUTRAL_PRIOR + confidence * (raw - NEUTRAL_PRIOR)), 2)

    cov = (Coverage.FULL if coverage_ratio >= 0.99
           else Coverage.PARTIAL if coverage_ratio > 0 else Coverage.NONE)
    notes = ["%d/%d applicable sub-factors (archetype=%s)" % (len(present), n_app, b.archetype.value),
             "conviction-adj: raw %.2f x conf %.2f -> %.2f" % (raw, confidence, final)]
    if coverage_ratio < 0.5:
        notes.append("LIMITED_DATA")
    if annualized:
        notes.append("single-quarter annualised TTM -- low confidence")
    if any(c.coverage == Coverage.PARTIAL for c in present):
        notes.append("some inputs low-confidence (short window / stale equity)")
    return PillarResult("financial_health", final, PILLAR_WEIGHT, cov, list(comps.values()), notes)
