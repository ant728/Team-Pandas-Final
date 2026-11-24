"""Step 9: today's screen. Which listed banks look most like the 2023 victims on the LATEST call reports?

Instructor audit B1; rules written before any 2026 data was downloaded: specs_tried.md #26-#27.

Step 8 asks whether the screen would have worked in 2023 (a test). This step applies the SAME score to the
latest quarter (a current list, with no outcomes yet):
1. Universe: every entity in the NY Fed CRSP-FRB link active at the end of its latest vintage (Sep 30, 2024).
   An entity controlled by another entity in the universe is folded into that parent.
2. Banks are linked, summed and measured exactly as in step 4, with call reports and NIC relationships as of
   TODAY_CALL_REPORT_DATE.
3. Score and top-10% flag exactly as in step 8.
4. Because the score is a relative ranking (it always flags a top 10%), we also compare levels with Dec 2022:
   medians, 90th percentiles, and how many banks reach First Republic's Dec 2022 values.

Outputs: outputs/fragility_screen_<date>.csv       one row per entity in today's universe
         outputs/fragility_screen_today.md         the report
         outputs/fragility_screen_today_summary.csv  the Dec 2022 vs. today comparison (read by the dashboard)
"""
import importlib

import numpy as np
import pandas as pd

from config import NYFED_LINK_VINTAGE_END, OUTPUTS, RAW, SCREEN_MAIN_CUTOFF, SCREEN_PREDICTORS, TODAY_CALL_REPORT_DATE

build = importlib.import_module("04_build_dataset")      # linking and measures, exactly as in step 4
screen = importlib.import_module("08_fragility_screen")   # score and flags, exactly as in step 8


def today_universe(parents):
    """Entities active at the end of the latest NY Fed link vintage, with controlled entities folded into their parent."""
    link = pd.read_csv(RAW / "nyfed_crsp_frb_link.csv")
    uni = link[link["dt_end"] >= NYFED_LINK_VINTAGE_END].rename(columns={"entity": "rssd_id"})
    assert uni["rssd_id"].is_unique
    ids = set(uni["rssd_id"])
    parent = uni["rssd_id"].map(lambda r: build.listed_controller(r, parents, ids - {r}))
    folded = uni[parent.notna()].assign(into=parent[parent.notna()].astype(int))
    for r in folded.itertuples():
        print(f"Folded {r.name.title()} into {uni.loc[uni.rssd_id == r.into, 'name'].iloc[0].title()} "
              "(it controls it on the as-of date)")
    uni = uni[parent.isna()]
    assert uni["permco"].is_unique, "one row per listed company"
    return uni, folded


def main():
    date = TODAY_CALL_REPORT_DATE
    parents = build.controlling_parents(date)
    uni, folded = today_universe(parents)
    banks = build.assign_entities(build.bank_level(date), uni, date)
    m = build.measures(banks)
    today = uni[["rssd_id", "permco", "name", "inst_type"]].merge(m, on="rssd_id", how="left", validate="1:1")
    today["has_fdic"] = today["n_banks"].notna()
    # Tickers come from CRSP, which our pull has for the Dec 2022 sample only; others show their name.
    tickers = pd.read_csv(OUTPUTS / "final_dataset.csv").set_index("rssd_id")["ticker"]
    today["ticker"] = today["rssd_id"].map(tickers).fillna(today["name"].str.title())

    ranked, cutoffs = screen.rank_and_flag(today[["rssd_id", "permco", "ticker", "name", "has_fdic", "total_assets_bn"]
                                                 + SCREEN_PREDICTORS])
    unranked = today[~today["rssd_id"].isin(ranked["rssd_id"])].copy()
    unranked["reason"] = np.where(~unranked["has_fdic"], "no insured bank linked on the as-of date "
                                  "(acquired, delisted or a non-bank)", "missing a predictor")
    flag = f"flag_top{round(SCREEN_MAIN_CUTOFF * 100)}"
    ranked = ranked.sort_values("rank")
    cols = ["rank", "ticker", "name", "rssd_id", "total_assets_bn"] + SCREEN_PREDICTORS + \
           [f"pct_{c}" for c in SCREEN_PREDICTORS] + ["score", "flag_top5", "flag_top10", "flag_top20"]
    ranked[cols].to_csv(OUTPUTS / f"fragility_screen_{date}.csv", index=False, float_format="%.6g")

    # ---- Did the system get safer? (#27) ----
    then = pd.read_csv(OUTPUTS / "fragility_screen.csv")          # the Dec 2022 ranked sample (step 8)
    frc = then.set_index("ticker").loc["FRC"]
    bench_u, bench_s = frc["uninsured_dep_share"], frc["sec_loss_to_equity"]
    rows = []
    for report_date, label, d in [("20221231", "Dec 31, 2022", then), (date, f"{date[4:6]}/{date[6:]}/{date[:4]}", ranked)]:
        rows.append({"report_date": report_date, "date": label, "banks_ranked": len(d),
                     "median_uninsured_share": d["uninsured_dep_share"].median(),
                     "p90_uninsured_share": d["uninsured_dep_share"].quantile(0.9),
                     "median_sec_loss_to_equity": d["sec_loss_to_equity"].median(),
                     "p90_sec_loss_to_equity": d["sec_loss_to_equity"].quantile(0.9),
                     "at_or_above_frc_both": int(((d["uninsured_dep_share"] >= bench_u) & (d["sec_loss_to_equity"] >= bench_s)).sum()),
                     "at_or_above_frc_uninsured": int((d["uninsured_dep_share"] >= bench_u).sum()),
                     "at_or_above_frc_sec_loss": int((d["sec_loss_to_equity"] >= bench_s).sum()),
                     "frc_uninsured_benchmark": bench_u, "frc_sec_loss_benchmark": bench_s})
    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUTS / "fragility_screen_today_summary.csv", index=False, float_format="%.6g")
    a, b = summary.iloc[0], summary.iloc[1]
    both_now = ranked[(ranked["uninsured_dep_share"] >= bench_u) & (ranked["sec_loss_to_equity"] >= bench_s)]

    k, cut, n_flag = cutoffs[SCREEN_MAIN_CUTOFF]
    L = ["# Who's next today: the screen on the latest call reports", "",
         f"Generated by `code/09_screen_today.py`. Rules written before any {date[:4]} data was downloaded: "
         "`specs_tried.md` #26–#27. Same score as the 2023 test in `outputs/fragility_screen.md`, applied to the call "
         f"reports of **{date[4:6]}/{date[6:]}/{date[:4]}**. This is a current list, not a forecast: there are no outcomes yet.", "",
         "## Did the system get safer since Dec 2022?", "",
         "The score is a *relative* ranking, so it flags a top 10% however safe banks are. These levels say how fragile "
         "that top 10% actually is.", "",
         f"| | Dec 31, 2022 | {b.date} |", "|---|---|---|",
         f"| Banks ranked | {a.banks_ranked} | {b.banks_ranked} |",
         f"| Median uninsured share | {a.median_uninsured_share:.1%} | {b.median_uninsured_share:.1%} |",
         f"| 90th percentile, uninsured share | {a.p90_uninsured_share:.1%} | {b.p90_uninsured_share:.1%} |",
         f"| Median securities loss / equity | {a.median_sec_loss_to_equity:.2f} | {b.median_sec_loss_to_equity:.2f} |",
         f"| 90th percentile, securities loss / equity | {a.p90_sec_loss_to_equity:.2f} | {b.p90_sec_loss_to_equity:.2f} |",
         f"| Banks at or above First Republic's Dec 2022 levels on **both** ({bench_u:.1%} uninsured, {bench_s:.2f} loss/equity) "
         f"| {a.at_or_above_frc_both} | {b.at_or_above_frc_both} |",
         f"| ... on uninsured share alone | {a.at_or_above_frc_uninsured} | {b.at_or_above_frc_uninsured} |",
         f"| ... on securities loss / equity alone | {a.at_or_above_frc_sec_loss} | {b.at_or_above_frc_sec_loss} |", ""]
    L += [f"Banks at or above First Republic's Dec 2022 levels on both measures today: "
          + (", ".join(f"{r.ticker} ({r.uninsured_dep_share:.1%}, {r.sec_loss_to_equity:.2f})" for r in both_now.itertuples())
             if len(both_now) else "**none**") + ".", ""]
    L += ["## Sample", "",
          f"- Universe: **{len(uni) + len(folded)}** entities in the NY Fed CRSP–FRB link at the end of its latest vintage "
          "(Sep 30, 2024). Banks listed since then are not covered.",
          f"- Folded into a parent in the universe: {', '.join(folded['name'].str.title()) or 'none'}.",
          f"- Ranked: **{len(ranked)}**. Not ranked: {len(unranked)}, listed below.",
          f"- **Top 10%:** the {k}th-highest score is {cut:.3f}; {n_flag} entities score at or above it.", "",
          "## The top-10% group today", "",
          "| Rank | Entity | Assets ($B) | Uninsured share | Securities loss / equity | Score |", "|---|---|---|---|---|---|"]
    for _, r in ranked[ranked[flag]].iterrows():
        L.append(f"| {r['rank']} | {r.ticker} ({r['name'].title()}) | {r.total_assets_bn:,.1f} | {r.uninsured_dep_share:.1%} | "
                 f"{r.sec_loss_to_equity:.2f} | {r.score:.3f} |")
    L += ["", "## Not ranked", ""] + [f"- {r['name'].title()}: {r.reason}" for _, r in unranked.iterrows()]
    (OUTPUTS / "fragility_screen_today.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Today's screen ({date}): {len(ranked)} ranked, {len(unranked)} not ranked; top 10% = {n_flag}. "
          f"At or above First Republic's Dec 2022 levels on both: {a.at_or_above_frc_both} then, "
          f"{b.at_or_above_frc_both} now. Report: outputs/fragility_screen_today.md")


if __name__ == "__main__":
    main()
