"""B4.2 verifier -- Valuation pillar on the live universe. Read-only.

Run from the scrapers folder with the venv active:
    rmdir /s /q rupeya\scoring\__pycache__
    python verify_valuation.py
"""

from __future__ import annotations

import collections

from rupeya.scoring import load_universe
from rupeya.scoring.valuation import score_valuation
from rupeya.scoring import macro


def s(x):
    return "%.2f" % x if x is not None else "  - "


def comp(r, name):
    return next(c for c in r.components if c.name == name)


def main():
    print("macro: PIB10Y=%.1f%% cost_of_equity=%.1f%% (no-growth fair P/E~%.1f)\n" % (
        macro.PIB_10Y_YIELD * 100, macro.discount_rate(1.0) * 100, 1.0 / (macro.discount_rate(1.0) - 0.08)))
    u = load_universe()
    results = {b.ticker: score_valuation(b, u) for b in u}

    samples = ["LUCK", "OGDC", "MARI", "MCB", "UBL", "FFC", "ENGRO", "HUBC",
               "PSO", "NESTLE", "SYS", "AGP"]
    print("=" * 82)
    print("SAMPLE -- Valuation (glass-box)  [fair value = conservative earnings-power, not DCF]")
    print("=" * 82)
    for t in samples:
        b, r = u.get(t), results.get(t)
        if not b or not r:
            print("\n%s: not in universe" % t)
            continue
        iv = comp(r, "intrinsic")
        mos = iv.inputs.get("margin_of_safety") if iv.score is not None else None
        fv = iv.inputs.get("fair_value") if iv.score is not None else None
        print("\n%s | %s | price=%s | P/E=%s" % (
            t, b.sector, b.latest_price,
            ("%.1f" % (b.latest_price / b.ttm_eps)) if (b.latest_price and b.ttm_eps and b.ttm_eps > 0) else "-"))
        print("   VALUATION = %s  coverage=%s | fair~Rs%s  MoS=%s" % (
            s(r.score), r.coverage.value, ("%.0f" % fv) if fv else "-",
            ("%+.0f%%" % (mos * 100)) if mos is not None else "-"))
        for c in r.components:
            mark = "N/A" if c.score is None else s(c.score)
            print("     %-14s %5s  [%-7s] %s" % (c.name, mark, c.coverage.value, c.rationale))

    scored = [(t, r.score) for t, r in results.items() if r.score is not None]
    print("\n" + "=" * 82)
    print("DISTRIBUTION (%d/%d scored)" % (len(scored), len(u)))
    print("=" * 82)
    print("  coverage: %s" % dict(collections.Counter(r.coverage.value for r in results.values())))
    haveiv = sum(1 for r in results.values() if comp(r, "intrinsic").score is not None)
    print("  have fair-value + margin-of-safety: %d" % haveiv)
    nones = sorted(t for t, r in results.items() if r.score is None)
    print("  unscored (loss-makers / no price) (%d): %s" % (len(nones), nones))
    buckets = collections.Counter(int(sc) for _, sc in scored)
    print("  histogram:")
    for k in range(6):
        print("     %d.x  %3d %s" % (k, buckets.get(k, 0), "#" * buckets.get(k, 0)))
    scored.sort(key=lambda x: x[1], reverse=True)
    print("\n  CHEAPEST 12 (highest valuation score):")
    for t, sc in scored[:12]:
        print("     %.2f  %-7s %s" % (sc, t, u.get(t).sector))
    print("  DEAREST 8:")
    for t, sc in scored[-8:]:
        print("     %.2f  %-7s %s" % (sc, t, u.get(t).sector))
    print("\nB4.2 verifier done -- read-only.")


if __name__ == "__main__":
    main()
