"""
Pillar 3 -- Valuation (composite weight 25%).

DCF is not feasible (no cash-flow data + PSX's circular-debt/lumpy-capex noise
makes FCF a poor perpetuity base). So this is the HYBRID:

  Relative value drives the score --
    * earnings_yield: E/P vs the 10Y PIB bond (the core PSX cheap/dear lens)
    * multiples:      P/E vs sector peers (robust z), fallback to absolute P/E
  Absolute value gives the founder-facing number --
    * intrinsic:      Gordon perpetuity on EARNINGS -> intrinsic_value_pkr +
                      margin_of_safety (for the STRONG BUY gate). Terminal growth
                      = mean-reverting inflation + a small, capped real-growth
                      premium, discounted at the cost of equity. This anchors a
                      no-real-growth company near ~9x (1/(coe - terminal infl)),
                      NOT 5x -- a nominal discount rate must be paired with
                      nominal (inflation-bearing) growth, never zero.
  Plus a dividend bonus when we have payout data.

Earnings-based, clearly labelled, never a fabricated DCF. Conviction-weighted
like Financial Health; a cheap stock with falling earnings is flagged a possible
value trap (the quality pillars decide if the cheapness is deserved).
"""

from __future__ import annotations

from . import macro
from .scale import piecewise, clamp
from .stats import robust_z
from .types import Coverage, ScoreComponent, PillarResult

PILLAR_WEIGHT = 0.25
SUBFACTOR_WEIGHTS = {"earnings_yield": 0.35, "multiples": 0.30, "intrinsic": 0.20, "dividend": 0.15}

EY_ANCHORS = [(-0.06, 1.0), (-0.02, 2.0), (0.0, 3.0), (0.03, 4.0), (0.07, 4.7), (0.12, 5.0)]
REL_ANCHORS = [(-2.0, 1.0), (-1.0, 2.0), (0.0, 3.0), (1.0, 4.0), (2.0, 5.0)]
ABS_PE_ANCHORS = [(4.0, 5.0), (8.0, 4.0), (12.0, 3.0), (18.0, 2.0), (25.0, 1.0)]
MOS_ANCHORS = [(-0.5, 1.0), (-0.25, 2.0), (0.0, 3.0), (0.25, 4.0), (0.5, 4.7), (0.75, 5.0)]
DY_ANCHORS = [(0.0, 2.0), (0.03, 3.0), (0.06, 4.0), (0.09, 4.7), (0.12, 5.0)]

NEUTRAL_PRIOR = 2.5
ANNUALIZED_CONFIDENCE = 0.5
CORE = ["earnings_yield", "multiples", "intrinsic"]

# --- intrinsic value (Gordon on earnings) ---
TERMINAL_INFLATION = 0.08    # long-run nominal growth: between SBP ~6% target and current ~11% spike
REAL_GROWTH_CAP = 0.04       # most sustainable real growth credited in perpetuity
REAL_DECLINE_FLOOR = -0.06   # floor on real growth fed into terminal g
GORDON_SPREAD_FLOOR = 0.04   # keep (coe - g) >= this so the perpetuity can't blow up
PE_FLOOR, PE_CAP = 4.0, 15.0


def _pe(b):
    if b.latest_price and b.ttm_eps and b.ttm_eps > 0:
        return b.latest_price / b.ttm_eps
    return None


def _earnings_yield(b):
    if not b.latest_price or not b.ttm_eps or b.ttm_eps <= 0:
        return ScoreComponent("earnings_yield", None, SUBFACTOR_WEIGHTS["earnings_yield"],
                              Coverage.NONE, rationale="no positive earnings / price")
    ey = b.ttm_eps / b.latest_price
    spread = ey - macro.PIB_10Y_YIELD
    return ScoreComponent("earnings_yield", round(piecewise(spread, EY_ANCHORS), 2),
                          SUBFACTOR_WEIGHTS["earnings_yield"], Coverage.FULL,
                          inputs={"earnings_yield": round(ey, 4), "pib": macro.PIB_10Y_YIELD,
                                  "spread": round(spread, 4)},
                          threshold="E/P minus 10Y PIB; 0=3.0, +7%=4.7",
                          rationale="E/P %.1f%% vs PIB %.1f%% (spread %+.1f%%)" % (
                              ey * 100, macro.PIB_10Y_YIELD * 100, spread * 100))


def _multiples(b, universe):
    pe = _pe(b)
    if pe is None:
        return ScoreComponent("multiples", None, SUBFACTOR_WEIGHTS["multiples"],
                              Coverage.NONE, rationale="no positive P/E")
    peer_pes = [p for p in (_pe(pp) for pp in universe.sector_peers(b.ticker))
                if p is not None and 0 < p < 100]
    if len(peer_pes) < 3:
        return ScoreComponent("multiples", round(piecewise(pe, ABS_PE_ANCHORS), 2),
                              SUBFACTOR_WEIGHTS["multiples"], Coverage.PARTIAL,
                              inputs={"pe": round(pe, 1), "basis": "absolute (sector peers <3)"},
                              threshold="absolute P/E; 8x=4.0, 12x=3.0, 18x=2.0",
                              rationale="P/E %.1f (no sector cohort)" % pe)
    z = robust_z(pe, peer_pes)
    srt = sorted(peer_pes)
    med = srt[len(srt) // 2]
    return ScoreComponent("multiples", round(piecewise(-z, REL_ANCHORS), 2),
                          SUBFACTOR_WEIGHTS["multiples"], Coverage.FULL,
                          inputs={"pe": round(pe, 1), "sector_median_pe": round(med, 1),
                                  "z": round(z, 2), "n_peers": len(peer_pes)},
                          threshold="P/E z-score vs sector (cheaper=higher); median=3.0",
                          rationale="P/E %.1f vs sector median %.1f (z %+.2f, n=%d)" % (
                              pe, med, z, len(peer_pes)))


def _intrinsic(b):
    eps = b.ttm_eps
    if not b.latest_price or eps is None or eps <= 0:
        return ScoreComponent("intrinsic", None, SUBFACTOR_WEIGHTS["intrinsic"],
                              Coverage.NONE, rationale="no positive earnings to capitalise")
    coe = macro.discount_rate(1.0)
    real_g = macro.real_growth(b.ni_cagr) if b.ni_cagr is not None else 0.0
    real_used = min(max(real_g, REAL_DECLINE_FLOOR), REAL_GROWTH_CAP)
    g = min(TERMINAL_INFLATION + real_used, coe - GORDON_SPREAD_FLOOR)
    fair_pe = min(max(1.0 / (coe - g), PE_FLOOR), PE_CAP)
    fair_value = fair_pe * eps
    mos = (fair_value - b.latest_price) / fair_value
    score = piecewise(mos, MOS_ANCHORS)
    trap = mos >= 0.25 and b.ni_cagr is not None and b.ni_cagr < 0
    if trap:
        score = min(score, 3.0)
    rat = "fair ~Rs%.0f (PE %.1f, g %.1f%%) vs Rs%.2f -> MoS %+.0f%%" % (
        fair_value, fair_pe, g * 100, b.latest_price, mos * 100)
    if trap:
        rat += "; cheap but earnings declining -- possible value trap"
    return ScoreComponent("intrinsic", round(score, 2), SUBFACTOR_WEIGHTS["intrinsic"], Coverage.FULL,
                          inputs={"fair_value": round(fair_value, 2), "fair_pe": round(fair_pe, 1),
                                  "margin_of_safety": round(mos, 4), "terminal_growth": round(g, 4),
                                  "method": "Gordon on earnings (terminal g = mean-rev inflation + capped real)"},
                          threshold="margin of safety vs Gordon earnings value; 0=3.0,+25%=4.0",
                          rationale=rat)


def _dividend(b):
    dps = dps_period = None
    for r in reversed(b.rows):
        if r.get("dividend_per_share") is not None:
            dps, dps_period = r["dividend_per_share"], r["period"]
            break
    if not dps or not b.latest_price:
        return ScoreComponent("dividend", None, SUBFACTOR_WEIGHTS["dividend"],
                              Coverage.NONE, rationale="no dividend data")
    dy = dps / b.latest_price
    score = piecewise(dy, DY_ANCHORS)
    note = ""
    if b.ttm_eps and b.ttm_eps > 0:
        payout = dps / b.ttm_eps
        if payout > 1.0:
            score = min(score, 3.0)
            note = "; payout %.0f%% > earnings (unsustainable)" % (payout * 100)
        elif payout > 0.8:
            note = "; payout %.0f%% high" % (payout * 100)
    return ScoreComponent("dividend", round(score, 2), SUBFACTOR_WEIGHTS["dividend"], Coverage.FULL,
                          inputs={"dps": dps, "dps_period": dps_period, "dividend_yield": round(dy, 4)},
                          threshold="dividend yield; 3%=3.0, 6%=4.0, 9%=4.7",
                          rationale="yield %.1f%% (dps %s)" % (dy * 100, dps_period) + note)


def score_valuation(b, universe):
    comps = {c.name: c for c in (_earnings_yield(b), _multiples(b, universe),
                                 _intrinsic(b), _dividend(b))}
    present_core = [comps[n] for n in CORE if comps[n].score is not None]
    if not present_core:
        return PillarResult("valuation", None, PILLAR_WEIGHT, Coverage.NONE, list(comps.values()),
                            notes=["no feedable valuation inputs (no positive earnings/price)"])
    scoring = list(present_core)
    if comps["dividend"].score is not None:
        scoring.append(comps["dividend"])
    wsum = sum(c.weight for c in scoring)
    raw = sum(c.score * c.weight for c in scoring) / wsum

    coverage_ratio = len(present_core) / len(CORE)
    confidence = coverage_ratio
    annualized = "annualized" in (b.ttm_basis or "")
    if annualized:
        confidence *= ANNUALIZED_CONFIDENCE
    final = round(clamp(NEUTRAL_PRIOR + confidence * (raw - NEUTRAL_PRIOR)), 2)

    cov = (Coverage.FULL if coverage_ratio >= 0.99
           else Coverage.PARTIAL if coverage_ratio > 0 else Coverage.NONE)
    notes = ["%d/%d core sub-factors%s" % (len(present_core), len(CORE),
             " + dividend" if comps["dividend"].score is not None else ""),
             "conviction-adj: raw %.2f x conf %.2f -> %.2f" % (raw, confidence, final)]
    if annualized:
        notes.append("single-quarter annualised earnings -- low confidence")
    return PillarResult("valuation", final, PILLAR_WEIGHT, cov, list(comps.values()), notes)
