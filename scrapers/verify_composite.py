"""B4.5 verifier -- the full RupeyaScore + verdict + style + Shariah. Read-only.

Run from the scrapers folder with the venv active:
    rmdir /s /q rupeya\scoring\__pycache__
    python verify_composite.py
"""

from __future__ import annotations

import collections

from rupeya.scoring import load_universe, score_universe, macro


def s(x):
    return "%.2f" % x if x is not None else " - "


def chip(sh):
    return "Halal " if sh is True else "Non-SC" if sh is False else "  ?   "


def pe(b):
    if b.latest_price and b.ttm_eps and b.ttm_eps > 0:
        return "%.1f" % (b.latest_price / b.ttm_eps)
    return "-"


def main():
    print("macro: CPI=%.1f%% PIB10Y=%.1f%% cost_of_equity=%.1f%%   "
          "RupeyaScore = 0.30 BQ + 0.30 FH + 0.25 VAL + 0.15 CAT\n" % (
              macro.CPI_INFLATION_YOY * 100, macro.PIB_10Y_YIELD * 100, macro.discount_rate(1.0) * 100))
    u = load_universe()
    results = score_universe(u)

    samples = ["MCB", "UBL", "MEBL", "MARI", "OGDC", "LUCK", "FFC", "EFERT",
               "ENGRO", "NESTLE", "SYS", "HUBC"]
    print("=" * 92)
    print("SAMPLE -- RupeyaScore (BQ / FH / VAL / CAT -> composite -> verdict)")
    print("=" * 92)
    print("  %-7s %-22s %-6s %-11s %-10s  BQ   FH   VAL  CAT  COMP  MoS" % (
        "ticker", "sector", "shariah", "style", "VERDICT"))
    for t in samples:
        b = u.get(t)
        if not b or t not in results:
            continue
        r, p = results[t]
        f = r.flags
        print("  %-7s %-22s %-6s %-11s %-10s  %-4s %-4s %-4s %-4s %-4s %s" % (
            t, (b.sector or "")[:22], chip(f["is_shariah_compliant"]), f["style"], f["verdict"],
            s(r.business_quality), s(r.financial_health), s(r.valuation), s(r.catalysts),
            s(r.composite), ("%+.0f%%" % (r.margin_of_safety * 100)) if r.margin_of_safety is not None else "-"))

    rated = [(t, r) for t, (r, _) in results.items() if r.composite is not None]
    print("\n" + "=" * 92)
    print("DISTRIBUTION (%d rated / %d)" % (len(rated), len(u)))
    print("=" * 92)
    vc = collections.Counter(r.flags["verdict"] for _, r in rated)
    print("  verdicts: " + "  ".join("%s=%d" % (v, vc.get(v, 0))
          for v in ["STRONG BUY", "BUY", "HOLD", "TRIM", "EXIT"]))
    print("  styles  : %s" % dict(collections.Counter(r.flags["style"] for _, r in rated)))
    sh = collections.Counter(r.flags["is_shariah_compliant"] for _, r in rated)
    print("  shariah : Halal=%d  Non-SC=%d  unknown=%d" % (sh.get(True, 0), sh.get(False, 0), sh.get(None, 0)))
    nrisk = collections.Counter(rf for _, r in rated for rf in r.flags["risk_flags"])
    print("  risk flags: %s" % dict(nrisk))

    buys = [(t, r) for t, r in rated if r.flags["verdict"] in ("STRONG BUY", "BUY")]
    buys.sort(key=lambda tr: tr[1].composite, reverse=True)
    print("\n" + "=" * 92)
    print("RUPEYA SIGNAL LIST -- BUY and above, ranked by RupeyaScore  (%d names)" % len(buys))
    print("=" * 92)
    print("  COMP  VERDICT     shariah  style       P/E   MoS     ticker  sector")
    for t, r in buys:
        b = u.get(t)
        print("  %-4s  %-10s  %-6s   %-10s  %-4s  %-6s  %-7s %s" % (
            s(r.composite), r.flags["verdict"], chip(r.flags["is_shariah_compliant"]),
            r.flags["style"], pe(b),
            ("%+.0f%%" % (r.margin_of_safety * 100)) if r.margin_of_safety is not None else "-",
            t, b.sector))

    sells = [(t, r) for t, r in rated if r.flags["verdict"] in ("EXIT", "TRIM")]
    sells.sort(key=lambda tr: tr[1].composite)
    print("\n  AVOID / TRIM (lowest 10):")
    for t, r in sells[:10]:
        b = u.get(t)
        print("     %-4s %-5s %-7s %s  %s" % (
            s(r.composite), r.flags["verdict"], t, b.sector,
            ("; " + ", ".join(r.flags["risk_flags"])) if r.flags["risk_flags"] else ""))
    print("\nB4.5 verifier done -- read-only, nothing written to the DB yet (that's B4.6).")


if __name__ == "__main__":
    main()
