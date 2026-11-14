"""Step 6: recompute numbers from each pipeline step another way, and compare.

Writes outputs/hand_checks.md and raises if any check fails.
"""
import csv

import numpy as np
import pandas as pd

from config import CALL_REPORT_DATE, CRSP_DAILY, CRSP_MARKET, INSURANCE_LIMIT_THOUSANDS, OUTPUTS, RAW
from ffiec_comparison import FFIEC_ZIP, comparison_table, write_report as write_ffiec_report

final = pd.read_csv(OUTPUTS / "final_dataset.csv").set_index("ticker")
results = []


def check(name, ours, theirs, tol, source):
    ok = abs(ours - theirs) <= tol
    results.append((name, ours, theirs, tol, "PASS" if ok else "FAIL", source))


def skip(name, reason):
    results.append((name, None, None, None, "SKIPPED", reason))


# --- Step 0: universe size, recounted from the raw NY Fed link with a plain loop -------------
d = int(CALL_REPORT_DATE)
with open(RAW / "nyfed_crsp_frb_link.csv", newline="") as f:
    n_active = sum(1 for r in csv.DictReader(f) if int(r["dt_start"]) <= d <= int(r["dt_end"]))
check(f"Entities in the NY Fed link on {CALL_REPORT_DATE}, counted by hand", len(final), n_active, 0,
      "raw nyfed_crsp_frb_link.csv rows with dt_start <= date <= dt_end")


# --- Call report measures vs. published SVB figures -----------------------------------------
check("SVB uninsured share of domestic deposits", final.at["SIVB", "uninsured_dep_share"], 0.94, 0.01,
      "Fed's Review of the Supervision and Regulation of SVB (Apr 2023): about 94% of domestic deposits uninsured")
check("SVB HTM unrealized loss ($B)", final.at["SIVB", "htm_unrealized_loss_bn"], 15.1, 0.3,
      "SVB Financial Group 2022 10-K: HTM fair value about $15.1B below amortized cost")

# --- Aggregation across a holding company's banks, recomputed with a plain loop --------------
with open(RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv", newline="") as f:
    jpm = sum(float(r["ASSET"]) for r in csv.DictReader(f) if r["RSSDHCR"] == "1039502") / 1e6
check("JPM total assets ($B), summed by hand", final.at["JPM", "total_assets_bn"], jpm, 1e-3,
      "raw FDIC rows with RSSDHCR = 1039502 (JPMorgan Chase & Co.)")

# --- Uninsured-deposit approximation vs. the reported estimate -------------------------------
fin = pd.read_csv(RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv")
rep = fin[fin["DEPUNINS"].notna() & (fin["DEPDOM"] > 0)]
approx = (rep["DEPLGAMT"] - INSURANCE_LIMIT_THOUSANDS * rep["DEPLGB"]).clip(lower=0) / rep["DEPDOM"]
corr = approx.corr(rep["DEPUNINS"] / rep["DEPDOM"])
check(f"Over-$250K approximation vs. reported uninsured share: correlation across {len(rep)} banks",
      corr, 1.0, 0.2, "banks that file both (we use the approximation only for banks that don't report)")

# --- CRSP returns vs. yfinance, Mar 8 close to Mar 13 close (raw, not abnormal) ---------------
prices = RAW / "prices_check.csv"
px = (pd.read_csv(prices, parse_dates=["date"]).pivot(index="date", columns="symbol", values="close")
      if prices.exists() else pd.DataFrame())
for t in ["JPM", "WAL", "ZION"]:
    name = f"{t} 3-day buy-and-hold return: CRSP vs. yfinance"
    try:
        yf_bhr = px.at[pd.Timestamp("2023-03-13"), t] / px.at[pd.Timestamp("2023-03-08"), t] - 1
    except KeyError:  # step 2 could not download this symbol (yfinance is optional)
        skip(name, "yfinance prices not available on this run (see step 2 warnings)")
        continue
    check(name, final.at[t, "bhr_0_2"], yf_bhr, 0.005, "yfinance adjusted closes (independent source)")

# --- WAL's BHAR recomputed from the raw CRSP rows with a plain loop --------------------------
days = ["2023-03-09", "2023-03-10", "2023-03-13"]
wal, mkt = 1.0, 1.0
with open(CRSP_DAILY, newline="") as f:
    for r in csv.DictReader(f):
        if r["ticker"] == "WAL" and r["date"] in days:
            wal *= 1 + float(r["ret"])
with open(CRSP_MARKET, newline="") as f:
    for r in csv.DictReader(f):
        if r["date"] in days:
            mkt *= 1 + float(r["vwretd"])
check("WAL BHAR[0,+2], recomputed from raw CRSP rows", final.at["WAL", "bhar_0_2"], (wal - 1) - (mkt - 1), 1e-4,
      "crsp_daily_2022_2023.csv and crsp_market_vwretd.csv")

# --- SVB's delisting treatment -----------------------------------------------------------------
check("SVB buy-and-hold return with -100% delisting return", final.at["SIVB", "bhr_0_2"], -1.0, 1e-9,
      "our assumption for the missing delisting return (config.MISSING_DLRET_FAILED)")

# --- Step 5: R1 recomputed with plain numpy (OLS by least squares, HC3 by the sandwich formula) --
s = final[final["in_sample"]]
X = np.column_stack([np.ones(len(s)), s["uninsured_dep_share"], s["htm_loss_to_equity"], s["log_assets"]])
y = s["bhar_0_2"].to_numpy()
b = np.linalg.lstsq(X, y, rcond=None)[0]
e = y - X @ b
XtX_inv = np.linalg.inv(X.T @ X)
h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)           # leverage of each bank
meat = X.T @ (X * (e ** 2 / (1 - h) ** 2)[:, None])
se_hc3 = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv))
reg = pd.read_csv(OUTPUTS / "regressions_v0.csv")
r1 = reg[reg["spec"].str.startswith("R1") & reg["variable"].eq("uninsured_dep_share")].iloc[0]
check("R1 uninsured-share coefficient, recomputed with numpy", r1["coef"], b[1], 1e-5,
      "numpy least squares on outputs/final_dataset.csv (in-sample rows)")
check("R1 uninsured-share HC3 standard error, recomputed by hand", r1["se"], se_hc3[1], 1e-5,
      "HC3 sandwich formula in numpy: (X'X)^-1 X' diag(e^2/(1-h)^2) X (X'X)^-1")

# --- FDIC API values vs. the FFIEC CDR Q4 2022 bulk file -------------------------------------
if FFIEC_ZIP.exists():
    ffiec = comparison_table()
    for row in ffiec.itertuples(index=False):
        check(f"{row.ticker} {row.field}: FDIC API vs. FFIEC CDR",
              row.fdic_api, row.ffiec_cdr, row.tolerance,
              f"FFIEC CERT(s) {row.certs}; {row.bank_reports}")
    write_ffiec_report(ffiec)
else:
    skip("FDIC API vs. FFIEC CDR Q4 2022 comparison",
         f"Local input not present: {FFIEC_ZIP.relative_to(RAW.parent.parent).as_posix()} "
         "(manual download, see README provenance); last result in outputs/ffiec_fdic_comparison.md")

# --- Write report ------------------------------------------------------------------------------
lines = ["# Hand checks", "",
         "Generated by `code/06_hand_checks.py`. Each number from the pipeline is recomputed another way.", "",
         "| Check | Pipeline | Independent | Tolerance | Result | Source of independent number |",
         "|---|---|---|---|---|---|"]
for name, ours, theirs, tol, res, src in results:
    if res == "SKIPPED":
        pipeline, independent, tolerance = "—", "—", "—"
    else:
        pipeline, independent, tolerance = f"{ours:.4f}", f"{theirs:.4f}", f"{tol:g}"
    lines.append(f"| {name} | {pipeline} | {independent} | {tolerance} | {res} | {src} |")
(OUTPUTS / "hand_checks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))

failed = [r[0] for r in results if r[4] == "FAIL"]
assert not failed, f"hand checks failed: {failed}"
