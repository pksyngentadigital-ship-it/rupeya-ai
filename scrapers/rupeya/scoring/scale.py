"""Scoring scale helpers -- raw ratio -> 0-5 sub-score via piecewise-linear anchors."""

from __future__ import annotations


def clamp(x, lo=0.0, hi=5.0):
    return max(lo, min(hi, x))


def piecewise(value, anchors):
    """Linear interpolation of value across (x, score) anchors. None-safe.

    Below lowest x -> lowest score; above highest -> highest score, clamped 0-5.
    """
    if value is None:
        return None
    pts = sorted(set(anchors))
    if value <= pts[0][0]:
        return clamp(pts[0][1])
    if value >= pts[-1][0]:
        return clamp(pts[-1][1])
    for i in range(len(pts) - 1):
        x0, s0 = pts[i]
        x1, s1 = pts[i + 1]
        if x0 <= value <= x1:
            t = (value - x0) / (x1 - x0) if x1 > x0 else 0.0
            return clamp(s0 + t * (s1 - s0))
    return clamp(pts[-1][1])
