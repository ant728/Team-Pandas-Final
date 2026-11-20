# Response to the instructor audit (Checkpoint 2)

Team Pandas · November 17, 2026 · responds to [`02_instructor_audit.md`](02_instructor_audit.md) (audited commit `88005d3`), tracked in [issue #15](https://github.com/ant728/Team-Pandas-Final/issues/15).

| ID | Finding | Response | Where |
|---|---|---|---|
| A1 | Pinned requirements don't install a working environment | **Fixed** | [PR #16](https://github.com/ant728/Team-Pandas-Final/pull/16), commit `23c0814` |
| A2 | Main result depends on SVB and Signature's imputed −100% returns | **Fixed:** main sample chosen and logged; all three rows reported in the README and on the dashboard | [PR #17](https://github.com/ant728/Team-Pandas-Final/pull/17); `specs_tried.md` #16–#17 |
| A3 | Standard errors ignore the common shock | **Fixed as suggested** (KRE-beta control, R5); the remaining limitation is disclosed | [PR #18](https://github.com/ant728/Team-Pandas-Final/pull/18), commit `80d3983`; README threat 10 |
| A4 | Ten real banks dropped by the link step | **Fixed:** match rate 327 → 337 of 343 | [PR #18](https://github.com/ant728/Team-Pandas-Final/pull/18), commit `80d3983`; README "Linking banks" |
| — | Magnitudes discussed (⚠️ in the summary table) | **Fixed:** one-SD effects reported | `outputs/regressions_v0.md`, README "Current outputs" |

Every change to the sample or the estimates was written into `specs_tried.md` and committed **before** it was run: #13–#15 in commits `e91320a` and `83c748b`, and #17 in commit `7d44cc3`.

## A1 · Fixed

`requirements.txt` now pins `scipy==1.13.1` and `patsy==0.5.6`, the versions that built the outputs; `statsmodels==0.14.2` fails to import with SciPy 1.15 or later. We tested in a fresh Python 3.12 virtual environment created only from `requirements.txt`. `python code/05_regressions.py` and `python run_all.py` both run, and the regression tables, summary statistics and hand checks came out byte-identical to the audited commit.

## A2 · Fixed

**Decision (`specs_tried.md` #17):** the main sample leaves out SVB and keeps Signature with its −100% delisting return.
- **SVB is the event, not a response to it.** Its Mar 8 announcement and Mar 10 failure *are* the shock. Our question is how that shock spread to *other* banks, so SVB's own return doesn't belong on the left-hand side.
- **Signature is an outcome of the run.** It's a separate bank that lost deposits after SVB and was closed on Mar 12, the kind of outcome we want to explain.
- **−100% is the economically right value for Signature.** Shareholders of a bank in FDIC receivership are wiped out. CRSP has no delisting return because trading stopped, not because the value is unknown.

**Disclosure:** we made this decision after reading the audit's leave-out table, which showed the coefficient weakening without SVB. `specs_tried.md` says so. The reasons are economic, and we report all three rows whatever they show.

| Sample | Spec | N | Uninsured-share coef (HC3 SE) | p |
|---|---|---|---|---|
| **Main: without SVB** | R1 | 332 | **−0.112 (0.056)** | **0.047** |
| Including SVB (earlier baseline) | R6 | 333 | −0.149 (0.066) | 0.023 |
| Without SVB and Signature | R3 | 331 | −0.065 (0.030) | 0.032 |

R2, R4 and R5 also run on the main sample now. The uninsured-share coefficient is negative and significant at 5% in all six specifications, but the main estimate is about three-quarters of the old baseline and only just clears 5%. These numbers use the 333-bank sample from the A4 fix, so they differ slightly from the audit's table (323 banks).

**Dashboard (Mason Friedman):** the March 2023 Results page has a "Dependence on failed-bank outcomes" table showing these three rows. It reads N, the coefficient and the SE from `outputs/regressions_v0.csv`, so nothing is hard-coded. Mason's verification of the dashboard change:

| Check | Evidence |
|---|---|
| Dashboard data and behavior | All three displayed N, coefficient and SE values match the generated CSV. The table fits a narrow browser without horizontal scrolling. Removing the regression CSV shows an explicit error while the chart stays usable; restoring it restores the table. Intro, Method, the historical table and search still work, with no console errors. The parser rejects missing, duplicate or incompatible rows and invalid numbers. |
| Published-file boundary | The local server returns the regression CSV unchanged and rejects raw CRSP paths, interim paths, directory listings and Git metadata with HTTP 404. No licensed row-level data is served. |

[Dashboard preview from Mason's check](../docs/images/a2_regression_comparison.jpg).

## A3 · Fixed as suggested; limitation disclosed

Following the audit's first suggestion, step 2 downloads KRE (SPDR S&P Regional Banking ETF) and step 3 estimates each bank's beta to KRE over trading days −250 to −30 (at least 150 days, the same window as the market model). R5 adds `kre_beta` to R1 (`specs_tried.md` #14). On the main sample, the uninsured-share coefficient is −0.109 (p = 0.038), against −0.112 in R1, so **it survives**. `kre_beta` itself is −0.141 (p < 0.001): banks that moved more with regional banks before the event fell more during it.

A new hand check recomputes WAL's KRE beta as cov/var from the raw files. **Remaining limitation (README threat 10):** R5 controls for each bank's exposure to the common factor, but its standard errors still treat residuals as independent, so the problem is reduced, not removed. KRE comes from yfinance because our CRSP pull doesn't include it.

## A4 · Fixed

Step 4 now assigns each insured bank to the highest listed company that controls it on 2022-12-31, walking up the FFIEC NIC relationships file, instead of using only the top-tier holder (`RSSDHCR`) (`specs_tried.md` #13).
- **Match rate: 327 → 337 of 343.** All 10 banks now have `has_fdic = True` (Hilltop, Amalgamated, First Guaranty, Greene County, Lake Shore, TFS, Kentucky First, Broadway, South Plains, Sterling). The 6 still unmatched are non-banks that own a thrift.
- Step 4 prints both match rates on every run, and the README reports them.
- **Found while building it (#15):** nine insured banks are owned by another insured bank, and the parent bank's consolidated call report already includes them. Summing both double-counted. Four sample entities were affected (small subsidiaries of State Street, Citi, Greene County and Pioneer), and these banks are now left out of the sums.
- **New hand check:** TFS Financial's assets, rebuilt from the raw NIC and FDIC rows with plain loops.
- The NIC file is a manual download (the FFIEC site blocks scripts with a CAPTCHA). "How to run" and the provenance table say how to get it.

## Checks after all fixes

`python run_all.py` runs end to end. **14 hand checks pass**; the FFIEC comparison is SKIPPED when its manually downloaded file is absent, and its last result is in `outputs/ffiec_fdic_comparison.md`. The dashboard loads with the new data, plotting 333 of 343 entities.
