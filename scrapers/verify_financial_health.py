"""B4.1 verifier -- Financial Health on the live universe. Read-only.

Run from the scrapers folder with the venv active:
    python verify_financial_health.py
"""

from __future__ import annotations

import collections

from rupeya.scoring import load_universe
from rupeya.scoring.financial_health import score_financial_health
from rupeya.scoring import macro


def s(x):
    return "%.2f" % x if x is not None else "  - "


def main():
    print("macro: CPI=%.1f%% PIB10Y=%.1f%% cost_of_equity=%.1f%%\n" % (
        macro.CPI_INFLATION_YOY * 100, macro.PIB_10Y_YIELD * 100, macro.discount_rate(1.0) * 100))
    u = load_universe()
    results = {b.ticker: score_financial_health(b) for b in u}

    samples = ["LUCK", "OGDC", "MARI", "MCB", "UBL", "ENGRO", "FFC", "ACPL", "AGP", "HUBC", "KAPCO", "ABL"]
    print("=" * 78)
    print("SAMPLE -- Financial Health (glass-box)")
    print("=" * 78)
    for t in samples:
        b, r = u.get(t), results.get(t)
        if not b or not r:
            print("\n%s: not in universe" % t)
            continue
        print("\n%s | %s | %s | tier=%s" % (t, b.sector, b.archetype.value, b.coverage.tier.value))
        print("   FINANCIAL HEALTH = %s  coverage=%s" % (s(r.score), r.coverage.value))
        print("   notes: %s" % "; ".join(r.notes))
        for c in r.components:
            mark = "N/A" if c.score is None else s(c.score)
            print("     %-9s %5s  [%-7s] %s" % (c.name, mark, c.coverage.value, c.rationale))

    scored = [(t, r.score) for t, r in results.items() if r.score is not None]
    print("\n" + "=" * 78)
    print("DISTRIBUTION (%d/%d scored)" % (len(scored), len(u)))
    print("=" * 78)
    print("  coverage: %s" % dict(collections.Counter(r.coverage.value for r in results.values())))
    print("  LIMITED_DATA (caps verdict at BUY): %d" % sum(1 for r in results.values() if "LIMITED_DATA" in r.notes))
    nones = sorted(t for t, r in results.items() if r.score is None)
    print("  unscored (%d): %s" % (len(nones), nones))
    buckets = collections.Counter(int(sc) for _, sc in scored)
    print("  histogram:")
    for k in range(6):
        print("     %d.x  %3d %s" % (k, buckets.get(k, 0), "#" * buckets.get(k, 0)))
    scored.sort(key=lambda x: x[1], reverse=True)
    print("\n  TOP 12:")
    for t, sc in scored[:12]:
        print("     %.2f  %-7s %s" % (sc, t, u.get(t).sector))
    print("  BOTTOM 8:")
    for t, sc in scored[-8:]:
        print("     %.2f  %-7s %s" % (sc, t, u.get(t).sector))
    print("\nB4.1 verifier done -- read-only.")


if __name__ == "__main__":
    main()
