"""
Period algebra for the scoring engine.

Our fundamentals use cumulative fiscal buckets (Q1/H1/9M/FY) per
fundamentals/models.py. This module turns that raw series into the things an
analyst actually reasons about: ordering, standalone quarters (by
subtraction), trailing-twelve-months, and CAGR — all with honest None-returns
when the data can't support the calculation (no silent fabrication).
"""

from __future__ import annotations

# Cumulative coverage of each bucket, from fiscal-year start.
KIND_MONTHS: dict[str, int] = {"Q1": 3, "H1": 6, "9M": 9, "FY": 12}
# Sort order within a fiscal year.
KIND_ORDER: dict[str, int] = {"Q1": 1, "H1": 2, "9M": 3, "FY": 4}
# Factor to annualize a cumulative bucket (crude — flagged loudly when used).
ANNUALIZE_FACTOR: dict[str, float] = {"Q1": 4.0, "H1": 2.0, "9M": 4.0 / 3.0, "FY": 1.0}


def parse_period(period: str) -> tuple[int, str] | None:
    """'2026-9M' -> (2026, '9M'); returns None if unparseable."""
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


def sort_key(period: str) -> tuple[int, int]:
    """Chronological sort key: (fiscal_year, kind_order). Latest sorts last."""
    p = parse_period(period)
    return (p[0], KIND_ORDER[p[1]]) if p else (0, 0)


def cagr(begin: float | None, end: float | None, years: float) -> float | None:
    """Compound annual growth rate over `years`.

    Returns None when CAGR is mathematically meaningless:
      - missing endpoints
      - non-positive start (can't compound off zero/negative)
      - non-positive end (a swing into loss — caller should report sign, not a rate)
      - years <= 0
    This is deliberate: a fabricated CAGR off a negative base is worse than
    'unknown'. Growth scoring falls back to absolute-change sign when None.
    """
    if begin is None or end is None or years is None or years <= 0:
        return None
    if begin <= 0 or end <= 0:
        return None
    return (end / begin) ** (1.0 / years) - 1.0


def annualize(value: float | None, kind: str) -> float | None:
    """Scale a cumulative bucket to a full-year figure (crude; flag when used)."""
    if value is None or kind not in ANNUALIZE_FACTOR:
        return None
    return value * ANNUALIZE_FACTOR[kind]


def standalone_from_cumulative(
    cumulative_by_kind: dict[str, float | None]
) -> dict[str, float | None]:
    """Derive standalone quarter flows from cumulative buckets, by subtraction.

    Input keys are kinds present for ONE fiscal year, e.g.
        {'Q1': q1, 'H1': h1, '9M': nine, 'FY': fy}
    Output:
        Q1s = Q1
        Q2s = H1 - Q1
        Q3s = 9M - H1
        Q4s = FY - 9M
    Only emits a standalone value when both needed cumulatives are present.
    """
    g = cumulative_by_kind.get
    out: dict[str, float | None] = {}
    if g("Q1") is not None:
        out["Q1s"] = g("Q1")
    if g("H1") is not None and g("Q1") is not None:
        out["Q2s"] = g("H1") - g("Q1")
    if g("9M") is not None and g("H1") is not None:
        out["Q3s"] = g("9M") - g("H1")
    if g("FY") is not None and g("9M") is not None:
        out["Q4s"] = g("FY") - g("9M")
    return out
