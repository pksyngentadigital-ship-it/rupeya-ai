"""B4.0 inspector -- `python -m rupeya.scoring`. Read-only universe report, ASCII only."""

from __future__ import annotations

import collections

from . import macro
from .data import load_universe
from .periods import parse_period


def pkr(v):
    if v is None:
        return "-"
    a = abs(v)
    if a >= 1e12:
        return "%.2fT" % (v / 1e12)
    if a >= 1e9:
        return "%.2fB" % (v / 1e9)
    if a >= 1e6:
        return "%.1fM" % (v / 1e6)
    return "%.0f" % v


def pct(v):
    return "%.1f%%" % (v * 100) if v is not None else "-"


def main():
    print("=" * 70)
    print("MACRO  AS_OF %s (founder to verify)" % macro.AS_OF)
    print("=" * 70)
    print("  policy=%s KIBOR6M=%s PIB10Y=%s CPI=%s ERP=%s" % (
        pct(macro.POLICY_RATE), pct(macro.KIBOR_6M), pct(macro.PIB_10Y_YIELD),
        pct(macro.CPI_INFLATION_YOY), pct(macro.EQUITY_RISK_PREMIUM)))
    print("  cost_of_equity=%s ; real value of +12%% nominal growth=%s" % (
        pct(macro.discount_rate(1.0)), pct(macro.real_growth(0.12))))

    u = load_universe()
    print("\n" + "=" * 70)
    print("UNIVERSE (%d covered)" % len(u))
    print("=" * 70)
    print("  archetype: %s" % dict(collections.Counter(b.archetype.value for b in u)))
    print("  tier: %s" % dict(collections.Counter(b.coverage.tier.value for b in u)))
    print("  priced: %d/%d" % (sum(1 for b in u if b.latest_price), len(u)))
    print("  market cap derived: %d/%d" % (sum(1 for b in u if b.market_cap), len(u)))
    print("  share-count changes: %d" % sum(1 for b in u if b.share_count_changed))
    print("  coverage feeds:")
    for feat in ["has_growth", "has_returns", "has_leverage", "has_cashflow", "has_dividends"]:
        print("     %-16s %d/%d" % (feat, sum(1 for b in u if getattr(b.coverage, feat)), len(u)))
    flagged = [(b.ticker, f) for b in u for f in b.integrity_flags]
    print("  integrity flags: %d across %d stocks" % (len(flagged), len(set(t for t, _ in flagged))))
    for t, f in flagged[:12]:
        print("     %-7s %s" % (t, f))
    if len(flagged) > 12:
        print("     ... and %d more" % (len(flagged) - 12))

    print("\n" + "=" * 70)
    print("SAMPLE BUNDLES")
    print("=" * 70)
    for t in ["LUCK", "OGDC", "MCB", "ENGRO", "FFC", "ACPL", "AGP", "ABL"]:
        b = u.get(t)
        if not b:
            print("\n--- %s: not in universe ---" % t)
            continue
        eps_s = "%.2f" % b.ttm_eps if b.ttm_eps is not None else "-"
        print("\n--- %s | %s | %s | tier=%s ---" % (t, b.sector, b.archetype.value, b.coverage.tier.value))
        print("    price=%s @ %s | impl.shares=%s | mcap=%s" % (
            b.latest_price, b.latest_price_date, pkr(b.implied_shares), pkr(b.market_cap)))
        print("    TTM NI=%s rev=%s eps=%s  [%s]" % (pkr(b.ttm_ni), pkr(b.ttm_revenue), eps_s, b.ttm_basis))
        real = "  (real %s)" % pct(macro.real_growth(b.revenue_cagr)) if b.revenue_cagr is not None else ""
        print("    growth: rev=%s/%sy NI=%s/%sy%s" % (
            pct(b.revenue_cagr), b.revenue_cagr_years or "-", pct(b.ni_cagr), b.ni_cagr_years or "-", real))
        if b.latest_price and b.ttm_eps:
            ey = b.ttm_eps / b.latest_price
            print("    P/E=%.1f E/P=%s E/P-PIB=%s" % (
                b.latest_price / b.ttm_eps, pct(ey), pct(macro.earnings_yield_spread(ey))))
        bs = b.bs_snapshot
        if bs and bs.get("book_value") and bs.get("eps") and bs.get("net_income"):
            ss = bs["net_income"] / bs["eps"]
            bvps = bs["book_value"] / ss
            stale = parse_period(b.latest_row["period"])[0] - parse_period(bs["period"])[0]
            stale_s = ", %dy stale" % stale if stale > 0 else ""
            pb = "  P/B=%.2f" % (b.latest_price / bvps) if b.latest_price else ""
            print("    book: BVPS=%.2f @ %s%s%s  fields=%s" % (bvps, bs["period"], stale_s, pb, b.bs_fields_present))
        elif bs:
            print("    book: @%s %s" % (bs["period"], b.bs_fields_present))
        else:
            print("    book: none")
    print("\nB4.0 inspector done -- read-only.")


if __name__ == "__main__":
    main()
