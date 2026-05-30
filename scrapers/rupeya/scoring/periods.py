"""
Period algebra for the scoring engine.

Cumulative fiscal buckets (Q1/H1/9M/FY) -> the things an analyst reasons about:
ordering, standalone quarters (by subtraction), trailing-twelve-months, and
robust growth -- with honest None-returns when data can't support a calc.
"""

from __future__ import annotations

import math

KIND_MONTHS = {"Q1": 3, "H1": 6, "9M": 9, "FY": 12}
KIND_ORDER = {"Q1": 1, "H1": 2, "9M": 3, "FY": 4}
ANNUALIZE_FACTOR = {"Q1": 4.0, "H1": 2.0, "9M": 4.0 / 3.0, "FY": 1.0}


def parse_period(period):
    """'2026-9M' -> (2026, '9M'); None if unparseable."""
    if not period or "-" not in period:
        return None
    year_s, kind = period.split("-", 1)
    kind = kind.upper()
    if kind not in KIND_ORDER:
        return None
    try:
        return int(year_s), kind
    except ValueError:
        return None


def sort_key(period):
    """Chronological sort key: (fiscal_year, kind_order)."""
    p = parse_period(period)
    return (p[0], KIND_ORDER[p[1]]) if p else (0, 0)


def cagr(begin, end, years):
    """Compound annual growth rate; None if meaningless (non-positive base/end)."""
    if begin is None or end is None or years is None or years <= 0:
        return None
    if begin <= 0 or end <= 0:
        return None
    return (end / begin) ** (1.0 / years) - 1.0


def trend_growth(points):
    """Robust annual growth from a (year, value) series. Returns (rate, span_years).

    Fits a log-linear trend (least-squares of ln(value) vs year) over all
    positive points, so a single low-base/COVID-dip endpoint can't distort the
    rate the way naive first-to-last CAGR does. Falls back to two-point CAGR
    when only two positive points exist; None when fewer than two. Non-positive
    (loss) years are dropped since ln() is undefined.
    """
    pts = sorted((x, float(v)) for x, v in points if v is not None and v > 0)
    if len(pts) < 2:
        return None, None
    span = float(pts[-1][0] - pts[0][0])
    if len(pts) == 2:
        x0, v0 = pts[0]
        x1, v1 = pts[1]
        n = x1 - x0
        if n <= 0:
            return None, span
        return (v1 / v0) ** (1.0 / n) - 1.0, span
    count = len(pts)
    mean_x = sum(x for x, _ in pts) / count
    mean_y = sum(math.log(v) for _, v in pts) / count
    sxx = sum((x - mean_x) ** 2 for x, _ in pts)
    sxy = sum((x - mean_x) * (math.log(v) - mean_y) for x, v in pts)
    if sxx == 0:
        return None, span
    slope = sxy / sxx
    return math.exp(slope) - 1.0, span


def annualize(value, kind):
    """Scale a cumulative bucket to a full-year figure (crude; flag when used)."""
    if value is None or kind not in ANNUALIZE_FACTOR:
        return None
    return value * ANNUALIZE_FACTOR[kind]


def standalone_from_cumulative(cumulative_by_kind):
    """Standalone quarter flows from cumulative buckets, by subtraction."""
    g = cumulative_by_kind.get
    out = {}
    if g("Q1") is not None:
        out["Q1s"] = g("Q1")
    if g("H1") is not None and g("Q1") is not None:
        out["Q2s"] = g("H1") - g("Q1")
    if g("9M") is not None and g("H1") is not None:
        out["Q3s"] = g("9M") - g("H1")
    if g("FY") is not None and g("9M") is not None:
        out["Q4s"] = g("FY") - g("9M")
    return out
