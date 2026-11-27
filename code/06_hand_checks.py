"""Step 6: recompute numbers from each pipeline step another way, and compare.

Writes outputs/hand_checks.md and raises if any check fails.
"""
import csv
import io
import zipfile

import numpy as np
import pandas as pd

from config import (CALL_REPORT_DATE, CRSP_DAILY, CRSP_MARKET, ESTIMATION_WINDOW, EVENT_DAY0, INSURANCE_LIMIT_THOUSANDS,
                    KRE_PRICES, NIC_RELATIONSHIPS, OUTPUTS, RAW, TODAY_CALL_REPORT_DATE)
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

# --- NIC link (instructor audit A4): TFS Financial, a listed company under a mutual holding company --
# The old rule (top-tier holder) missed it. Rebuild its assets from the raw NIC and FDIC files with plain loops.
tfsl = int(final.at["TFSL", "rssd_id"])
with zipfile.ZipFile(NIC_RELATIONSHIPS) as z, z.open(z.namelist()[0]) as f:
    kids = {int(r["ID_RSSD_OFFSPRING"]) for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            if int(r["#ID_RSSD_PARENT"]) == tfsl and r["CTRL_IND"] == "1"
            and int(r["DT_START"]) <= d <= int(r["DT_END"])}
with open(RAW / "fdic_institutions.csv", newline="") as f:
    certs = {r["CERT"] for r in csv.DictReader(f) if r["FED_RSSD"] and int(float(r["FED_RSSD"])) in kids}
with open(RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv", newline="") as f:
    tfsl_assets = sum(float(r["ASSET"]) for r in csv.DictReader(f) if r["CERT"] in certs) / 1e6
check("TFS Financial total assets ($B), via NIC ownership rows", final.at["TFSL", "total_assets_bn"], tfsl_assets, 1e-3,
      "raw NIC relationships (banks TFS Financial controls on 2022-12-31) and raw FDIC rows")

# --- Bank-centric rule (R10): Schwab's bank equity / market value, from raw FDIC and CRSP rows --
schw = final.at["SCHW", "rssd_id"]
with open(RAW / f"fdic_financials_{CALL_REPORT_DATE}.csv", newline="") as f:
    schw_eq = sum(float(r["EQTOT"]) for r in csv.DictReader(f) if r["RSSDHCR"] and int(float(r["RSSDHCR"])) == schw)
with open(CRSP_DAILY, newline="") as f:
    schw_mcap = sum(abs(float(r["prc"])) * float(r["shrout"]) for r in csv.DictReader(f)
                    if r["ticker"] == "SCHW" and r["date"] == "2022-12-30")
check("Schwab bank equity / market value (bank-centric rule, R10)", final.at["SCHW", "bank_eq_to_mcap"],
      schw_eq / schw_mcap, 1e-6, "raw FDIC rows with RSSDHCR = Schwab, and CRSP price x shares on 2022-12-30")

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
for col, days in [("bhar_0_2", ["2023-03-09", "2023-03-10", "2023-03-13"]),
                  ("bhar_0_1", ["2023-03-09", "2023-03-10"])]:  # R7's pre-rescue window (specs_tried.md #18)
    wal, mkt = 1.0, 1.0
    with open(CRSP_DAILY, newline="") as f:
        for r in csv.DictReader(f):
            if r["ticker"] == "WAL" and r["date"] in days:
                wal *= 1 + float(r["ret"])
    with open(CRSP_MARKET, newline="") as f:
        for r in csv.DictReader(f):
            if r["date"] in days:
                mkt *= 1 + float(r["vwretd"])
    check(f"WAL {col}, recomputed from raw CRSP rows", final.at["WAL", col], (wal - 1) - (mkt - 1), 1e-4,
          "crsp_daily_2022_2023.csv and crsp_market_vwretd.csv")

# --- WAL's KRE beta (spec R5) recomputed as cov/var with a plain loop --------------------------
kre_px = {}
with open(KRE_PRICES, newline="") as f:
    for r in csv.DictReader(f):
        kre_px[r["date"][:10]] = float(r["close"])
kre_dates = sorted(kre_px)
kre_ret = {d1: kre_px[d1] / kre_px[d0] - 1 for d0, d1 in zip(kre_dates, kre_dates[1:])}
with open(CRSP_MARKET, newline="") as f:
    cal = sorted(r["date"] for r in csv.DictReader(f))
i0 = cal.index(EVENT_DAY0)
est_days = set(cal[i0 + ESTIMATION_WINDOW[0]: i0 + ESTIMATION_WINDOW[1] + 1])
pairs = []
with open(CRSP_DAILY, newline="") as f:
    for r in csv.DictReader(f):
        if r["ticker"] == "WAL" and r["date"] in est_days and r["ret"] not in ("", "C", "B"):
            pairs.append((kre_ret[r["date"]], float(r["ret"])))
mx = sum(x for x, _ in pairs) / len(pairs)
my = sum(y for _, y in pairs) / len(pairs)
wal_kre_beta = sum((x - mx) * (y - my) for x, y in pairs) / sum((x - mx) ** 2 for x, _ in pairs)
check("WAL beta to KRE, recomputed as cov/var from raw files", final.at["WAL", "kre_beta"], wal_kre_beta, 1e-8,
      "crsp_daily_2022_2023.csv and kre_daily.csv, trading days -250 to -30")

# --- SVB's delisting treatment -----------------------------------------------------------------
check("SVB buy-and-hold return with -100% delisting return", final.at["SIVB", "bhr_0_2"], -1.0, 1e-9,
      "our assumption for the missing delisting return (config.MISSING_DLRET_FAILED)")

# --- Step 5: R1 recomputed with plain numpy (OLS by least squares, HC3 by the sandwich formula) --
s = final[final["main_sample"]]  # R1 runs on the main sample (specs_tried.md #17)
X = np.column_stack([np.ones(len(s)), s["uninsured_dep_share"], s["htm_loss_to_equity"], s["log_assets"]])
y = s["bhar_0_2"].to_numpy()
b = np.linalg.lstsq(X, y, rcond=None)[0]
e = y - X @ b
XtX_inv = np.linalg.inv(X.T @ X)
h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)           # leverage of each bank
meat = X.T @ (X * (e ** 2 / (1 - h) ** 2)[:, None])
se_hc3 = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv))
reg = pd.read_csv(OUTPUTS / "regressions.csv")
r1 = reg[reg["spec"].str.startswith("R1") & reg["variable"].eq("uninsured_dep_share")].iloc[0]
check("R1 uninsured-share coefficient, recomputed with numpy", r1["coef"], b[1], 1e-5,
      "numpy least squares on outputs/final_dataset.csv (in-sample rows)")
check("R1 uninsured-share HC3 standard error, recomputed by hand", r1["se"], se_hc3[1], 1e-5,
      "HC3 sandwich formula in numpy: (X'X)^-1 X' diag(e^2/(1-h)^2) X (X'X)^-1")

# --- Step 8, the fragility screen: First Republic's score and post-event return, by hand ------------
screen = pd.read_csv(OUTPUTS / "fragility_screen.csv").set_index("ticker")
with open(OUTPUTS / "final_dataset.csv", newline="") as f:
    rows = [(float(r["uninsured_dep_share"]), float(r["sec_loss_to_equity"]), r["ticker"])
            for r in csv.DictReader(f) if r["uninsured_dep_share"] and r["sec_loss_to_equity"]]
frc_vals = [(u, s) for u, s, t in rows if t == "FRC"][0]
pcts = []
for j, x in enumerate(frc_vals):
    below = sum(1 for r in rows if r[j] < x)
    ties = sum(1 for r in rows if r[j] == x)
    pcts.append((below + (ties + 1) / 2) / len(rows))     # average rank of the tie group, as a share of N
check("First Republic screen score, from percentile ranks counted by hand", screen.at["FRC", "score"],
      sum(pcts) / 2, 1e-6, "plain counts over outputs/final_dataset.csv (entities with both predictors)")

growth = 1.0
with open(CRSP_DAILY, newline="") as f:
    for r in csv.DictReader(f):
        if r["ticker"] == "FRC" and "2023-03-13" < r["date"] <= "2023-12-29":
            ret = float(r["ret"]) if r["ret"] else 0.0
            dl = float(r["dlret"]) if r["dlstdt"] == r["date"] and r["dlret"] else 0.0
            growth *= (1 + ret) * (1 + dl)
check("First Republic return, Mar 13 close to Dec 29 close (with delisting return)", screen.at["FRC", "post_bhr"],
      growth - 1, 1e-6, "raw CRSP rows for FRC, including its delisting return")

# --- Step 9, today's screen: JPMorgan's uninsured share on the latest call reports, by hand -----------
today = pd.read_csv(OUTPUTS / f"fragility_screen_{TODAY_CALL_REPORT_DATE}.csv").set_index("ticker")
unins = dom = 0.0
with open(RAW / f"fdic_financials_{TODAY_CALL_REPORT_DATE}.csv", newline="") as f:
    for r in csv.DictReader(f):
        if r["RSSDHCR"] and int(float(r["RSSDHCR"])) == 1039502:    # JPMorgan Chase & Co.
            unins += float(r["DEPUNINS"])
            dom += float(r["DEPDOM"])
check(f"JPMorgan uninsured share on {TODAY_CALL_REPORT_DATE} (today's screen), summed by hand",
      today.at["JPM", "uninsured_dep_share"], unins / dom, 1e-6,   # the CSV keeps 6 significant digits
      f"raw FDIC rows for {TODAY_CALL_REPORT_DATE} with RSSDHCR = 1039502")

# --- Step 10, placebo windows: one window's coefficient rebuilt from raw CRSP rows, and the window count ----
placebo = pd.read_csv(OUTPUTS / "placebo_windows.csv").set_index("day0")
with open(CRSP_MARKET, newline="") as f:
    days_2022 = sorted(r["date"] for r in csv.DictReader(f) if r["date"].startswith("2022"))
check("Placebo windows: 2022 trading days minus 2 (each window needs days 0 to +2 in 2022)", len(placebo),
      len(days_2022) - 2, 0, "crsp_market_vwretd.csv dates, counted by hand")

pw = ["2022-06-13", "2022-06-14", "2022-06-15"]        # the week of the 75 bp Fed hike, chosen by hand
mkt = 1.0
with open(CRSP_MARKET, newline="") as f:
    for r in csv.DictReader(f):
        if r["date"] in pw:
            mkt *= 1 + float(r["vwretd"])
growth, ndays = {}, {}
with open(CRSP_DAILY, newline="") as f:
    for r in csv.DictReader(f):
        if r["date"] in pw and r["ret"] not in ("", "B", "C"):
            p = int(r["permno"])
            growth[p] = growth.get(p, 1.0) * (1 + float(r["ret"]))
            ndays[p] = ndays.get(p, 0) + 1
ms = pd.read_csv(OUTPUTS / "final_dataset.csv")
ms = ms[ms["main_sample"]]
X, y = [], []
for r in ms.itertuples():
    p = int(r.permno)
    if ndays.get(p) == 3:
        X.append([1.0, r.uninsured_dep_share, r.htm_loss_to_equity, r.log_assets])
        y.append((growth[p] - 1) - (mkt - 1))
X, y = np.array(X), np.array(y)
beta_hand = np.linalg.solve(X.T @ X, X.T @ y)[1]       # OLS by the normal equations
check(f"Placebo window {pw[0]}: uninsured-share coefficient by the normal equations ({len(y)} banks)",
      placebo.at[pw[0], "coef"], beta_hand, 1e-6, "raw CRSP rows for Jun 13-15, 2022 and outputs/final_dataset.csv")

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
