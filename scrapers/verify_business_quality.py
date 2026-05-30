"""B4.3 verifier -- Business Quality pillar on the live universe. Read-only.

Run from the scrapers folder with the venv active:
    rmdir /s /q rupeya\scoring\__pycache__
    python verify_business_quality.py
"""

from __future__ import annotations

import collections

from rupeya.scoring import load_universe, build_sector_context
from rupeya.scoring.business_quality import score_business_quality
from rupeya.scoring import macro


def s(x):
    return "%.2f" % x if x is not None else "  - "


def comp(r, name):
    return next(c for c in r.components if c.name == name)


def main():
    u = load_universe()
    ctx = build_sector_context(u)

    print("=" * 80)
    print("SECTOR ATTRACTIVENESS (median real NI growth, median ROE)  CPI=%.1f%% coe=%.1f%%"
          % (macro.CPI_INFLATION_YOY * 100, macro.discount_rate(1.0) * 100))
    print("=" * 80)
    rows = sorted(ctx.items(), key=lambda kv: (kv[1]["real_growth"] is None, -(kv[1]["real_growth"] or -9)))
    for sec, c in rows:
        g = "%+.1f%%" % (c["real_growth"] * 100) if c["real_growth"] is not None else "  -  "
        roe = "%.0f%%" % (c["roe"] * 100) if c["roe"] is not None else " - "
        print("   %-28s n=%-2d  real growth %6s   ROE %5s" % (sec, c["n"], g, roe))

    results = {b.ticker: score_business_quality(b, u) for b in u}
    samples = ["LUCK", "OGDC", "MARI", "MCB", "NESTLE", "ENGRO", "FFC", "SYS",
               "HUBC", "KAPCO", "COLG", "AGP"]
    print("\n" + "=" * 80)
    print("SAMPLE -- Business Quality (glass-box)")
    print("=" * 80)
    for t in samples:
        b, r = u.get(t), results.get(t)
        if not b or not r:
            print("\n%s: not in universe" % t)
            continue
        print("\n%s | %s | mcap=%s" % (
            t, b.sector, ("%.0fB" % (b.market_cap / 1e9)) if b.market_cap else "-"))
        print("   BUSINESS QUALITY = %s  coverage=%s" % (s(r.score), r.coverage.value))
        for c in r.components:
            mark = "N/A" if c.score is None else s(c.score)
            print("     %-22s %5s  [%-7s] %s" % (c.name, mark, c.coverage.value, c.rationale))

    scored = [(t, r.score) for t, r in results.items() if r.score is not None]
    print("\n" + "=" * 80)
    print("DISTRIBUTION (%d/%d scored)" % (len(scored), len(u)))
    print("=" * 80)
    print("  coverage: %s" % dict(collections.Counter(r.coverage.value for r in results.values())))
    nones = sorted(t for t, r in results.items() if r.score is None)
    print("  unscored (%d): %s" % (len(nones), nones))
    buckets = collections.Counter(int(sc) for _, sc in scored)
    print("  histogram:")
    for k in range(6):
        print("     %d.x  %3d %s" % (k, buckets.get(k, 0), "#" * buckets.get(k, 0)))
    scored.sort(key=lambda x: x[1], reverse=True)
    print("\n  HIGHEST QUALITY 12:")
    for t, sc in scored[:12]:
        print("     %.2f  %-7s %s" % (sc, t, u.get(t).sector))
    print("  LOWEST 8:")
    for t, sc in scored[-8:]:
        print("     %.2f  %-7s %s" % (sc, t, u.get(t).sector))
    print("\nB4.3 verifier done -- read-only.")


if __name__ == "__main__":
    main()
