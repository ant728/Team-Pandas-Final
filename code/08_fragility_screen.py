"""Step 8: the "who's next" screen. Would Dec 31, 2022 balance sheets alone have flagged the banks that
got into trouble after SVB?

The rules were written down before any rank was computed: see "Pre-specified out-of-sample fragility
screen" in specs_tried.md (2026-11-10) and the implementation details #21-#25 (2026-11-18).

1. Ranking sample: every listed entity with both predictors (uninsured_dep_share, sec_loss_to_equity).
   Nobody is dropped for failing or for missing later returns.
2. Each predictor becomes a percentile rank (higher = more fragile); the score is their plain average.
   The top 10% are flagged, ties at the cutoff included. Top 5% and 20% are secondary only.
3. Outcomes, all AFTER the Mar 9-13, 2023 event window:
   a. First Republic and PacWest, the two named cases;
   b. FDIC failures from Mar 14 through Dec 31, 2023;
   c. a CRSP buy-and-hold return of -50% or worse from the Mar 13 close to the Dec 29, 2023 close.
The March event return is NOT used to build the score.

Inputs:  outputs/final_dataset.csv, data/processed/bank_entity_map.csv, data/raw/fdic_failures_2023.csv,
         data/raw/crsp/crsp_daily_2022_2023.csv (licensed; only per-entity aggregates are written out)
Outputs: outputs/fragility_screen.csv   one row per listed entity: predictors, ranks, score, flags, outcomes
         outputs/fragility_screen.md    the report: sample, cutoffs, named cases, recall and precision
         outputs/fragility_screen_scorecard.csv   recall and precision per outcome and cutoff (read by the dashboard)
"""
import math

import numpy as np
import pandas as pd

from config import (CRSP_DAILY, FAILURE_WINDOW, OUTPUTS, POST_EVENT_CLOSES, PROCESSED, RAW, SCREEN_CUTOFFS,
                    SCREEN_MAIN_CUTOFF, SCREEN_PREDICTORS, SEVERE_LOSS)

NAMED_CASES = {"FRC": "First Republic", "PACW": "PacWest"}


def rank_and_flag(df):
    """Percentile ranks, score, rank, and a flag for each cutoff (specs_tried.md #22)."""
    ranked = df[df[SCREEN_PREDICTORS].notna().all(axis=1)].copy()
    for col in SCREEN_PREDICTORS:
        ranked[f"pct_{col}"] = ranked[col].rank(pct=True, method="average")
    ranked["score"] = ranked[[f"pct_{c}" for c in SCREEN_PREDICTORS]].mean(axis=1)
    ranked["rank"] = ranked["score"].rank(ascending=False, method="min").astype(int)
    n = len(ranked)
    cutoffs = {}
    for share in SCREEN_CUTOFFS:
        k = math.ceil(share * n)
        cutoff = ranked["score"].nlargest(k).min()          # score of the k-th highest entity
        ranked[f"flag_top{round(share * 100)}"] = ranked["score"] >= cutoff   # ties at the cutoff are flagged
        cutoffs[share] = (k, cutoff, int(ranked[f"flag_top{round(share * 100)}"].sum()))
    return ranked, cutoffs


def fdic_failures():
    """Failed banks in the outcome window, matched to listed entities (specs_tried.md #24)."""
    fail = pd.read_csv(RAW / "fdic_failures_2023.csv")
    fail["fail_date"] = pd.to_datetime(fail["FAILDATE"], format="%m/%d/%Y")
    bank_map = pd.read_csv(PROCESSED / "bank_entity_map.csv")[["CERT", "rssd_id"]]
    fail = fail.merge(bank_map, on="CERT", how="left", validate="1:1")
    start, end = (pd.Timestamp(x) for x in FAILURE_WINDOW)
    fail["in_window"] = fail["fail_date"].between(start, end)
    fail["before_window"] = fail["fail_date"] < start
    return fail


def post_event_returns(permcos):
    """Compounded return, Mar 13 close to Dec 29 close, with delisting returns (specs_tried.md #25)."""
    first, last = (pd.Timestamp(x) for x in POST_EVENT_CLOSES)
    d = pd.read_csv(CRSP_DAILY, usecols=["permno", "permco", "date", "prc", "ret", "dlstdt", "dlret"],
                    parse_dates=["date", "dlstdt"], low_memory=False)
    d = d[d["permco"].isin(permcos) & d["date"].between(first, last)]
    rows = []
    for permco, g in d.groupby("permco"):
        # A company with several share classes: use the one with the most trading days.
        permno = g.groupby("permno").size().idxmax()
        g = g[g["permno"] == permno].sort_values("date")
        rec = {"permco": permco, "post_bhr": np.nan, "post_missing_reason": ""}
        start_row = g[g["date"] == first]
        if start_row.empty or start_row["prc"].isna().all():
            rec["post_missing_reason"] = "no Mar 13 close"
            rows.append(rec)
            continue
        after = g[g["date"] > first].copy()
        delist = after["dlstdt"].notna() & after["date"].eq(after["dlstdt"])
        if delist.any() and after.loc[delist, "dlret"].isna().any():
            rec["post_missing_reason"] = "delisted without a delisting return"
            rows.append(rec)
            continue
        if after.loc[~delist, "ret"].isna().any():
            rec["post_missing_reason"] = "missing daily return"
            rows.append(rec)
            continue
        r = after["ret"].copy()
        r[delist] = (1 + after.loc[delist, "ret"].fillna(0)) * (1 + after.loc[delist, "dlret"]) - 1
        rec["post_bhr"] = (1 + r).prod() - 1   # after a delisting the holder has the proceeds: no more rows
        rows.append(rec)
    out = pd.DataFrame(rows)
    missing = set(permcos) - set(out["permco"])
    out = pd.concat([out, pd.DataFrame({"permco": sorted(missing), "post_bhr": np.nan,
                                        "post_missing_reason": "no CRSP rows after Mar 13"})], ignore_index=True)
    return out


def scorecard(ranked, outcome, flag):
    """Recall and precision of one flag against one 0/1 outcome, ignoring missing outcomes."""
    known = ranked[ranked[outcome].notna()]
    hits = known[known[outcome].astype(bool) & known[flag]]
    n_events, n_flagged = int(known[outcome].astype(bool).sum()), int(known[flag].sum())
    return {"events": n_events, "flagged": n_flagged, "hits": len(hits),
            "recall": len(hits) / n_events if n_events else np.nan,
            "precision": len(hits) / n_flagged if n_flagged else np.nan,
            "base_rate": n_events / len(known) if len(known) else np.nan, "missing": int(ranked[outcome].isna().sum())}


def main():
    final = pd.read_csv(OUTPUTS / "final_dataset.csv")
    universe = final[["rssd_id", "permco", "ticker", "name", "has_fdic", "has_returns"] + SCREEN_PREDICTORS].copy()
    universe["ticker"] = universe["ticker"].fillna(universe["name"].str.title())  # 4 entities have no CRSP ticker
    ranked, cutoffs = rank_and_flag(universe)
    excluded = universe[~universe["rssd_id"].isin(ranked["rssd_id"])].copy()
    excluded["reason"] = np.where(~excluded["has_fdic"], "no FDIC data (not matched to an insured bank)",
                                  "missing a predictor")

    # Outcome b: FDIC failures in the window.
    fail = fdic_failures()
    in_win = fail[fail["in_window"]]
    ranked["fdic_failure"] = ranked["rssd_id"].isin(in_win["rssd_id"].dropna())
    ranked["failed_before_window"] = ranked["rssd_id"].isin(fail.loc[fail["before_window"], "rssd_id"].dropna())
    fail_dates = in_win.dropna(subset=["rssd_id"]).groupby("rssd_id")["fail_date"].min()
    ranked["fdic_fail_date"] = ranked["rssd_id"].map(fail_dates).dt.date

    # Outcome c: severe post-event loss.
    post = post_event_returns(ranked["permco"].tolist())
    ranked = ranked.merge(post, on="permco", how="left", validate="1:1")
    ranked["severe_loss"] = (ranked["post_bhr"] <= SEVERE_LOSS).where(ranked["post_bhr"].notna())
    no_rows = ranked["post_missing_reason"].eq("no CRSP rows after Mar 13")
    ranked.loc[no_rows & ranked["has_returns"], "post_missing_reason"] = "delisted before Mar 13"
    ranked.loc[no_rows & ~ranked["has_returns"], "post_missing_reason"] = "no CRSP returns at all"

    ranked = ranked.sort_values("rank")
    cols = (["rank", "ticker", "name", "rssd_id", "permco"] + SCREEN_PREDICTORS
            + [f"pct_{c}" for c in SCREEN_PREDICTORS] + ["score"] + [f"flag_top{round(s * 100)}" for s in SCREEN_CUTOFFS]
            + ["failed_before_window", "fdic_failure", "fdic_fail_date", "post_bhr", "severe_loss", "post_missing_reason"])
    ranked[cols].to_csv(OUTPUTS / "fragility_screen.csv", index=False, float_format="%.6g")

    # ---- Report ----
    main_flag = f"flag_top{round(SCREEN_MAIN_CUTOFF * 100)}"
    k, cut, n_flag = cutoffs[SCREEN_MAIN_CUTOFF]
    L = ["# Who's next: the out-of-sample fragility screen", "",
         "Generated by `code/08_fragility_screen.py`. Rules written before any rank was computed: "
         "`specs_tried.md`, \"Pre-specified out-of-sample fragility screen\" (2026-11-10) and #21–#25 (2026-11-18). "
         "The score uses only Dec 31, 2022 call reports; every outcome comes after Mar 13, 2023. "
         "These are descriptive results on a handful of crisis outcomes, not a test of forecasting skill.", "",
         "## Sample", "",
         f"- Universe: **{len(universe)}** listed entities (NY Fed CRSP–FRB link on Dec 31, 2022).",
         f"- Ranked: **{len(ranked)}** (both predictors available). Excluded: {len(excluded)}, each listed below.",
         f"- Score: average of the percentile ranks of `uninsured_dep_share` and `sec_loss_to_equity` (higher = more fragile).",
         f"- **Main flag, top 10%:** the {k}th-highest score is {cut:.3f}; {n_flag} entities score at or above it "
         f"({n_flag / len(ranked):.1%} of the ranked sample).", ""]
    L += ["| Cutoff | Rank needed | Score cutoff | Flagged |", "|---|---|---|---|"]
    L += [f"| Top {round(s * 100)}%{' (main)' if s == SCREEN_MAIN_CUTOFF else ' (secondary)'} | {kk} | {cc:.3f} | {nn} |"
          for s, (kk, cc, nn) in cutoffs.items()]
    L += ["", "Excluded from the ranking:", ""] + [f"- {r.ticker} ({r.name.title()}): {r.reason}" for r in excluded.itertuples()]

    L += ["", "## 1. Named cases", "", "| Entity | Uninsured share | Securities loss / equity | Percentile ranks | Score | Rank | "
          "Flagged (top 10%) | Cutoff |", "|---|---|---|---|---|---|---|---|"]
    for t, label in NAMED_CASES.items():
        r = ranked[ranked["ticker"] == t]
        if r.empty:
            L.append(f"| {label} ({t}) | not ranked | | | | | | |")
            continue
        r = r.iloc[0]
        L.append(f"| {label} ({t}) | {r.uninsured_dep_share:.1%} | {r.sec_loss_to_equity:.2f} | "
                 f"{r.pct_uninsured_dep_share:.0%} / {r.pct_sec_loss_to_equity:.0%} | {r.score:.3f} | {r['rank']} of {len(ranked)} | "
                 f"**{'Yes' if r[main_flag] else 'No'}** | {cut:.3f} |")

    L += ["", "## 2. FDIC failures, Mar 14 – Dec 31, 2023", ""]
    L += [f"- {r.NAME.title()} ({r.CITYST.title()}), failed {r.fail_date:%b %d, %Y}: "
          + (f"listed entity {ranked.loc[ranked['rssd_id'] == r.rssd_id, 'ticker'].iloc[0]}" if pd.notna(r.rssd_id)
             and (ranked["rssd_id"] == r.rssd_id).any() else "**not part of a listed entity**, so it can't be flagged")
          for r in in_win.sort_values("fail_date").itertuples()]
    before = ranked[ranked["failed_before_window"]]
    L += ["", f"Already failed before the window (Mar 10–12): {', '.join(before['ticker'])}; "
          f"{int(before[main_flag].sum())} of them are in the top-10% group. They count as non-failures in the window.", ""]

    L += ["## Recall and precision", "",
          "Recall = share of the events that were flagged. Precision = share of the flagged entities that had the event. "
          "Base rate = share of the ranked sample that had the event (what random flagging would give as precision).", "",
          "| Outcome | Cutoff | Events | Flagged | Flagged and had the event | Recall | Precision | Base rate | Missing outcome |",
          "|---|---|---|---|---|---|---|---|---|"]
    cards = []
    for outcome, label in [("fdic_failure", "FDIC failure"), ("severe_loss", f"Return ≤ {SEVERE_LOSS:.0%}")]:
        for s in SCREEN_CUTOFFS:
            sc = scorecard(ranked, outcome, f"flag_top{round(s * 100)}")
            cards.append({"outcome": outcome, "label": label, "cutoff": s, **sc})
            L.append(f"| {label} | Top {round(s * 100)}%{' (main)' if s == SCREEN_MAIN_CUTOFF else ''} | {sc['events']} | "
                     f"{sc['flagged']} | {sc['hits']} | {sc['recall']:.0%} | {sc['precision']:.0%} | {sc['base_rate']:.1%} | "
                     f"{sc['missing']} |")

    pd.DataFrame(cards).to_csv(OUTPUTS / "fragility_screen_scorecard.csv", index=False, float_format="%.6g")
    sev = ranked[ranked["severe_loss"].eq(True)].sort_values("post_bhr")
    L += ["", f"## 3. Return of {SEVERE_LOSS:.0%} or worse, Mar 13 – Dec 29, 2023", "",
          "| Entity | Return | Rank | Flagged (top 10%) |", "|---|---|---|---|"]
    L += [f"| {r.ticker} ({r['name'].title()}) | {r.post_bhr:.1%} | {r['rank']} | {'Yes' if r[main_flag] else 'No'} |"
          for _, r in sev.iterrows()]
    miss = ranked[ranked["post_bhr"].isna()]
    L += ["", "Missing return outcome: " + (", ".join(f"{r.ticker} ({r.post_missing_reason})" for r in miss.itertuples())
                                            if len(miss) else "none") + "."]

    L += ["", "## The top-10% group", "", "| Rank | Entity | Uninsured share | Securities loss / equity | Score | "
          "Failed in window | Return after Mar 13 |", "|---|---|---|---|---|---|---|"]
    for _, r in ranked[ranked[main_flag]].iterrows():
        ret = f"{r.post_bhr:.1%}" if pd.notna(r.post_bhr) else f"missing ({r.post_missing_reason})"
        failed = "already failed" if r.failed_before_window else ("**Yes**" if r.fdic_failure else "No")
        L.append(f"| {r['rank']} | {r.ticker} ({r['name'].title()}) | {r.uninsured_dep_share:.1%} | {r.sec_loss_to_equity:.2f} | "
                 f"{r.score:.3f} | {failed} | {ret} |")
    (OUTPUTS / "fragility_screen.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    named = ", ".join(f"{t} rank {int(ranked.loc[ranked.ticker == t, 'rank'].iloc[0])} "
                      f"({'flagged' if ranked.loc[ranked.ticker == t, main_flag].iloc[0] else 'not flagged'})"
                      for t in NAMED_CASES if (ranked["ticker"] == t).any())
    print(f"Screen: {len(ranked)} ranked of {len(universe)}; top 10% = {n_flag} flagged (score >= {cut:.3f}). {named}. "
          "Full report: outputs/fragility_screen.md")


if __name__ == "__main__":
    main()
