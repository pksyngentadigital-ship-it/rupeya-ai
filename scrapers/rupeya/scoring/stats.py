"""Robust cross-sectional stats for sector peer comparison (median/MAD, winsorize)."""

from __future__ import annotations

from statistics import median


def clean(values):
    out = []
    for v in values:
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f == f and f not in (float("inf"), float("-inf")):
            out.append(f)
    return out


def med(values):
    xs = clean(values)
    return median(xs) if xs else None


def mad(values):
    xs = clean(values)
    if len(xs) < 2:
        return None
    m = median(xs)
    return 1.4826 * median([abs(x - m) for x in xs])


def robust_z(value, peers):
    if value is None:
        return None
    xs = clean(peers)
    if len(xs) < 3:
        return None
    m = median(xs)
    spread = mad(xs)
    if not spread:
        return 0.0
    return max(-3.0, min(3.0, (float(value) - m) / spread))


def winsorize(values, p=0.05):
    xs = sorted(clean(values))
    if len(xs) < 5:
        return xs
    lo = xs[int(p * (len(xs) - 1))]
    hi = xs[int((1 - p) * (len(xs) - 1))]
    return [min(max(x, lo), hi) for x in xs]


def percentile_rank(value, peers):
    if value is None:
        return None
    xs = clean(peers)
    if not xs:
        return None
    return sum(1 for x in xs if x < float(value)) / len(xs)
