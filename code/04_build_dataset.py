"""Step 4: build the final dataset. One row = one listed bank entity in the NY Fed link on Dec 31, 2022.

1. Map every FDIC-insured bank to a sample entity:
   - to its holding company, if the holding company (RSSDHCR on the Q4 2022 report) is in the sample, or
   - to itself, if the bank itself is the listed entity (e.g. First Republic, Signature, Zions).
2. Sum the call report fields across each entity's banks and compute the fragility measures.
3. Merge with CRSP event returns on PERMCO.

Uninsured deposits: the FDIC's estimate (DEPUNINS), which is filled for 4,720 of the 4,773 banks in Q4 2022.
For the few without it, we approximate: amount in accounts over $250K minus $250K x the number of those accounts
(the two agree closely where both exist; see outputs/hand_checks.md).

Outputs:
  data/processed/bank_measures.csv   one row per entity with FDIC data
  outputs/final_dataset.csv          all 343 entities, with flags for why any are out of the sample
"""
import numpy as np
import pandas as pd

from config import CALL_REPORT_DATE, INSURANCE_LIMIT_THOUSANDS, OUTPUTS, PROCESSED, RAW

SUM_FIELDS = ["ASSET", "DEP", "DEPDOM", "uninsured", "uninsured_reported", "EQTOT", "EQCCOMPI",
              "SC", "SCHA", "SCHF", "SCAA", "SCAF"]


def bank_level():
    fin = pd.read_csv(RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv")
    inst = pd.read_csv(RAW / "fdic_institutions.csv")[["CERT", "FED_RSSD"]]
    fin = fin.merge(inst, on="CERT", how="left", validate="1:1")
    assert fin["CERT"].is_unique

    # Uninsured deposits: FDIC estimate where filled, otherwise the over-$250K approximation.
    approx = (fin["DEPLGAMT"] - INSURANCE_LIMIT_THOUSANDS * fin["DEPLGB"]).clip(lower=0)
    fin["uninsured"] = fin["DEPUNINS"].fillna(approx)
    fin["uninsured_reported"] = fin["DEPDOM"].where(fin["DEPUNINS"].notna(), 0)  # deposits covered by an estimate
    return fin


def assign_entities(fin, uni):
    sample = set(uni["rssd_id"])
    via_hc = fin["RSSDHCR"].where(fin["RSSDHCR"].isin(sample))
    via_bank = fin["FED_RSSD"].where(fin["FED_RSSD"].isin(sample))
    # A bank can't be both its own listed entity and owned by a different listed one.
    assert not (via_hc.notna() & via_bank.notna()).any()
    fin["rssd_id"] = via_hc.fillna(via_bank)
    return fin[fin["rssd_id"].notna()].astype({"rssd_id": int})


def measures(banks):
    g = banks.groupby("rssd_id")
    m = g[SUM_FIELDS].sum(min_count=1)
    m["n_banks"] = g.size()
    m["total_assets_bn"] = m["ASSET"] / 1e6
    m["log_assets"] = np.log(m["ASSET"])
    m["uninsured_dep_share"] = m["uninsured"] / m["DEPDOM"]
    m["share_uninsured_reported"] = m["uninsured_reported"] / m["DEPDOM"]
    m["htm_unrealized_loss_bn"] = (m["SCHA"] - m["SCHF"]) / 1e6
    m["afs_unrealized_loss_bn"] = (m["SCAA"] - m["SCAF"]) / 1e6
    # HTM losses are NOT in book equity (HTM is carried at amortized cost): the "hidden" hit.
    m["htm_loss_to_equity"] = (m["SCHA"] - m["SCHF"]) / m["EQTOT"]
    # Alternative: all securities losses. AFS losses already reduced book equity through AOCI.
    m["sec_loss_to_equity"] = ((m["SCHA"] - m["SCHF"]) + (m["SCAA"] - m["SCAF"])) / m["EQTOT"]
    # EQCCOMPI is the annual OCI flow, not the accumulated AOCI balance.
    m["oci_2022_to_equity"] = m["EQCCOMPI"] / m["EQTOT"]
    m["htm_share_of_securities"] = m["SCHA"] / (m["SCHA"] + m["SCAF"])
    return m.reset_index()


def main():
    uni = pd.read_csv(PROCESSED / f"universe_{CALL_REPORT_DATE}.csv")
    assert uni["rssd_id"].is_unique and uni["permco"].is_unique

    banks = assign_entities(bank_level(), uni)
    m = measures(banks)
    rets = pd.read_csv(PROCESSED / "bank_returns.csv")

    final = (uni[["rssd_id", "permco", "name", "inst_type"]]
             .merge(m, on="rssd_id", how="left", validate="1:1")
             .merge(rets, on="permco", how="left", validate="1:1"))
    assert len(final) == len(uni)

    final["has_fdic"] = final["n_banks"].notna()
    final["has_returns"] = final["bhar_0_2"].notna()
    final["positive_equity"] = final["EQTOT"] > 0
    final["in_sample"] = final["has_fdic"] & final["has_returns"] & final["positive_equity"]

    cols = ["rssd_id", "permco", "permno", "ticker", "name", "inst_type", "n_banks", "total_assets_bn",
            "log_assets", "uninsured_dep_share", "share_uninsured_reported", "htm_unrealized_loss_bn",
            "afs_unrealized_loss_bn", "htm_loss_to_equity", "sec_loss_to_equity", "oci_2022_to_equity",
            "htm_share_of_securities", "n_event_days", "delisted_in_window", "dlret_imputed", "beta", "est_obs",
            "bhr_0_2", "bhar_0_2", "car_0_2", "has_fdic", "has_returns", "positive_equity", "in_sample"]
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    m.to_csv(PROCESSED / "bank_measures.csv", index=False)
    final[cols].to_csv(OUTPUTS / "final_dataset.csv", index=False)

    print(f"{len(final)} entities | FDIC match: {final['has_fdic'].sum()} | CRSP event returns: "
          f"{final['has_returns'].sum()} | positive equity: {final['positive_equity'].sum()} | "
          f"IN SAMPLE: {final['in_sample'].sum()}")
    print("not matched to FDIC:", ", ".join(final.loc[~final["has_fdic"], "name"].str.title()))

    # Range checks. These values are possible in the data but suspicious, so we list them on every run
    # instead of hiding them. They are known, open issues (README threats 4, 5 and 8; audits/01_self_audit.md).
    s = final[final["in_sample"]]
    for col, limit, why in [("uninsured_dep_share", 1.0, "a share above 100%"),
                            ("sec_loss_to_equity", 1.0, "securities losses larger than equity"),
                            ("htm_loss_to_equity", 1.0, "HTM losses larger than equity")]:
        out = s.loc[s[col] > limit, ["ticker", col]].sort_values(col, ascending=False)
        if len(out):
            print(f"RANGE WARNING, {why} ({col} > {limit:g}): "
                  + ", ".join(f"{t} {v:.2f}" for t, v in out.itertuples(index=False)))


if __name__ == "__main__":
    main()
