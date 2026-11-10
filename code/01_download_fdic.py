"""Step 1: pull Q4 2022 call report fields from the FDIC BankFind API for EVERY insured bank.

Outputs:
  data/raw/fdic_financials_20221231.csv    one row per bank (CERT) on the report date
  data/raw/fdic_institutions.csv           CERT -> the bank's own RSSD ID (FED_RSSD), for all banks ever

The holding company link (RSSDHCR) comes from the Q4 2022 record itself, so it is the ownership
on the report date, not today's.
"""
import pandas as pd
import requests

from config import CALL_REPORT_DATE, FDIC_FIELDS, RAW
from provenance import log_download

API = "https://api.fdic.gov/banks"


def fetch_all(endpoint, params):
    """Page through an FDIC endpoint (max 10,000 rows per call)."""
    rows, offset = [], 0
    while True:
        r = requests.get(f"{API}/{endpoint}", params={**params, "limit": 10000, "offset": offset}, timeout=120)
        r.raise_for_status()
        js = r.json()
        rows += [d["data"] for d in js["data"]]
        offset += 10000
        if offset >= js["meta"]["total"]:
            break
    assert len(rows) == js["meta"]["total"]
    return pd.DataFrame(rows).drop(columns="ID", errors="ignore"), js["meta"]["index"]["name"]


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    fin, vintage = fetch_all("financials", {"filters": f"REPDTE:{CALL_REPORT_DATE}",
                                            "fields": ",".join(FDIC_FIELDS),
                                            "sort_by": "CERT", "sort_order": "ASC"})
    assert fin["CERT"].is_unique, "one row per bank per quarter"
    path = RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv"
    fin.to_csv(path, index=False)
    log_download(path, f"{API}/financials", vintage=vintage, note=f"all banks, REPDTE={CALL_REPORT_DATE}")
    print(f"financials: {len(fin)} banks on {CALL_REPORT_DATE}")

    inst, vintage = fetch_all("institutions", {"fields": "CERT,FED_RSSD,NAME",
                                               "sort_by": "CERT", "sort_order": "ASC"})
    assert inst["CERT"].is_unique
    path = RAW / "fdic_institutions.csv"
    inst.to_csv(path, index=False)
    log_download(path, f"{API}/institutions", vintage=vintage, note="CERT -> FED_RSSD, active and inactive banks")
    print(f"institutions: {len(inst)} banks (active and inactive)")


if __name__ == "__main__":
    main()
