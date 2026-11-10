"""Step 1: pull Q4 2022 call report fields from the FDIC BankFind API for every bank owned by a sample entity.

Output: data/raw/fdic_financials_20221231.csv, one row per insured bank (CERT) on the report date.

The holding company link (RSSDHCR) comes from the same Q4 2022 record, so it is the ownership
structure on the report date, not today's.
"""
import pandas as pd
import requests

from config import CALL_REPORT_DATE, CROSSWALK, FDIC_FIELDS, RAW
from provenance import log_download

API = "https://api.fdic.gov/banks/financials"


def fetch(filter_expr):
    params = {
        "filters": f"{filter_expr} AND REPDTE:{CALL_REPORT_DATE}",
        "fields": ",".join(FDIC_FIELDS),
        "limit": 1000,
        "format": "json",
    }
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    js = r.json()
    rows = [d["data"] for d in js["data"]]
    assert js["meta"]["total"] == len(rows), "paging needed: more rows than one call returns"
    return rows, js["meta"]["index"]["name"]


def main():
    xw = pd.read_csv(CROSSWALK)
    frames, vintages = [], set()
    for row in xw.itertuples():
        flt = f"RSSDHCR:{row.entity_id}" if row.entity_type == "hc" else f"CERT:{row.entity_id}"
        rows, vintage = fetch(flt)
        vintages.add(vintage)
        if not rows:
            raise ValueError(f"No FDIC rows for {row.ticker} ({flt})")
        df = pd.DataFrame(rows)
        df["ticker"] = row.ticker
        frames.append(df)
        print(f"{row.ticker}: {len(df)} bank(s) via {flt}")

    out = pd.concat(frames, ignore_index=True).drop(columns="ID", errors="ignore")
    # One row per bank per quarter, and each bank belongs to exactly one sample entity.
    assert out["CERT"].is_unique, "a bank was pulled for two entities"

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv"
    out.to_csv(path, index=False)
    log_download(path, API, vintage=";".join(sorted(vintages)),
                 note=f"REPDTE={CALL_REPORT_DATE}; filters by RSSDHCR (holding co.) or CERT (bank)")
    print(f"Saved {len(out)} rows to {path}")


if __name__ == "__main__":
    main()
