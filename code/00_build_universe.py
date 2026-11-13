"""Step 0: build the sample universe, every listed bank entity linked to CRSP on the call report date.

Source: the NY Fed CRSP-FRB link (RSSD ID -> CRSP PERMCO, with link start/end dates).
We keep links active on CALL_REPORT_DATE, so banks that failed or merged later stay in the sample.

Outputs:
  data/raw/nyfed_crsp_frb_link.csv            the raw link file
  data/processed/universe_20221231.csv        one row per linked entity (key: rssd_id, also unique on permco)
  requests/crsp_permcos.csv                   the PERMCO list we send to the professor for CRSP returns
"""
import pandas as pd
import requests

from config import CALL_REPORT_DATE, NYFED_LINK_URL, NYFED_LINK_VINTAGE_END, PROCESSED, RAW, REQUESTS
from provenance import log_download


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    raw_path = RAW / "nyfed_crsp_frb_link.csv"
    # The NY Fed site rejects requests with no browser-like User-Agent.
    r = requests.get(NYFED_LINK_URL, headers={"User-Agent": "Mozilla/5.0 (FIN331 class project)"}, timeout=60)
    r.raise_for_status()
    raw_path.write_bytes(r.content)
    log_download(raw_path, NYFED_LINK_URL, vintage="crsp_20240930v2", note="RSSD -> PERMCO link with date ranges")

    link = pd.read_csv(raw_path)
    d = int(CALL_REPORT_DATE)
    uni = link[(link["dt_start"] <= d) & (link["dt_end"] >= d)].rename(columns={"entity": "rssd_id"})
    # One row = one listed entity. Both IDs must be unique, or a bank would be double counted.
    assert uni["rssd_id"].is_unique and uni["permco"].is_unique
    # Links that end after the call report date but before today mark banks that failed, merged, or delisted.
    uni["link_ends_by_2024"] = uni["dt_end"] < NYFED_LINK_VINTAGE_END

    PROCESSED.mkdir(parents=True, exist_ok=True)
    REQUESTS.mkdir(parents=True, exist_ok=True)
    uni.to_csv(PROCESSED / f"universe_{CALL_REPORT_DATE}.csv", index=False)
    uni[["permco", "name", "rssd_id"]].sort_values("permco").to_csv(REQUESTS / "crsp_permcos.csv", index=False)

    print(f"{len(uni)} entities linked on {CALL_REPORT_DATE}; "
          f"{uni['link_ends_by_2024'].sum()} links end before Sep 30, 2024 (failed, merged, or delisted)")
    print(uni["inst_type"].str.title().value_counts().to_string())


if __name__ == "__main__":
    main()
