"""
Data-access layer for the scoring engine. Reads only.

load_universe() -> Universe of StockBundles carrying the derived primitives:
archetype, implied shares, market cap, TTM (with basis), split-immune trend
growth, point-in-time balance-sheet snapshot, coverage tier, integrity flags.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta

from .periods import parse_period, sort_key, trend_growth, annualize, ANNUALIZE_FACTOR
from .types import Archetype, SECTOR_ARCHETYPE, Coverage, Tier, DataCoverage, StockBundle

log = logging.getLogger("rupeya.scoring.data")

BALANCE_COLS = ["book_value", "debt", "cash", "fcf"]
SHARE_CHANGE_THRESHOLD = 0.10


def _archetype_for(sector):
    return SECTOR_ARCHETYPE.get(sector or "", Archetype.NON_FINANCIAL)


def _implied_shares(row):
    if not row:
        return None
    ni, eps = row.get("net_income"), row.get("eps")
    if ni is None or eps in (None, 0):
        return None
    try:
        return float(ni) / float(eps)
    except (TypeError, ZeroDivisionError):
        return None


def _trend_over_annual(annual, key):
    pts = []
    for r in annual:
        v = r.get(key)
        p = parse_period(r["period"])
        if v is not None and p is not None:
            pts.append((p[0], float(v)))
    return trend_growth(pts)


def _build_bundle(meta, rows, price):
    rows = sorted(rows, key=lambda r: sort_key(r["period"]))
    annual = [r for r in rows if (parse_period(r["period"]) or (0, ""))[1] == "FY"]
    annual.sort(key=lambda r: parse_period(r["period"])[0])

    b = StockBundle(
        ticker=meta["ticker"],
        name=meta.get("name") or meta["ticker"],
        sector=meta.get("sector"),
        sub_sector=meta.get("sub_sector"),
        archetype=_archetype_for(meta.get("sector")),
        is_shariah_compliant=meta.get("is_shariah_compliant"),
        shariah_ratios=meta.get("shariah_ratios"),
        style=meta.get("style"),
        rows=rows,
        annual=annual,
        latest_fy=annual[-1] if annual else None,
        latest_row=rows[-1] if rows else None,
    )

    if price:
        b.latest_price, b.latest_price_date = price
    else:
        b.integrity_flags.append("no recent price")

    for r in reversed(rows):
        present = [c for c in BALANCE_COLS if r.get(c) is not None]
        if present:
            b.bs_snapshot = r
            b.bs_fields_present = present
            break

    series = []
    for r in annual:
        sh = _implied_shares(r)
        p = parse_period(r["period"])
        if sh and p:
            series.append((p[0], sh))
    b.implied_shares_series = series
    b.implied_shares = _implied_shares(b.latest_row) or (series[-1][1] if series else None)
    if len(series) >= 2:
        vals = [s for _, s in series]
        if min(vals) > 0:
            ratio = max(vals) / min(vals)
            b.share_count_change_ratio = ratio
            if ratio > 1.0 + SHARE_CHANGE_THRESHOLD:
                b.share_count_changed = True
                b.integrity_flags.append(
                    "share count changed %.1fx (bonus/split/rights) -- per-share "
                    "history not comparable; growth uses NI/revenue" % ratio)

    if b.latest_price and b.implied_shares:
        b.market_cap = b.latest_price * b.implied_shares

    _compute_ttm(b)
    b.revenue_cagr, b.revenue_cagr_years = _trend_over_annual(annual, "revenue")
    b.ni_cagr, b.ni_cagr_years = _trend_over_annual(annual, "net_income")
    _check_monotonicity(b)
    b.coverage = _assess_coverage(b)
    return b


def _compute_ttm(b):
    annual, latest_row = b.annual, b.latest_row

    def eps_from(ni):
        if ni is None or not b.implied_shares:
            return None
        return ni / b.implied_shares

    if annual:
        fy = b.latest_fy
        fy_year = parse_period(fy["period"])[0]
        fy_ni, fy_rev = fy.get("net_income"), fy.get("revenue")
        newer = [r for r in b.rows
                 if parse_period(r["period"])[0] > fy_year
                 and parse_period(r["period"])[1] != "FY"]
        if newer:
            cur = max(newer, key=lambda r: sort_key(r["period"]))
            cur_year, cur_kind = parse_period(cur["period"])
            prior = next((r for r in b.rows
                          if parse_period(r["period"]) == (cur_year - 1, cur_kind)), None)
            if prior and fy_ni is not None and cur.get("net_income") is not None \
                    and prior.get("net_income") is not None:
                b.ttm_ni = fy_ni + cur["net_income"] - prior["net_income"]
                if None not in (fy_rev, cur.get("revenue"), prior.get("revenue")):
                    b.ttm_revenue = fy_rev + cur["revenue"] - prior["revenue"]
                b.ttm_basis = "FY%d + %s - %s (stub)" % (fy_year, cur["period"], prior["period"])
            else:
                b.ttm_ni, b.ttm_revenue = fy_ni, fy_rev
                b.ttm_basis = "FY%d (newer %s, no prior-year stub)" % (fy_year, cur["period"])
        else:
            b.ttm_ni, b.ttm_revenue = fy_ni, fy_rev
            b.ttm_basis = "FY%d" % fy_year
        b.ttm_eps = eps_from(b.ttm_ni)
    elif latest_row:
        kind = parse_period(latest_row["period"])[1]
        b.ttm_ni = annualize(latest_row.get("net_income"), kind)
        b.ttm_revenue = annualize(latest_row.get("revenue"), kind)
        b.ttm_eps = eps_from(b.ttm_ni)
        b.ttm_basis = "annualized %s x%.2f" % (latest_row["period"], ANNUALIZE_FACTOR.get(kind, 1.0))
        b.integrity_flags.append(
            "TTM annualized from a single %s filing -- low confidence" % latest_row["period"])


def _check_monotonicity(b):
    by_year = defaultdict(dict)
    for r in b.rows:
        p = parse_period(r["period"])
        if p:
            by_year[p[0]][p[1]] = r
    order = ["Q1", "H1", "9M", "FY"]
    for year, kinds in by_year.items():
        seq = [(k, kinds[k].get("revenue")) for k in order
               if k in kinds and kinds[k].get("revenue") is not None]
        for (k0, v0), (k1, v1) in zip(seq, seq[1:]):
            if v1 < v0 - 1:
                b.integrity_flags.append(
                    "%d: cumulative revenue %s(%.0f) < %s(%.0f)" % (year, k1, v1, k0, v0))


def _assess_coverage(b):
    cov = DataCoverage(n_periods=len(b.rows), n_annual=len(b.annual),
                       has_price=b.latest_price is not None)
    n_ni = sum(1 for r in b.annual if r.get("net_income") is not None)
    cov.has_growth = n_ni >= 2 or (b.revenue_cagr_years or 0) > 0
    snap = b.bs_snapshot or {}
    cov.has_returns = snap.get("book_value") is not None
    cov.has_leverage = (snap.get("debt") is not None and snap.get("book_value") is not None
                        and b.archetype != Archetype.BANK)
    cov.has_cashflow = any(r.get("fcf") is not None for r in b.rows)
    cov.has_dividends = any(r.get("dividend_per_share") is not None for r in b.rows)
    if b.bs_snapshot:
        cov.tier = Tier.RICH
    elif cov.n_periods >= 2:
        cov.tier = Tier.GROWTH_ONLY
    else:
        cov.tier = Tier.SINGLE_PERIOD
    return cov


class Universe:
    def __init__(self, bundles):
        self.bundles = {b.ticker: b for b in bundles}
        self.sectors = defaultdict(list)
        for b in bundles:
            self.sectors[b.sector or "?"].append(b.ticker)

    def __len__(self):
        return len(self.bundles)

    def __iter__(self):
        return iter(self.bundles.values())

    def get(self, ticker):
        return self.bundles.get(ticker)

    def sector_peers(self, ticker, include_self=False):
        b = self.bundles.get(ticker)
        if not b:
            return []
        peers = [self.bundles[t] for t in self.sectors.get(b.sector or "?", [])]
        return peers if include_self else [p for p in peers if p.ticker != ticker]


def _fetch_latest_prices(client, window_days=14):
    maxrow = (client.table("prices_daily").select("date")
              .order("date", desc=True).limit(1).execute().data)
    if not maxrow:
        return {}
    maxdate = maxrow[0]["date"]
    cutoff = (date.fromisoformat(maxdate) - timedelta(days=window_days)).isoformat()
    rows = (client.table("prices_daily").select("ticker,date,close")
            .gte("date", cutoff).limit(20000).execute().data or [])
    latest = {}
    for r in rows:
        t, d, c = r["ticker"], r["date"], r.get("close")
        if c is None:
            continue
        if t not in latest or d > latest[t][1]:
            latest[t] = (float(c), d)
    return latest


def load_universe(client=None, covered_only=True):
    if client is None:
        from .. import db
        client = db.get_client()
    stocks = (client.table("stocks")
              .select("ticker,name,sector,sub_sector,is_covered,"
                      "is_shariah_compliant,shariah_ratios,style,market_cap_pkr")
              .limit(2000).execute().data or [])
    if covered_only:
        stocks = [s for s in stocks if s.get("is_covered")]
    fund = (client.table("fundamentals_quarterly").select("*").limit(5000).execute().data or [])
    by_t = defaultdict(list)
    for r in fund:
        by_t[r["ticker"]].append(r)
    prices = _fetch_latest_prices(client)
    bundles = [_build_bundle(s, by_t.get(s["ticker"], []), prices.get(s["ticker"])) for s in stocks]
    log.info("Loaded universe: %d stocks, %d priced", len(bundles),
             sum(1 for b in bundles if b.latest_price))
    return Universe(bundles)
