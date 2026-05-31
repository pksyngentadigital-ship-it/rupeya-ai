"""
B4.6 orchestrator -- python -m rupeya.scoring [--dry-run] [--limit N]

Scores every covered PSX stock (deterministic, $0 API) and upserts the result to
public.stock_scores, logging a scrape_runs row. Read-only preview with --dry-run.

    cd scrapers ; .venv\\Scripts\\activate
    python -m rupeya.scoring --dry-run      # preview + sanity, writes NOTHING
    python -m rupeya.scoring                # writes to stock_scores
"""

from __future__ import annotations

import argparse
import collections

from . import load_universe, score_universe, MODEL_VERSION

SCORE_COLS = ("business_quality", "financial_health", "valuation", "catalysts", "composite")
VERDICTS = ["STRONG BUY", "BUY", "HOLD", "TRIM", "EXIT"]


def _clamp_mos(v):
    return None if v is None else max(-9.99, min(9.99, v))


def main():
    ap = argparse.ArgumentParser(description="Rupeya B4 scoring orchestrator")
    ap.add_argument("--dry-run", action="store_true", help="compute + verify, write nothing")
    ap.add_argument("--limit", type=int, default=0, help="score only first N (debug)")
    args = ap.parse_args()

    u = load_universe()
    results = score_universe(u)
    items = list(results.items())[: args.limit] if args.limit else list(results.items())

    rows = []
    for _t, (res, _p) in items:
        if res.composite is None:
            continue
        row = res.to_db_row()
        row["margin_of_safety"] = _clamp_mos(row["margin_of_safety"])
        rows.append(row)

    # ---- sanity checks (mandatory before any write) ----
    problems = []
    for r in rows:
        for col in SCORE_COLS:
            v = r[col]
            if v is not None and not (0.0 <= v <= 5.0):
                problems.append((r["ticker"], col, v))

    print("Scored %d stocks -> %d rows (model %s)" % (len(items), len(rows), MODEL_VERSION))
    vc = collections.Counter(r["flags"]["verdict"] for r in rows)
    print("verdicts: " + "  ".join("%s=%d" % (v, vc.get(v, 0)) for v in VERDICTS))
    shariah = collections.Counter(r["flags"]["is_shariah_compliant"] for r in rows)
    print("shariah : Halal=%d  Non-SC=%d  unknown=%d" % (
        shariah.get(True, 0), shariah.get(False, 0), shariah.get(None, 0)))
    print("sanity  : %d out-of-range scores" % len(problems))
    if problems:
        print("   !!", problems[:10])
    buys = sorted(((r["ticker"], r["composite"]) for r in rows
                   if r["flags"]["verdict"] in ("STRONG BUY", "BUY")),
                  key=lambda x: -x[1])
    print("BUY list: " + (", ".join("%s(%.2f)" % (t, c) for t, c in buys) or "(none)"))

    if args.dry_run:
        print("\nDRY RUN -- nothing written to stock_scores.")
        return
    if problems:
        print("\nABORTED -- out-of-range scores; refusing to write.")
        return

    from .. import loader  # lazy: only needed for the write path
    with loader.RunLogger("scoring_b4") as run:
        written = loader.upsert_stock_scores(rows)
        run.rows_written = written
    print("\nWROTE %d rows to public.stock_scores (verdict/style/shariah in flags)." % written)


if __name__ == "__main__":
    main()
