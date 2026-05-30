"""
Pillar 1 -- Business Quality (composite weight 30%).

Blueprint 4.1: moat, industry attractiveness, management, earnings durability.
We never fabricate a moat we can't see, so the mapping is data-honest:

  * earnings_durability (REAL): net-income volatility + positive-year streak.
  * industry_attractiveness (REAL): the stock's SECTOR's aggregate real growth +
    profitability, computed across the universe (sectors are not equal).
  * moat (PROXY, flagged): market leadership (mcap rank in sector) + return
    persistence (ROE above cost of equity, rich subset). A proxy, not direct
    market-share / brand data.
  * management: NO governance data (promoter holding / related-party / audit) ->
    not scored, flagged, so it never silently inflates the score.

Conviction-weighted like the other pillars.
"""

from __future__ import annotations

import statistics

from . import macro
from .scale import piecewise, clamp
from .stats import med, percentile_rank
from .types import Coverage, ScoreComponent, PillarResult

PILLAR_WEIGHT = 0.30
SUBFACTOR_WEIGHTS = {"earnings_durability": 0.45, "industry_attractiveness": 0.35, "moat": 0.20}
CORE = ["earnings_durability", "industry_attractiveness", "moat"]
NEUTRAL_PRIOR = 2.5

POS_FRAC_ANCHORS = [(0.5, 0.5), (0.6, 1.5), (0.8, 3.5), (1.0, 5.0)]
GROWTHVOL_ANCHORS = [(0.1, 5.0), (0.3, 3.5), (0.6, 2.0), (1.0, 0.5)]  # low vol = durable
SECTOR_GROWTH_ANCHORS = [(-0.05, 1.0), (0.0, 2.5), (0.03, 3.5), (0.06, 4.5), (0.10, 5.0)]
LEAD_ANCHORS = [(0.0, 2.0), (0.5, 3.0), (0.8, 4.0), (1.0, 5.0)]
PERSIST_ANCHORS = [(0.5, 1.5), (1.0, 3.0), (1.5, 4.5), (2.0, 5.0)]
PLAUSIBLE_ROE = 0.60  # exclude data-artefact ROEs from sector stats / persistence


def build_sector_context(universe):
    """Per-sector aggregates: median real NI growth and median ROE."""
    by_sec = {}
    for b in universe:
        by_sec.setdefault(b.sector or "?", []).append(b)
    ctx = {}
    for sec, members in by_sec.items():
        growths = [macro.real_growth(m.ni_cagr) for m in members if m.ni_cagr is not None]
        roes = []
        for m in members:
            snap = m.bs_snapshot or {}
            if snap.get("book_value") and m.ttm_ni:
                roe = m.ttm_ni / snap["book_value"]
                if 0 < roe < PLAUSIBLE_ROE:
                    roes.append(roe)
        ctx[sec] = {"real_growth": med(growths), "roe": med(roes), "n": len(members)}
    return ctx


def _sector_ctx(universe):
    if not hasattr(universe, "_bq_ctx"):
        universe._bq_ctx = build_sector_context(universe)
    return universe._bq_ctx


def _durability(b):
    nis = [r["net_income"] for r in b.annual if r.get("net_income") is not None]
    if len(nis) < 3:
        return ScoreComponent("earnings_durability", None, SUBFACTOR_WEIGHTS["earnings_durability"],
                              Coverage.NONE, rationale="need >=3 annual NI points")
    pos = sum(1 for x in nis if x > 0)
    pos_score = piecewise(pos / len(nis), POS_FRAC_ANCHORS)
    growths = [nis[i] / nis[i - 1] - 1 for i in range(1, len(nis)) if nis[i - 1] and nis[i - 1] > 0]
    if len(growths) >= 2:
        vol = statistics.pstdev(growths)
        score = 0.5 * pos_score + 0.5 * piecewise(vol, GROWTHVOL_ANCHORS)
        rat = "positive %d/%d yrs, NI-growth vol %.0f%%" % (pos, len(nis), vol * 100)
        inputs = {"positive_years": pos, "total_years": len(nis), "growth_vol": round(vol, 3)}
    else:
        vol, score = None, pos_score
        rat = "positive %d/%d yrs" % (pos, len(nis))
        inputs = {"positive_years": pos, "total_years": len(nis)}
    cov = Coverage.FULL if len(nis) >= 4 else Coverage.PARTIAL
    return ScoreComponent("earnings_durability", round(score, 2),
                          SUBFACTOR_WEIGHTS["earnings_durability"], cov, inputs,
                          threshold="positive-year fraction + NI-growth volatility", rationale=rat)


def _industry(b, ctx):
    c = ctx.get(b.sector or "?")
    if not c:
        return ScoreComponent("industry_attractiveness", None,
                              SUBFACTOR_WEIGHTS["industry_attractiveness"], Coverage.NONE,
                              rationale="no sector aggregates")
    coe = macro.discount_rate(1.0)
    parts, bits = [], []
    if c["real_growth"] is not None:
        parts.append(piecewise(c["real_growth"], SECTOR_GROWTH_ANCHORS))
        bits.append("real growth %.1f%%" % (c["real_growth"] * 100))
    if c["roe"] is not None:
        parts.append(piecewise(c["roe"], [(0.05, 1.0), (macro.RISK_FREE, 2.0), (coe, 3.5), (coe + 0.1, 5.0)]))
        bits.append("ROE %.0f%%" % (c["roe"] * 100))
    if not parts:
        return ScoreComponent("industry_attractiveness", None,
                              SUBFACTOR_WEIGHTS["industry_attractiveness"], Coverage.NONE,
                              rationale="no sector growth/ROE signal")
    cov = Coverage.FULL if len(parts) == 2 else Coverage.PARTIAL
    return ScoreComponent("industry_attractiveness", round(sum(parts) / len(parts), 2),
                          SUBFACTOR_WEIGHTS["industry_attractiveness"], cov,
                          inputs={"sector": b.sector, "sector_real_growth": c["real_growth"],
                                  "sector_roe": c["roe"], "sector_n": c["n"]},
                          threshold="sector aggregate real-growth + ROE",
                          rationale="%s sector: %s" % (b.sector, ", ".join(bits)))


def _moat(b, universe):
    signals, bits = [], []
    peers = [p for p in universe.sector_peers(b.ticker, include_self=True) if p.market_cap]
    if b.market_cap and len(peers) >= 3:
        pr = percentile_rank(b.market_cap, [p.market_cap for p in peers])
        signals.append(piecewise(pr, LEAD_ANCHORS))
        bits.append("size rank %.0f%% in sector" % (pr * 100))
    snap = b.bs_snapshot or {}
    if snap.get("book_value") and b.ttm_ni:
        roe = b.ttm_ni / snap["book_value"]
        if 0 < roe < PLAUSIBLE_ROE:
            signals.append(piecewise(roe / macro.discount_rate(1.0), PERSIST_ANCHORS))
            bits.append("ROE %.0fx cost-of-equity" % (roe / macro.discount_rate(1.0)))
    if not signals:
        return ScoreComponent("moat", None, SUBFACTOR_WEIGHTS["moat"], Coverage.NONE,
                              rationale="no moat proxy available")
    return ScoreComponent("moat", round(sum(signals) / len(signals), 2),
                          SUBFACTOR_WEIGHTS["moat"], Coverage.PARTIAL,
                          inputs={"signals": len(signals)},
                          threshold="PROXY: mcap leadership + ROE persistence (no direct moat data)",
                          rationale="proxy (" + ", ".join(bits) + ")")


def _management():
    return ScoreComponent("management", None, 0.0, Coverage.NONE,
                          rationale="no governance data (promoter/related-party/audit) -- not scored")


def score_business_quality(b, universe):
    ctx = _sector_ctx(universe)
    comps = {c.name: c for c in (_durability(b), _industry(b, ctx), _moat(b, universe), _management())}
    present_core = [comps[n] for n in CORE if comps[n].score is not None]
    if not present_core:
        return PillarResult("business_quality", None, PILLAR_WEIGHT, Coverage.NONE,
                            list(comps.values()), notes=["no feedable business-quality inputs"])
    wsum = sum(c.weight for c in present_core)
    raw = sum(c.score * c.weight for c in present_core) / wsum
    coverage_ratio = len(present_core) / len(CORE)
    final = round(clamp(NEUTRAL_PRIOR + coverage_ratio * (raw - NEUTRAL_PRIOR)), 2)
    cov = (Coverage.FULL if coverage_ratio >= 0.99
           else Coverage.PARTIAL if coverage_ratio > 0 else Coverage.NONE)
    notes = ["%d/%d core sub-factors (management: no data)" % (len(present_core), len(CORE)),
             "conviction-adj: raw %.2f x conf %.2f -> %.2f" % (raw, coverage_ratio, final)]
    return PillarResult("business_quality", final, PILLAR_WEIGHT, cov, list(comps.values()), notes)
