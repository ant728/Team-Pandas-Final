"""Step 4: build the final dataset. One row = one listed bank entity in the NY Fed link on Dec 31, 2022.

1. Map every FDIC-insured bank to a sample entity (specs_tried.md #13, instructor audit A4):
   - to itself, if the bank itself is the listed entity (e.g. First Republic, Signature, Zions), or
   - to the HIGHEST listed entity that controls it on Dec 31, 2022, walking up the FFIEC NIC relationships
     file. Before this, we used only the bank's top-tier holder (RSSDHCR), which misses a listed company
     that sits below an unlisted parent (e.g. a listed mid-tier company owned by a mutual holding company).
   - A bank controlled by ANOTHER insured bank is left out of the sums: the parent bank's consolidated call
     report already includes it (specs_tried.md #15).
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

from config import (BANK_CENTRIC_MIN_EQ_TO_MCAP, BANKING_NAICS_PREFIXES, CALL_REPORT_DATE, EVENT_TRIGGER_TICKERS,
                    INSURANCE_LIMIT_THOUSANDS, INTERIM, NIC_DIR, NIC_RELATIONSHIPS, OUTPUTS, PROCESSED, RAW)

SUM_FIELDS = ["ASSET", "DEP", "DEPDOM", "uninsured", "uninsured_reported", "EQTOT", "EQCCOMPI",
              "SC", "SCHA", "SCHF", "SCAA", "SCAF"]


def bank_level(date=CALL_REPORT_DATE):
    fin = pd.read_csv(RAW / f"fdic_financials_{date}.csv")
    inst = pd.read_csv(RAW / "fdic_institutions.csv")[["CERT", "FED_RSSD"]]
    fin = fin.merge(inst, on="CERT", how="left", validate="1:1")
    assert fin["CERT"].is_unique

    # Uninsured deposits: FDIC estimate where filled, otherwise the over-$250K approximation.
    approx = (fin["DEPLGAMT"] - INSURANCE_LIMIT_THOUSANDS * fin["DEPLGB"]).clip(lower=0)
    fin["uninsured"] = fin["DEPUNINS"].fillna(approx)
    fin["uninsured_reported"] = fin["DEPDOM"].where(fin["DEPUNINS"].notna(), 0)  # deposits covered by an estimate
    return fin


def controlling_parents(date=CALL_REPORT_DATE):
    """offspring RSSD -> its controlling parents' RSSDs, for relationships active on the call report date."""
    files = [NIC_RELATIONSHIPS]
    if not NIC_RELATIONSHIPS.exists():
        raise FileNotFoundError(
            f"No NIC relationships file at {NIC_RELATIONSHIPS}. Download 'Relationships' (CSV) from "
            "https://www.ffiec.gov/npw/FinancialReport/DataDownload (manual: the site uses a CAPTCHA) "
            "and save the ZIP there. See README provenance.")
    rel = pd.read_csv(files[0], low_memory=False)
    rel.columns = rel.columns.str.lstrip("#").str.strip()
    d = int(date)
    active = rel[(rel["CTRL_IND"] == 1) & (rel["DT_START"] <= d) & (rel["DT_END"] >= d)]
    print(f"NIC relationships: {len(rel)} rows, {len(active)} controlling and active on {date} "
          f"({files[0].name})")
    return active.groupby("ID_RSSD_OFFSPRING")["ID_RSSD_PARENT"].apply(list).to_dict()


def nic_primary_activity():
    """RSSD -> primary activity code (NAICS) from the NIC attributes files (active and closed entities)."""
    files = [NIC_DIR / "CSV_ATTRIBUTES_ACTIVE.zip", NIC_DIR / "CSV_ATTRIBUTES_CLOSED.zip"]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        raise FileNotFoundError(f"Missing {missing} in {NIC_DIR}: download 'Attributes- Active' and 'Attributes- Closed' "
                                "(CSV) from https://www.ffiec.gov/npw/FinancialReport/DataDownload. See README provenance.")
    att = pd.concat([pd.read_csv(f, dtype=str, encoding="latin-1", low_memory=False) for f in files])
    att.columns = att.columns.str.lstrip("#").str.strip()
    att["ID_RSSD"] = att["ID_RSSD"].astype(int)
    assert att["ID_RSSD"].is_unique, "one attributes row per institution"
    return att.set_index("ID_RSSD")["ACT_PRIM_CD"].str.strip()


def listed_controller(rssd, parents, sample):
    """The highest (farthest up) listed entity that controls this institution, or None."""
    best, best_depth, seen, frontier, depth = set(), -1, {rssd}, [rssd], 0
    while frontier:
        depth += 1
        frontier = [p for x in frontier for p in parents.get(x, []) if p not in seen]
        seen.update(frontier)
        listed = {p for p in frontier if p in sample}
        if listed:
            best, best_depth = listed, depth
    assert len(best) <= 1, f"RSSD {rssd} is controlled by two listed entities at the same level: {best}"
    return next(iter(best), None)


def assign_entities(fin, uni, date=CALL_REPORT_DATE):
    sample = set(uni["rssd_id"])
    parents = controlling_parents(date)
    via_bank = fin["FED_RSSD"].where(fin["FED_RSSD"].isin(sample))
    via_nic = fin["FED_RSSD"].map(lambda r: listed_controller(r, parents, sample) if pd.notna(r) else None)
    # A bank can't be both its own listed entity and owned by a different listed one.
    clash = via_bank.notna() & via_nic.notna()
    assert not clash.any(), f"listed banks also controlled by a listed company: {fin.loc[clash, 'NAME'].tolist()}"
    fin["rssd_id"] = via_bank.fillna(via_nic)

    # Bank-owned banks are already inside their parent bank's consolidated call report (specs_tried.md #15).
    bank_ids = set(fin["FED_RSSD"].dropna())
    owned_by_bank = fin["FED_RSSD"].map(lambda r: any(p in bank_ids for p in parents.get(r, [])))
    dropped = fin[owned_by_bank & fin["rssd_id"].notna()]
    if len(dropped):
        print("Left out of the sums (already in their parent bank's report): "
              + ", ".join(f"{n.title()} -> entity {int(e)}" for n, e in dropped[["NAME", "rssd_id"]].itertuples(index=False)))
    fin.loc[owned_by_bank, "rssd_id"] = np.nan
    fin["fdic_link"] = np.where(via_bank.notna(), "bank itself", "controlling company (NIC)")

    # The old rule, kept only to report what changed: the top-tier holder (RSSDHCR) if it is in the sample.
    old = fin["RSSDHCR"].where(fin["RSSDHCR"].isin(sample)).fillna(via_bank)
    differ = old.notna() & fin["rssd_id"].notna() & (old != fin["rssd_id"])
    assert not differ.any(), f"NIC walk disagrees with RSSDHCR for: {fin.loc[differ, 'NAME'].tolist()}"
    fin["old_rule_match"] = old.notna()
    return fin[fin["rssd_id"].notna()].astype({"rssd_id": int})


def measures(banks):
    g = banks.groupby("rssd_id")
    m = g[SUM_FIELDS].sum(min_count=1)
    m["n_banks"] = g.size()
    m["n_banks_old_rule"] = g["old_rule_match"].sum()  # for reporting what the NIC walk changed
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
    # Which bank belongs to which listed entity, for matching failed banks in the screen (step 8).
    banks[["CERT", "FED_RSSD", "NAME", "rssd_id"]].to_csv(PROCESSED / "bank_entity_map.csv", index=False)
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
    # Main sample (specs_tried.md #17): in_sample minus the bank that triggered the event (SVB).
    trigger = final["ticker"].isin(EVENT_TRIGGER_TICKERS)
    assert trigger.sum() == len(EVENT_TRIGGER_TICKERS), "each event-trigger ticker should match exactly one entity"
    final["main_sample"] = final["in_sample"] & ~trigger

    # Bank-centric sample for R10 (specs_tried.md #20): drop entities whose banks are a small part of the company.
    mcap = pd.read_csv(INTERIM / "mcap_20221230.csv").set_index("permco")["mcap_thousands"]
    final["bank_eq_to_mcap"] = final["EQTOT"] / final["permco"].map(mcap)
    final["nic_primary_activity"] = final["rssd_id"].map(nic_primary_activity())
    nonbank_code = final["nic_primary_activity"].notna() & ~final["nic_primary_activity"].str.startswith(BANKING_NAICS_PREFIXES, na=False)
    small_bank = final["bank_eq_to_mcap"] < BANK_CENTRIC_MIN_EQ_TO_MCAP
    final["bank_centric"] = final["main_sample"] & ~nonbank_code & ~small_bank
    dropped = final[final["main_sample"] & ~final["bank_centric"]]
    print(f"Bank-centric sample: {final['bank_centric'].sum()} of {final['main_sample'].sum()} main-sample entities. Dropped: "
          + ", ".join(f"{t} ({'equity ' + format(r, '.1%') + ' of market value' if r < BANK_CENTRIC_MIN_EQ_TO_MCAP else 'NAICS ' + c})"
                      for t, r, c in dropped[["ticker", "bank_eq_to_mcap", "nic_primary_activity"]].itertuples(index=False)))

    cols = ["rssd_id", "permco", "permno", "ticker", "name", "inst_type", "n_banks", "total_assets_bn",
            "log_assets", "uninsured_dep_share", "share_uninsured_reported", "htm_unrealized_loss_bn",
            "afs_unrealized_loss_bn", "htm_loss_to_equity", "sec_loss_to_equity", "oci_2022_to_equity",
            "htm_share_of_securities", "n_event_days", "delisted_in_window", "dlret_imputed", "beta", "kre_beta", "est_obs",
            "bhr_0_2", "bhar_0_2", "bhr_0_1", "bhar_0_1", "car_0_2", "has_fdic", "has_returns", "positive_equity", "in_sample",
            "main_sample", "bank_eq_to_mcap", "nic_primary_activity", "bank_centric"]
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    m.to_csv(PROCESSED / "bank_measures.csv", index=False)
    final[cols].to_csv(OUTPUTS / "final_dataset.csv", index=False)

    print(f"{len(final)} entities | FDIC match: {final['has_fdic'].sum()} | CRSP event returns: "
          f"{final['has_returns'].sum()} | positive equity: {final['positive_equity'].sum()} | "
          f"IN SAMPLE: {final['in_sample'].sum()} | MAIN SAMPLE (without SVB): {final['main_sample'].sum()}")
    old = final["n_banks_old_rule"].fillna(0) > 0
    grew = final[old & (final["n_banks"] > final["n_banks_old_rule"])]
    print(f"FDIC match rate: {old.sum()}/{len(final)} with the top-tier-holder rule -> "
          f"{final['has_fdic'].sum()}/{len(final)} with the NIC walk. Newly matched: "
          + ", ".join(final.loc[final["has_fdic"] & ~old, "name"].str.title()))
    print(f"Entities that gained banks under the NIC walk: {len(grew)}"
          + (" (" + ", ".join(grew["name"].str.title()) + ")" if len(grew) else ""))
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
