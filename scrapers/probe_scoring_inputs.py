"""
Read-only diagnostic for B4 scoring inputs.

Run once from the scrapers/ folder to confirm the REAL shape of the data
the scoring engine will consume, before we write the data-access layer:

    cd C:\\Users\\Abdullah\\Documents\\Claude\\Projects\\Rupeya.ai\\scrapers
    python probe_scoring_inputs.py

It writes NOTHING. It only reads stocks / fundamentals_quarterly / prices_daily
and prints a compact report. Paste the whole output back.
"""

from __future__ import annotations

import collections

from rupeya import db

COLS = ["revenue", "net_income", "eps", "book_value",
        "debt", "cash", "fcf", "dividend_per_share"]
BS_COLS = ["book_value", "debt", "cash", "fcf", "dividend_per_share"]


def fnum(v):
    return f"{float(v):,.0f}" if v is not None else "·"


def main() -> None:
    client = db.get_client()

    # ---- stocks universe ----
    stocks = (
        client.table("stocks")
        .select("ticker,name,sector,sub_sector,is_covered,"
                "is_shariah_compliant,style,market_cap_pkr")
        .limit(2000)
        .execute()
        .data
        or []
    )
    by_ticker = {s["ticker"]: s for s in stocks}
    covered = [s for s in stocks if s.get("is_covered")]

    print("=" * 64)
    print("STOCKS")
    print("=" * 64)
    print(f"total stocks      : {len(stocks)}")
    print(f"is_covered = TRUE : {len(covered)}")
    sec = collections.Counter((s.get("sector") or "?") for s in covered)
    print(f"sectors (covered) : {len(sec)} distinct")
    for name, n in sec.most_common():
        print(f"    {n:>3}  {name}")
    print(f"is_shariah set on : {sum(1 for s in stocks if s.get('is_shariah_compliant') is not None)} / {len(stocks)}")
    print(f"style set on      : {sum(1 for s in stocks if s.get('style'))} / {len(stocks)}")
    print(f"market_cap set on : {sum(1 for s in stocks if s.get('market_cap_pkr') is not None)} / {len(stocks)}")

    # ---- fundamentals ----
    fund = (
        client.table("fundamentals_quarterly")
        .select("*")
        .limit(5000)
        .execute()
        .data
        or []
    )
    by_t: dict[str, list] = collections.defaultdict(list)
    for r in fund:
        by_t[r["ticker"]].append(r)

    print("\n" + "=" * 64)
    print("FUNDAMENTALS_QUARTERLY")
    print("=" * 64)
    print(f"rows               : {len(fund)}")
    print(f"distinct tickers    : {len(by_t)}")

    fill = {c: sum(1 for r in fund if r.get(c) is not None) for c in COLS}
    print("column non-null     :")
    for c in COLS:
        print(f"    {c:<20} {fill[c]:>4} / {len(fund)}")

    # period-kind histogram
    def kind(p):
        return p.split("-")[-1] if "-" in p else "?"
    kinds = collections.Counter(kind(r["period"]) for r in fund)
    print(f"period kinds        : {dict(kinds)}")

    # tiers
    rich, thin = [], []
    for t, rows in by_t.items():
        has_bs = any(r.get(c) is not None for r in rows for c in BS_COLS)
        (rich if has_bs else thin).append(t)
    print(f"\nRICH (>=1 balance-sheet col): {len(rich)}")
    print("   ", " ".join(sorted(rich)))
    print(f"THIN (only rev/NI/EPS)      : {len(thin)}")
    print("   ", " ".join(sorted(thin)))

    pc = collections.Counter(len(rows) for rows in by_t.values())
    print(f"\nperiods-per-ticker  : {dict(sorted(pc.items()))}")

    # coverage vs universe
    covered_set = {s["ticker"] for s in covered}
    fund_set = set(by_t)
    print(f"covered WITHOUT any fundamentals: {sorted(covered_set - fund_set)}")

    # ---- sample dumps + reconciliation ----
    samples = ["LUCK", "OGDC", "MCB", "ENGRO", "FFC"] + sorted(thin)[:3]
    print("\n" + "=" * 64)
    print("SAMPLE ROWS  (eyeball units: expect ABSOLUTE PKR for rev/NI/BV/debt/cash/fcf; per-share for eps/dps)")
    print("=" * 64)
    for t in samples:
        rows = sorted(by_t.get(t, []), key=lambda r: r["period"])
        if not rows:
            print(f"\n--- {t}: (no fundamentals) ---")
            continue
        st = by_ticker.get(t, {})
        print(f"\n--- {t} | {st.get('sector','?')} | mcap={fnum(st.get('market_cap_pkr'))} "
              f"| shariah={st.get('is_shariah_compliant')} | style={st.get('style')} ---")
        for r in rows:
            print(f"   {r['period']:<9} rev={fnum(r.get('revenue')):>18}  NI={fnum(r.get('net_income')):>15}  "
                  f"eps={r.get('eps')}  BV={fnum(r.get('book_value')):>18}  debt={fnum(r.get('debt')):>15}  "
                  f"cash={fnum(r.get('cash')):>15}  fcf={fnum(r.get('fcf')):>15}  dps={r.get('dividend_per_share')}")
        cand = [r for r in rows if r.get("eps") and r.get("net_income")]
        if cand:
            r = cand[-1]
            shares = r["net_income"] / r["eps"]
            line = f"   >> implied shares (NI/EPS @ {r['period']}) = {shares:,.0f}"
            mc = st.get("market_cap_pkr")
            if mc:
                line += f" ; mcap/shares = implied price {float(mc)/shares:,.2f} PKR"
            if r.get("book_value"):
                line += f" ; BVPS = {r['book_value']/shares:,.2f}"
            print(line)

    # ---- price coverage ----
    print("\n" + "=" * 64)
    print("PRICES_DAILY")
    print("=" * 64)
    for t in ["LUCK", "OGDC", "MCB"]:
        latest = (
            client.table("prices_daily").select("date,close")
            .eq("ticker", t).order("date", desc=True).limit(1).execute().data
        )
        print(f"   {t}: latest = {latest}")


if __name__ == "__main__":
    main()
