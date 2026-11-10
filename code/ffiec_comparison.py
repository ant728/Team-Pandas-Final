"""Compare selected Q4 2022 FDIC API aggregates with the FFIEC CDR bulk file."""
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from config import OUTPUTS, PROCESSED, RAW, ROOT

FFIEC_ZIP = RAW / "ffiec_call_20221231.zip"
CERT_CROSSWALK = ROOT / "inputs" / "ffiec_compare_certificates.csv"
FIELDS = {
    "ASSET": ("RCFD2170", "RCON2170"),
    "DEPUNINS": ("RCON5597",),
    "SCHA": ("RCFD1754", "RCON1754"),
    "SCHF": ("RCFD1771", "RCON1771"),
    "SCAA": ("RCFD1772", "RCON1772"),
    "SCAF": ("RCFD1773_RCB", "RCON1773_RCB"),
}
TOLERANCE_THOUSANDS = 1.0


def read_tsv(zf: ZipFile, member: str) -> pd.DataFrame:
    # FFIEC tab-delimited files have a field-code header, a description row, then data.
    with zf.open(member) as stream:
        return pd.read_csv(stream, sep="\t", skiprows=[1], dtype={"IDRSSD": "string"})


def _members(zf: ZipFile) -> list[str]:
    return [name for name in zf.namelist() if name.endswith(".txt")]


def _read_member_with_fields(zf: ZipFile, members: list[str], prefix: str, fields: set[str]) -> pd.DataFrame:
    for member in members:
        if Path(member).name.startswith(prefix):
            df = read_tsv(zf, member)
            if fields.issubset(df.columns):
                return df
    raise ValueError(f"No FFIEC member beginning {prefix!r} contains fields {sorted(fields)}")


def _first_reported(row: pd.Series, candidates: tuple[str, ...]) -> float:
    for field in candidates:
        if field not in row.index:
            continue
        value = pd.to_numeric(pd.Series([row[field]]), errors="coerce").iloc[0]
        if pd.notna(value):
            return float(value)
    return float("nan")


def comparison_table() -> pd.DataFrame:
    if not FFIEC_ZIP.exists():
        raise FileNotFoundError(f"Missing local FFIEC file: {FFIEC_ZIP}")
    certs = pd.read_csv(CERT_CROSSWALK, dtype={"CERT": "string"})
    if certs["CERT"].duplicated().any():
        raise ValueError("The FFIEC comparison CERT crosswalk contains duplicates")

    fdic = pd.read_csv(PROCESSED / "bank_measures.csv").set_index("ticker")
    required_fdic = set(FIELDS)
    missing_fdic = required_fdic - set(fdic.columns)
    if missing_fdic:
        raise ValueError(f"FDIC API measures are missing columns: {sorted(missing_fdic)}")
    missing_tickers = set(certs["ticker"]) - set(fdic.index)
    if missing_tickers:
        raise ValueError(f"Selected entities are missing from FDIC measures: {sorted(missing_tickers)}")

    with ZipFile(FFIEC_ZIP) as zf:
        members = _members(zf)
        por = _read_member_with_fields(
            zf, members, "FFIEC CDR Call Bulk POR", {"IDRSSD", "FDIC Certificate Number", "Financial Institution Name"}
        )
        por["CERT"] = pd.to_numeric(por["FDIC Certificate Number"], errors="coerce").astype("Int64").astype("string")
        certs["CERT"] = certs["CERT"].str.strip()
        entity = certs.merge(por[["CERT", "IDRSSD", "Financial Institution Name"]],
                             on="CERT", how="left", validate="m:1")
        if entity["IDRSSD"].isna().any():
            missing = entity.loc[entity["IDRSSD"].isna(), "CERT"].tolist()
            raise ValueError(f"FFIEC POR did not contain selected FDIC CERTs: {missing}")
        if entity.duplicated(["ticker", "IDRSSD"]).any():
            raise ValueError("Selected FFIEC bank records are duplicated")

        rc = _read_member_with_fields(zf, members, "FFIEC CDR Call Schedule RC ", {"IDRSSD", "RCFD2170", "RCON2170"})
        rcb = _read_member_with_fields(zf, members, "FFIEC CDR Call Schedule RCB ",
                                       {"IDRSSD", "RCFD1754", "RCFD1771", "RCFD1772", "RCFD1773"})
        rco = _read_member_with_fields(zf, members, "FFIEC CDR Call Schedule RCO ", {"IDRSSD", "RCON5597"})
        for schedule, name in [(rc, "RC"), (rcb, "RC-B"), (rco, "RC-O")]:
            if schedule["IDRSSD"].duplicated().any():
                raise ValueError(f"FFIEC {name} schedule has duplicate IDRSSD rows")
        ffiec = entity.merge(rc, on="IDRSSD", how="left", validate="m:1", suffixes=("", "_RC"))
        ffiec = ffiec.merge(rcb, on="IDRSSD", how="left", validate="m:1", suffixes=("", "_RCB"))
        ffiec = ffiec.merge(rco[["IDRSSD", "RCON5597"]], on="IDRSSD", how="left", validate="m:1")

    rows = []
    for ticker, group in ffiec.groupby("ticker", sort=True):
        for field, source_codes in FIELDS.items():
            vals = [_first_reported(row, source_codes) for _, row in group.iterrows()]
            if any(pd.isna(value) for value in vals):
                raise ValueError(f"Missing FFIEC {field} value for {ticker}; values={vals}")
            ffiec_value = float(sum(vals))
            fdic_value = float(fdic.at[ticker, field])
            difference = ffiec_value - fdic_value
            status = "PASS" if abs(difference) <= TOLERANCE_THOUSANDS else "FAIL"
            rows.append({"ticker": ticker, "field": field, "fdic_api": fdic_value,
                         "ffiec_cdr": ffiec_value, "difference": difference,
                         "tolerance": TOLERANCE_THOUSANDS, "result": status,
                         "certs": ", ".join(group["CERT"].astype(str)),
                         "bank_reports": "; ".join(group["Financial Institution Name"].astype(str))})
    return pd.DataFrame(rows)


def write_report(table: pd.DataFrame) -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    report = OUTPUTS / "ffiec_fdic_comparison.md"
    if table.empty:
        report.write_text("# FDIC API vs. FFIEC CDR comparison\n\nNo comparison was run.\n", encoding="utf-8")
        return report

    entities = table["ticker"].nunique()
    bank_count = pd.read_csv(CERT_CROSSWALK)["CERT"].nunique()
    passes = int((table["result"] == "PASS").sum())
    checks = len(table)
    exact = bool((table["difference"] == 0).all())
    if passes == checks and exact:
        summary = (f"Across {entities} listed entities ({bank_count} bank filings), all {checks} "
                   "Q4 2022 field comparisons matched exactly.")
    elif passes == checks:
        summary = (f"Across {entities} listed entities ({bank_count} bank filings), all {checks} "
                   f"comparisons matched within ${TOLERANCE_THOUSANDS:,.0f} thousand.")
    else:
        summary = (f"{passes} of {checks} comparisons passed; the differences are shown below.")

    lines = [
        "# FDIC API vs. FFIEC CDR comparison", "",
        "Q4 2022 (report date 2022-12-31), current FFIEC CDR bulk snapshot downloaded 2026-11-10.",
        "Amounts are $ thousands. For consolidated reporters the comparison uses RCFD values where available, otherwise RCON; uninsured deposits use RCON5597.",
        "FFIEC banks are matched to the FDIC API entity using the FDIC certificate numbers in the input crosswalk.", "",
        summary, "",
        "| Entity | Field | FDIC API | FFIEC CDR | Difference | Result | CERT(s) |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in table.itertuples(index=False):
        lines.append(f"| {row.ticker} | {row.field} | {row.fdic_api:,.0f} | {row.ffiec_cdr:,.0f} | "
                     f"{row.difference:,.0f} | {row.result} | {row.certs} |")
    lines += ["", "Field mapping: `ASSET` = RCFD2170/RCON2170; `DEPUNINS` = RCON5597; "
              "`SCHA` = RCFD1754/RCON1754; `SCHF` = RCFD1771/RCON1771; "
              "`SCAA` = RCFD1772/RCON1772; `SCAF` = RCFD1773/RCON1773.", ""]
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = comparison_table()
    path = write_report(result)
    print(result[["ticker", "field", "fdic_api", "ffiec_cdr", "difference", "result"]].to_string(index=False))
    print(f"\nWrote {path}")
    failed = result.loc[result["result"] != "PASS", ["ticker", "field", "difference"]]
    if not failed.empty:
        raise AssertionError(f"FDIC/FFIEC comparisons failed:\n{failed.to_string(index=False)}")
