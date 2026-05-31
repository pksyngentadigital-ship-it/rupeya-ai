"""Read-back check -- confirm B4 scores persisted to public.stock_scores. Read-only.

    python verify_stock_scores.py
"""

from __future__ import annotations

import collections

from rupeya import db


def main():
    c = db.get_client()
    rows = c.table("stock_scores").select("*").limit(2000).execute().data or []
    print("rows in public.stock_scores : %d" % len(rows))
    if not rows:
        print("  (empty -- did the write run?)")
        return

    mv = collections.Counter(r.get("model_version") for r in rows)
    print("model_version               : %s" % dict(mv))
    vc = collections.Counter((r.get("flags") or {}).get("verdict") for r in rows)
    print("verdicts (from flags JSONB) : " + "  ".join(
        "%s=%d" % (v, vc.get(v, 0)) for v in ["STRONG BUY", "BUY", "HOLD", "TRIM", "EXIT"]))
    sh = collections.Counter((r.get("flags") or {}).get("is_shariah_compliant") for r in rows)
    print("shariah                     : Halal=%d Non-SC=%d unknown=%d" % (
        sh.get(True, 0), sh.get(False, 0), sh.get(None, 0)))
    bad = [r["ticker"] for r in rows if r.get("composite") is not None
           and not (0 <= float(r["composite"]) <= 5)]
    print("composite out of 0-5 range  : %d %s" % (len(bad), bad[:8]))

    buys = [r for r in rows if (r.get("flags") or {}).get("verdict") in ("STRONG BUY", "BUY")]
    buys.sort(key=lambda r: -(float(r.get("composite") or 0)))
    print("\nBUY rows persisted:")
    print("  ticker  comp   verdict  shariah  style       fair_Rs    MoS")
    for r in buys:
        f = r.get("flags") or {}
        iv = r.get("intrinsic_value_pkr")
        mos = r.get("margin_of_safety")
        print("  %-7s %-5s  %-7s  %-6s   %-10s  %-9s  %s" % (
            r["ticker"], r.get("composite"), f.get("verdict"),
            "Halal" if f.get("is_shariah_compliant") else "Non-SC", f.get("style"),
            ("%.0f" % float(iv)) if iv is not None else "-",
            ("%+.0f%%" % (float(mos) * 100)) if mos is not None else "-"))

    mcb = next((r for r in rows if r["ticker"] == "MCB"), None)
    if mcb:
        print("\nMCB full persisted row (spot-check vs what the engine computed):")
        print("  BQ=%s FH=%s VAL=%s CAT=%s -> composite=%s" % (
            mcb.get("business_quality"), mcb.get("financial_health"),
            mcb.get("valuation"), mcb.get("catalysts"), mcb.get("composite")))
        print("  intrinsic_value_pkr=%s  margin_of_safety=%s" % (
            mcb.get("intrinsic_value_pkr"), mcb.get("margin_of_safety")))
        print("  flags=%s" % mcb.get("flags"))
    print("\nB4 read-back done.")


if __name__ == "__main__":
    main()
