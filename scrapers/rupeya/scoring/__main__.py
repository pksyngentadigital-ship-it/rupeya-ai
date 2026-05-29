"""
B4.0 inspector -- `python -m rupeya.scoring`

Read-only. Loads the Universe through the new data layer and prints a report so
we can confirm the foundation reflects reality (derived shares, market cap,
TTM basis, split-immune growth, archetype dispatch, coverage tiers, integrity
flags) BEFORE any scoring math is written. Writes nothing.

Output is deliberately ASCII-only so it renders on Windows cmd without any
UnicodeEncodeError.
"""

from __future__ import annotations

import collections

from . import macro
from .data import load_universe
from .periods import parse_period
from .types import Archetype, Tier


def pkr(v):
    if v is None:
        return "-"
    a = abs(v)
    if a >= 1e12:
        return f"{v/1e12:,.2f}T"
    if a >= 1e9:
        return f"{v/1e9:,.2f}B"
    if a >= 1e6:
        return f"{v/1e6:,.1f}M"
    return f"{v:,.0f}"


def pct(v):
    return f"{v*100:,.1f}%" if v is not None else "-"


def main() -> None:
    print("=" * 70)
    print(f"MACRO YARDSTICKS  (AS_OF {macro.AS_OF} -- founder to verify)")
    print("=" * 70)
    print(f"  policy={pct(macro.POLICY_RATE)}  KIBOR6M={pct(macro.KIBOR_6M)}  "
          f"PIB10Y={pct(macro.PIB_10Y_YIELD)}  CPI={pct(macro.CPI_INFLATION_YOY)}  "
          f"ERP={pct(macro.EQUITY_RISK_PREMIUM)}")
    print(f"  discount_rate(beta=1) = {pct(macro.discount_rate(1.0))}   "
          f"real value of +12% nominal growth = {pct(macro.real_growth(0.12))}")

    u = load_universe()

    print("\n" + "=" * 70)
    print(f"UNIVERSE  ({len(u)} covered stocks)")
    print("=" * 70)
    arch = collections.Counter(b.archetype.value for b in u)
    tier = collections.Counter(b.coverage.tier.value for b in u)
    print(f"  archetype : {dict(arch)}")
    print(f"  tier      : {dict(tier)}")
    print(f"  priced    : {sum(1 for b in u if b.latest_price)} / {len(u)}")
    print(f"  market cap derived : {sum(1 for b in u if b.market_cap)} / {len(u)}")
    print(f"  share-count changes detected : {sum(1 for b in u if b.share_count_changed)}")

    print("\n  coverage feeds (how many stocks can feed each metric family):")
    for feat in ["has_growth", "has_returns", "has_leverage", "has_cashflow",
                 "has_dividends"]:
        n = sum(1 for b in u if getattr(b.coverage, feat))
        print(f"     {feat:<16} {n:>3} / {len(u)}")

    flagged = [(b.ticker, f) for b in u for f in b.integrity_flags]
    n_stocks_flagged = len(set(t for t, _ in flagged))
    print(f"\n  integrity flags raised : {len(flagged)} across {n_stocks_flagged} stocks")
    for t, f in flagged[:12]:
        print(f"     {t:<7} {f}")
    if len(flagged) > 12:
        print(f"     ... and {len(flagged)-12} more")

    print("\n" + "=" * 70)
    print("SAMPLE BUNDLES  (eyeball the derived primitives)")
    print("=" * 70)
    samples = ["LUCK", "OGDC", "MCB", "ENGRO", "FFC", "ACPL", "AGP", "ABL"]
    for t in samples:
        b = u.get(t)
        if not b:
            print(f"\n--- {t}: not in universe ---")
            continue
        c = b.coverage
        eps_s = f"{b.ttm_eps:.2f}" if b.ttm_eps is not None else "-"
        print(f"\n--- {t} | {b.sector} | {b.archetype.value} | tier={c.tier.value} ---")
        print(f"    price={b.latest_price} @ {b.latest_price_date} | "
              f"impl.shares={pkr(b.implied_shares)} | mcap={pkr(b.market_cap)}")
        print(f"    TTM NI={pkr(b.ttm_ni)}  rev={pkr(b.ttm_revenue)}  eps={eps_s}   "
              f"[{b.ttm_basis}]")
        real = (f"  (real {pct(macro.real_growth(b.revenue_cagr))})"
                if b.revenue_cagr is not None else "")
        print(f"    growth: rev CAGR={pct(b.revenue_cagr)}/{b.revenue_cagr_years or '-'}y  "
              f"NI CAGR={pct(b.ni_cagr)}/{b.ni_cagr_years or '-'}y{real}")
        if b.latest_price and b.ttm_eps:
            ey = b.ttm_eps / b.latest_price
            print(f"    P/E={b.latest_price/b.ttm_eps:.1f}  E/P={pct(ey)}  "
                  f"E/P-minus-PIB={pct(macro.earnings_yield_spread(ey))}")
        # Book value: use shares CONTEMPORANEOUS with the snapshot, flag staleness.
        bs = b.bs_snapshot
        if bs and bs.get("book_value") and bs.get("eps") and bs.get("net_income"):
            snap_shares = bs["net_income"] / bs["eps"]
            bvps = bs["book_value"] / snap_shares
            stale = parse_period(b.latest_row["period"])[0] - parse_period(bs["period"])[0]
            stale_s = f", {stale}y stale" if stale > 0 else ""
            pb = f"  P/B={b.latest_price/bvps:.2f}" if b.latest_price else ""
            print(f"    book: BVPS={bvps:,.2f} @ {bs['period']}{stale_s}{pb}  "
                  f"fields={b.bs_fields_present}")
        elif bs:
            print(f"    book: @{bs['period']} {b.bs_fields_present}")
        else:
            print("    book: none")

    print("\nB4.0 inspector done -- read-only, nothing written.")


if __name__ == "__main__":
    main()
