"""Step 3: event-window returns for every bank, from CRSP.

Main outcome: buy-and-hold abnormal return (BHAR) over trading days [0, +2] = Mar 9, 10, 13, 2023:
    BHAR = prod(1 + bank return) - prod(1 + CRSP value-weighted market return)
We compound instead of summing because these moves are huge: summing daily returns overstates a crash
(WAL: -76% summed vs. -64% actual, see specs_tried.md #3).

Delistings: on a bank's delisting date, its return is (1 + ret) * (1 + dlret) - 1. SVB and Signature
delisted Mar 10 with no CRSP delisting return; we set it to MISSING_DLRET_FAILED (-100%, equity wiped out).
A bank that delists inside the window holds cash for the remaining days.

Secondary outcome: market-model CAR (sum of daily abnormal returns, beta estimated on days -250 to -30).

Inputs:  data/raw/crsp/*.csv (licensed; from Prof. Bowen; never committed)
Outputs: data/interim/crsp_event_days.csv   row-level event-day returns (git-ignored, licensed)
         data/processed/bank_returns.csv    one row per bank (PERMNO): computed aggregates only
"""
import numpy as np
import pandas as pd

from config import (CRSP_DAILY, CRSP_DELIST, CRSP_MARKET, ESTIMATION_WINDOW, EVENT_DAY0, EVENT_WINDOW,
                    INTERIM, MIN_EST_OBS, MISSING_DLRET_FAILED, PROCESSED)


def load():
    for f in (CRSP_DAILY, CRSP_MARKET, CRSP_DELIST):
        if not f.exists():
            raise FileNotFoundError(
                f"{f} is missing. The CRSP files are licensed and not in the repo: get them from a teammate "
                f"(Lehigh users only) and put them in data/raw/crsp/.")
    d = pd.read_csv(CRSP_DAILY, parse_dates=["date", "dlstdt"], low_memory=False)
    m = pd.read_csv(CRSP_MARKET, parse_dates=["date"])
    assert not d.duplicated(["permno", "date"]).any(), "one row per PERMNO per day"
    assert m["date"].is_unique
    assert (d["shrcd"] == 11).all(), "README says all ordinary common shares"
    return d, m


def total_return(d):
    """Daily return including the delisting return on the delisting date."""
    d = d.copy()
    on_delist = d["date"].eq(d["dlstdt"])
    d["dlret_imputed"] = on_delist & d["dlret"].isna() & d["dlstcd"].between(500, 599)
    d.loc[d["dlret_imputed"], "dlret"] = MISSING_DLRET_FAILED
    d["r"] = d["ret"]
    has_dl = on_delist & d["dlret"].notna()
    d.loc[has_dl, "r"] = (1 + d.loc[has_dl, "ret"].fillna(0)) * (1 + d.loc[has_dl, "dlret"]) - 1
    return d


def main():
    d, m = load()
    d = total_return(d)

    # Trading calendar = CRSP market index days.
    cal = m["date"].sort_values().reset_index(drop=True)
    day0 = pd.Timestamp(EVENT_DAY0)
    assert (cal == day0).any(), f"{EVENT_DAY0} is not a trading day"
    p0 = cal.index[cal == day0][0]
    evt_days = cal.iloc[p0 + EVENT_WINDOW[0]: p0 + EVENT_WINDOW[1] + 1]
    est_days = cal.iloc[p0 + ESTIMATION_WINDOW[0]: p0 + ESTIMATION_WINDOW[1] + 1]
    mkt = m.set_index("date")["vwretd"]
    mkt_bhr = (1 + mkt[evt_days]).prod() - 1

    evt = d[d["date"].isin(evt_days)].copy()
    evt["rel_day"] = evt["date"].map({dt: i + EVENT_WINDOW[0] for i, dt in enumerate(evt_days)})
    evt["mkt_ret"] = evt["date"].map(mkt)

    rows = []
    for permno, g in evt.groupby("permno"):
        last = g.iloc[-1]
        rec = {"permno": permno, "permco": last["permco"], "ticker": g.iloc[0]["ticker"],
               "comnam": g.iloc[0]["comnam"], "n_event_days": len(g),
               "delisted_in_window": bool(g["date"].eq(g["dlstdt"]).any()),
               "dlret_imputed": bool(g["dlret_imputed"].any())}
        rec["bhr_0_2"] = (1 + g["r"]).prod() - 1      # days after a delisting earn 0 (cash)
        rec["bhar_0_2"] = rec["bhr_0_2"] - mkt_bhr

        est = d[(d["permno"] == permno) & d["date"].isin(est_days)][["date", "ret"]].dropna()
        est = est.assign(mkt=est["date"].map(mkt))
        rec["est_obs"] = len(est)
        if len(est) >= MIN_EST_OBS:
            beta, alpha = np.polyfit(est["mkt"], est["ret"], 1)
            ar = g["r"] - (alpha + beta * g["mkt_ret"])
            rec.update(beta=beta, car_0_2=ar.sum())
            evt.loc[g.index, "ar"] = ar
        rows.append(rec)

    out = pd.DataFrame(rows)
    assert out["permno"].is_unique and out["permco"].is_unique

    INTERIM.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    evt[["permno", "permco", "ticker", "date", "rel_day", "ret", "dlret", "dlret_imputed", "r", "mkt_ret", "ar"]] \
        .to_csv(INTERIM / "crsp_event_days.csv", index=False)
    out.to_csv(PROCESSED / "bank_returns.csv", index=False)

    print(f"market BHR over {evt_days.iloc[0]:%b %d}-{evt_days.iloc[-1]:%b %d}: {mkt_bhr:.2%}")
    print(f"{len(out)} banks with event-window returns; "
          f"{out['delisted_in_window'].sum()} delisted in the window "
          f"({', '.join(out.loc[out['delisted_in_window'], 'ticker'])}); "
          f"{out['car_0_2'].isna().sum()} without enough estimation days for a market-model CAR")


if __name__ == "__main__":
    main()
