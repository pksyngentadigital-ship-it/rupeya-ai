"""
Pillar 4 -- News & Catalysts (composite weight 15%).

Blueprint 4.4: earnings surprise, regulatory news, corporate actions, macro.
The news_items pipeline (B3b) isn't built, so regulatory/news sentiment is
unavailable and stays flagged. What we CAN compute honestly today:

  * earnings_surprise: latest annual earnings vs the stock's own trend
    (acceleration = positive catalyst, deceleration = negative)
  * macro_catalyst: the current rate REGIME applied as a sector tilt. In the
    Apr-2026 tightening (policy 11.5%), banks/insurers benefit (NIM, investment
    income) and leveraged cyclicals (cement/auto/textile/power) face a headwind.
  * corporate_actions: dividend trend (raised / held / cut) where we have payouts
  * regulatory_news: N/A until B3b -- never fabricated.

Conviction-weighted: with only ~2 of 4 inputs, most stocks sit near neutral,
which is the honest state of our catalyst signal pre-B3b.
"""

from __future__ import annotations

from .scale import piecewise, clamp
from .periods import parse_period
from .types import Coverage, ScoreComponent, PillarResult

PILLAR_WEIGHT = 0.15
SUBFACTOR_WEIGHTS = {"earnings_surprise": 0.30, "macro_catalyst": 0.25,
                     "corporate_actions": 0.20, "regulatory_news": 0.25}
CORE = ["earnings_surprise", "macro_catalyst", "corporate_actions", "regulatory_news"]
NEUTRAL_PRIOR = 2.5

# See macro.AS_OF: SBP tightening (policy 11.5%, CPI double digit).
RATE_REGIME = "tightening"
SECTOR_RATE_SCORE = {
    "Commercial Banks": 4.0, "Insurance": 3.5,
    "Oil & Gas Exploration": 3.5,            # USD-linked revenue, low leverage
    "Fertilizer": 3.0, "Pharmaceutical": 3.0, "Food & Personal Care": 3.0,
    "Technology & Communication": 3.0, "Conglomerate": 3.0,
    "Chemical": 2.5, "Transport": 2.5,
    "Cement": 2.0, "Automobile Assembler": 2.0, "Auto Parts & Accessories": 2.0,
    "Engineering": 2.0, "Textile": 2.0, "Power": 2.0,
    "Oil & Gas Marketing": 2.0, "Refinery": 2.0, "Real Estate": 2.0,
}
DEFAULT_RATE_SCORE = 2.8
SURPRISE_ANCHORS = [(-0.30, 1.0), (-0.10, 2.0), (0.0, 3.0), (0.10, 4.0), (0.30, 5.0)]


def _earnings_surprise(b):
    nis = [r["net_income"] for r in b.annual if r.get("net_income") is not None]
    if len(nis) < 3 or b.ni_cagr is None or not nis[-2] or nis[-2] <= 0:
        return ScoreComponent("earnings_surprise", None, SUBFACTOR_WEIGHTS["earnings_surprise"],
                              Coverage.NONE, rationale="not enough earnings history for momentum")
    latest_yoy = nis[-1] / nis[-2] - 1
    accel = latest_yoy - b.ni_cagr
    return ScoreComponent("earnings_surprise", round(piecewise(accel, SURPRISE_ANCHORS), 2),
                          SUBFACTOR_WEIGHTS["earnings_surprise"], Coverage.FULL,
                          inputs={"latest_yoy": round(latest_yoy, 4), "trend": round(b.ni_cagr, 4),
                                  "acceleration": round(accel, 4)},
                          threshold="latest YoY NI vs trend; +10% accel=4.0",
                          rationale="latest YoY %+.0f%% vs trend %+.0f%% (accel %+.0f%%)" % (
                              latest_yoy * 100, b.ni_cagr * 100, accel * 100))


def _macro_catalyst(b):
    score = SECTOR_RATE_SCORE.get(b.sector or "", DEFAULT_RATE_SCORE)
    tilt = "tailwind" if score >= 3.5 else "headwind" if score <= 2.2 else "neutral"
    return ScoreComponent("macro_catalyst", float(score), SUBFACTOR_WEIGHTS["macro_catalyst"],
                          Coverage.FULL,
                          inputs={"regime": RATE_REGIME, "sector": b.sector},
                          threshold="rate regime -> sector tilt",
                          rationale="%s regime: %s -> %s" % (RATE_REGIME, b.sector, tilt))


def _corporate_actions(b):
    series = [(parse_period(r["period"])[0], r["dividend_per_share"])
              for r in b.annual if r.get("dividend_per_share") is not None]
    if len(series) < 2:
        return ScoreComponent("corporate_actions", None, SUBFACTOR_WEIGHTS["corporate_actions"],
                              Coverage.NONE, rationale="no dividend history")
    series.sort()
    last, prev = series[-1][1], series[-2][1]
    if last == 0 and prev > 0:
        score, action = 1.0, "dividend suspended"
    elif last > prev * 1.05:
        score, action = 4.0, "dividend raised"
    elif last < prev * 0.95:
        score, action = 1.5, "dividend cut"
    else:
        score, action = 3.0, "dividend held"
    return ScoreComponent("corporate_actions", float(score), SUBFACTOR_WEIGHTS["corporate_actions"],
                          Coverage.FULL, inputs={"last_dps": last, "prev_dps": prev},
                          threshold="dividend trend", rationale=action)


def _regulatory():
    return ScoreComponent("regulatory_news", None, SUBFACTOR_WEIGHTS["regulatory_news"],
                          Coverage.NONE, rationale="no news/regulatory feed (pending B3b pipeline)")


def score_catalysts(b):
    comps = {c.name: c for c in (_earnings_surprise(b), _macro_catalyst(b),
                                 _corporate_actions(b), _regulatory())}
    present = [comps[n] for n in CORE if comps[n].score is not None]
    if not present:
        return PillarResult("catalysts", None, PILLAR_WEIGHT, Coverage.NONE, list(comps.values()),
                            notes=["no feedable catalyst inputs"])
    wsum = sum(c.weight for c in present)
    raw = sum(c.score * c.weight for c in present) / wsum
    coverage_ratio = len(present) / len(CORE)
    final = round(clamp(NEUTRAL_PRIOR + coverage_ratio * (raw - NEUTRAL_PRIOR)), 2)
    cov = (Coverage.FULL if coverage_ratio >= 0.99
           else Coverage.PARTIAL if coverage_ratio > 0 else Coverage.NONE)
    notes = ["%d/%d inputs (regulatory/news pending B3b)" % (len(present), len(CORE)),
             "conviction-adj: raw %.2f x conf %.2f -> %.2f" % (raw, coverage_ratio, final)]
    return PillarResult("catalysts", final, PILLAR_WEIGHT, cov, list(comps.values()), notes)
