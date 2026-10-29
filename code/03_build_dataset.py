"""Step 3: build the final dataset. One row = one listed bank entity (holding company, or the bank if it has none).

1. Bank fragility measures: sum the Q4 2022 call report fields across each entity's banks, then take ratios.
2. Event study: market-model CAR over trading days [0, +2] around Mar 9, 2023.
3. Merge 1:1 on ticker.

Outputs:
  data/processed/bank_measures.csv     one row per entity
  data/processed/event_returns.csv     one row per entity x event day (the ARs behind each CAR)
  outputs/poc_final_rows.csv           the final rows
"""
import numpy as np
import pandas as pd

from config import (CALL_REPORT_DATE, CROSSWALK, ESTIMATION_WINDOW, EVENT_DAY0, EVENT_WINDOW,
                    MARKET, OUTPUTS, PROCESSED, RAW)

SUM_FIELDS = ["ASSET", "DEP", "DEPDOM", "DEPUNINS", "EQTOT", "SC", "SCHA", "SCHF", "SCAA", "SCAF"]
MIN_EST_OBS = 150


def bank_measures():
    fin = pd.read_csv(RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv")
    assert fin["CERT"].is_unique

    g = fin.groupby("ticker")
    m = g[SUM_FIELDS].sum(min_count=1)  # $ thousands
    m["n_banks"] = g.size()
    # DEPUNINS is only reported by banks over $1B, so tiny subsidiaries show up as missing.
    m["n_banks_missing_uninsured"] = g["DEPUNINS"].apply(lambda s: s.isna().sum())

    m["total_assets_bn"] = m["ASSET"] / 1e6
    m["uninsured_dep_share"] = m["DEPUNINS"] / m["DEPDOM"]
    m["htm_unrealized_loss_bn"] = (m["SCHA"] - m["SCHF"]) / 1e6
    m["afs_unrealized_loss_bn"] = (m["SCAA"] - m["SCAF"]) / 1e6
    # HTM losses are NOT in book equity (HTM is carried at amortized cost), so this is the "hidden" hit.
    m["htm_loss_to_equity"] = (m["SCHA"] - m["SCHF"]) / m["EQTOT"]
    # Alternative: all securities losses. AFS losses already reduced book equity via AOCI.
    m["sec_loss_to_equity"] = ((m["SCHA"] - m["SCHF"]) + (m["SCAA"] - m["SCAF"])) / m["EQTOT"]
    m["htm_share_of_securities"] = m["SCHA"] / (m["SCHA"] + m["SCAF"])
    m["call_report_date"] = pd.to_datetime(CALL_REPORT_DATE).date()
    return m.reset_index()


def event_study(xw):
    px = pd.read_csv(RAW / "prices.csv", parse_dates=["date"])
    wide = px.pivot(index="date", columns="symbol", values="close")
    rets = wide.pct_change(fill_method=None)

    # Trading calendar = the market's trading days.
    cal = rets.index[rets[MARKET].notna()]
    day0 = pd.Timestamp(EVENT_DAY0)
    assert day0 in cal, f"{EVENT_DAY0} is not a trading day"
    p0 = cal.get_loc(day0)
    est_days = cal[p0 + ESTIMATION_WINDOW[0]: p0 + ESTIMATION_WINDOW[1] + 1]
    evt_days = cal[p0 + EVENT_WINDOW[0]: p0 + EVENT_WINDOW[1] + 1]

    cars, ars = [], []
    for row in xw.itertuples():
        rec = {"ticker": row.ticker, "car_note": ""}
        if row.yf_symbol not in rets.columns:
            rec["car_note"] = "no prices in yfinance (delisted)"
            cars.append(rec)
            continue

        est = rets.loc[est_days, [row.yf_symbol, MARKET]].dropna()
        evt = rets.loc[evt_days, [row.yf_symbol, MARKET]]
        if len(est) < MIN_EST_OBS or evt[row.yf_symbol].isna().any():
            rec["car_note"] = f"too little data (est obs={len(est)}, missing event days={evt[row.yf_symbol].isna().sum()})"
            cars.append(rec)
            continue

        beta, alpha = np.polyfit(est[MARKET], est[row.yf_symbol], 1)
        ar = evt[row.yf_symbol] - (alpha + beta * evt[MARKET])
        ar_mkt = evt[row.yf_symbol] - evt[MARKET]
        rec.update(alpha=alpha, beta=beta, est_obs=len(est),
                   car_0_2=ar.sum(), car_0_2_mktadj=ar_mkt.sum())
        cars.append(rec)
        for d, rel in zip(evt_days, range(EVENT_WINDOW[0], EVENT_WINDOW[1] + 1)):
            ars.append({"ticker": row.ticker, "date": d.date(), "rel_day": rel,
                        "ret": evt.at[d, row.yf_symbol], "mkt_ret": evt.at[d, MARKET],
                        "ar": ar[d], "ar_mktadj": ar_mkt[d]})

    return pd.DataFrame(cars), pd.DataFrame(ars)


def main():
    xw = pd.read_csv(CROSSWALK)
    assert xw["ticker"].is_unique and xw["entity_id"].is_unique

    measures = bank_measures()
    cars, ars = event_study(xw)

    final = (xw[["ticker", "entity_name", "entity_type", "entity_id"]]
             .merge(measures, on="ticker", how="left", validate="1:1")
             .merge(cars, on="ticker", how="left", validate="1:1"))
    assert len(final) == len(xw) and final["ticker"].is_unique
    final["est_obs"] = final["est_obs"].astype("Int64")

    cols = ["ticker", "entity_name", "entity_type", "entity_id", "call_report_date", "n_banks",
            "n_banks_missing_uninsured", "total_assets_bn", "uninsured_dep_share",
            "htm_unrealized_loss_bn", "afs_unrealized_loss_bn", "htm_loss_to_equity",
            "sec_loss_to_equity", "htm_share_of_securities", "beta", "est_obs",
            "car_0_2", "car_0_2_mktadj", "car_note"]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    measures.to_csv(PROCESSED / "bank_measures.csv", index=False)
    ars.to_csv(PROCESSED / "event_returns.csv", index=False)
    final[cols].to_csv(OUTPUTS / "poc_final_rows.csv", index=False, float_format="%.4f")

    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(final[["ticker", "total_assets_bn", "uninsured_dep_share", "htm_loss_to_equity",
                     "car_0_2", "car_note"]].round(3))


if __name__ == "__main__":
    main()
