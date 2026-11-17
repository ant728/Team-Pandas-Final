# Instructor audit: Team Pandas, Checkpoint 2

**Repo:** ant728/Team-Pandas-Final · **Audited commit:** `88005d3` (2026-11-14, `main`) · **Seed:** 6, bank fragility: SVB, and who's next

> Note from your human teacher: This review is generated with minimal supervision from Opus 5.5-high. It is thorough, but can be too generous at times and doesn't know my taste for what is "good". Grades it and I would assign are correlated, but noisy, ok? If you want additional feedback from _me_, you need to find me before/after/during class or during office hours for a guaranteed speedy reply. I will try to respond to emails and issues, but can not respond to student inquiries around the clock across the final weeks of class. Response times will be unpredictable, though during Thanksgiving week, I will do my best to respond quickly virtually, as in person options will be nil.

## Summary

This is strong v0 work on the full sample (323 banks):
- a point-in-time universe from the NY Fed link, including failed banks;
- CRSP returns with delisting handling;
- an FDIC–FFIEC cross-check;
- hand checks for every step;
- an honest list of 11 threats.

Several numbers check out independently:
- my own HC3 regression reproduces R1 exactly;
- your call-report measures match the raw FFIEC file;
- your 3-day returns match a second price source.

Two things to fix:
1. On a fresh install, the regression step crashes, because SciPy isn't pinned (A1).
2. Your headline coefficient depends heavily on two failed banks with imputed −100% returns, and that choice needs to be made explicitly and logged (A2).

| Check | Result |
|---|---|
| Reruns from scratch | ❌ step 05 fails on a clean install (A1). With SciPy < 1.15 it reproduces exactly. Steps 01/04/07 couldn't download from the FDIC API here (blocked host, not your bug); step 03 needs the licensed CRSP files |
| Inputs have provenance | ✅ `data/provenance_log.csv`, a CRSP request file and the Stata pull script |
| Keys unique, merges validated | ✅ `rssd_id` and `permco` asserted |
| No look-ahead / survivorship | ✅ Q4 2022 reports, the Dec 31 2022 link universe, failed banks kept |
| LLM leakage handled | n/a |
| `specs_tried.md` complete | ✅ |
| Magnitudes discussed | ⚠️ coefficients only so far |
| Hand checks | ✅ `outputs/hand_checks.md` |
| Threats to validity | ✅ 11 items, including the ones below |
| Every number traces to `outputs/` | ✅ README numbers match `regressions_v0.md` |

## What holds up

- **Regression recomputed.** My own OLS with HC3 on `outputs/final_dataset.csv` (`in_sample`, N = 323) gives R1: uninsured share −0.1506 (SE 0.0692), HTM loss/equity −0.0766 (0.1124), log assets −0.0149 (0.0049). Identical to `outputs/regressions_v0.md`.
- **Measures checked against the raw call reports.** For the 11 listed entities whose own RSSD files a call report, I computed RCON5597/RCON2200 and (RCFD/RCON 1754 − 1771)/G105 from the FFIEC CDR 12/31/2022 bulk file. They match `uninsured_dep_share` (10 comparable) and `htm_loss_to_equity` (11) to 1e-16. This confirms the FDIC API fields map as you say (EQTOT = G105).
- **Returns from a second source.** yfinance closes from Mar 8 to Mar 13, 2023 reproduce `bhr_0_2` for 17 large listed banks. 16 match to 0.0000, and RF differs by 0.0004 (likely a dividend adjustment).
- **Licensing:** only CRSP-derived results are committed, never CRSP rows, as your README promises.
- **Seed 6, call-report date:** the quarter before the event.
- **Seed 6, small illiquid banks:** flagged (2,247 bid/ask rows), with filters to be logged.

## Findings

### A1 · Blocking · The pinned requirements don't install a working environment

**Evidence:**
- `requirements.txt` pins `statsmodels==0.14.2` but not SciPy. A fresh `pip install -r requirements.txt` (Python 3.12) resolves `scipy==1.17.1`.
- `code/05_regressions.py` then fails on import: `ImportError: cannot import name '_lazywhere' from 'scipy._lib._util'`. `run_all.py` uses `check=True`, so it stops there.
- With `scipy==1.14.1` added, step 05 reproduces `regressions_v0.csv`, `regressions_v0.md` and `summary_stats.csv` byte for byte.
- The README says versions "are pinned to the ones that built the committed outputs".

**Why it matters:** The documented path doesn't reproduce your results on a new machine. It's a one-line fix.

**Fix:** Pin the full environment: `pip freeze > requirements.txt` from the environment that built the outputs, or at least add `scipy==<the version you used>`.

**How to show it's fixed:** The auditor will create a clean environment from `requirements.txt` and run `python code/05_regressions.py`.

### A2 · Major · The main result depends on SVB and Signature's imputed −100% returns

**Evidence:** `outputs/final_dataset.csv` has SIVB and SBNY at `bhr_0_2` = −1.0 with `dlret_imputed` = True (BHAR −0.962), and the two highest uninsured shares (0.939, 0.897). Auditor re-estimates of R1 (HC3):

| Sample | Uninsured share coef (SE) |
|---|---|
| All 323 (your R1) | −0.151 (0.069) |
| Without SIVB (322) | −0.111 (0.059) |
| Without SIVB and SBNY (321, your R3) | −0.062 (0.032) |

You disclose this (threat 1, R3).

**Why it matters:** SVB's failure is the event itself, not a response to it. Signature's failure is arguably an outcome of the run, but its −100% rests on an assumption (no trade after Mar 10, no CRSP delisting return). With both in, two points set much of the slope.

**Fix:** Decide the treatment from the economics, not the result, and log the decision in `specs_tried.md` before the final run. One defensible choice:
- exclude SVB as the trigger;
- keep Signature with the −100% assumption as the main specification;
- report all three rows of the table above in the paper and dashboard.

**How to show it's fixed:** A dated `specs_tried.md` entry naming the main sample, and the dashboard showing the robustness rows.

### A3 · Minor · Standard errors ignore the common shock: try a simple fix

**Evidence:** All banks share Mar 9–13, 2023 (threat 10). `05_regressions.py:34` uses `cov_type="HC3"`, which assumes independent errors across banks.

**Why it matters:** A regional-bank factor moves every residual together, so p-values are too small. You note this yourself.

**Fix:** Add each bank's pre-event beta to a regional-bank index (e.g. KRE, estimated over trading days −250 to −30) as a regressor, or compute abnormal returns against KRE as a robustness outcome. Report whether the uninsured coefficient survives. Log it in `specs_tried.md`.

**How to show it's fixed:** A new specification row in `regressions_v0.md`.

### A4 · Minor · Ten real banks are dropped by the link step

**Evidence:** The README's "Linking banks" section: 10 listed banks (Hilltop, Amalgamated, First Guaranty, TFS, …) are unmatched, because their banks' top-tier holder (`RSSDHCR`) is an unlisted parent above the listed company (threat 6).

**Why it matters:** This is the seed's "ID link quality" item. The drops aren't random: mutual-holding-company structures are concentrated among small thrifts.

**Fix:** Walk the NIC relationship file (parent → child, with ownership dates) to assign each bank to the listed entity that controls it on 2022-12-31, instead of using only the top-tier holder. Report the match rate before and after.

**How to show it's fixed:** `has_fdic` is True for those 10, and the match rate is in the README.

## How to respond

This audit is `audits/02_instructor_audit.md` in your repo. Fix what you can, then add `audits/03_audit_response.md`, replying to each finding ID: fixed (the commit), disputed (why), or disclosed as a limitation (where).

**Deadline: Saturday, November 21, 2026.**
