"""
Robust cross-sectional statistics for peer (sector) comparison.

A veteran never compares a company to a *mean* — one outlier (a single
loss-making cyclical, a bank with a one-off) drags the average and lies.
We use median + MAD (median absolute deviation) and winsorize tails, so a
single broken peer can't distort a sector z-score.
"""

from __future__ import annotations

from statistics import median


def clean(values: list[float | None]) -> list[float]:
    """Drop None / NaN, keep finite numbers."""
    out: list[float] = []
    for v in values:
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f == f and f not in (float("inf"), float("-inf")):  # NaN/inf guard
            out.append(f)
    return out


def med(values: list[float | None]) -> float | None:
    xs = clean(values)
    return median(xs) if xs else None


def mad(values: list[float | None]) -> float | None:
    """Median absolute deviation, scaled to be ~comparable to std-dev."""
    xs = clean(values)
    if len(xs) < 2:
        return None
    m = median(xs)
    deviations = [abs(x - m) for x in xs]
    return 1.4826 * median(deviations)  # 1.4826 makes MAD ≈ σ for normal data


def robust_z(value: float | None, peers: list[float | None]) -> float | None:
    """Robust z-score of `value` within its peer cohort. Clamped to [-3, 3]."""
    if value is None:
        return None
    xs = clean(peers)
    if len(xs) < 3:
        return None
    m = median(xs)
    spread = mad(xs)
    if not spread:
        return 0.0
    z = (float(value) - m) / spread
    return max(-3.0, min(3.0, z))


def winsorize(values: list[float], p: float = 0.05) -> list[float]:
    """Clip the extreme p tails to the p / (1-p) percentiles."""
    xs = sorted(clean(values))
    if len(xs) < 5:
        return xs
    lo = xs[int(p * (len(xs) - 1))]
    hi = xs[int((1 - p) * (len(xs) - 1))]
    return [min(max(x, lo), hi) for x in xs]


def percentile_rank(value: float | None, peers: list[float | None]) -> float | None:
    """Fraction of peers strictly below `value`, in [0, 1]."""
    if value is None:
        return None
    xs = clean(peers)
    if not xs:
        return None
    below = sum(1 for x in xs if x < float(value))
    return below / len(xs)
