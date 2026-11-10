# Checkpoint 2 self-audit — dashboard contribution

**Scope:** Mason Friedman's dashboard after integrating the full CRSP
pipeline from [PR #7](https://github.com/ant728/Team-Pandas-Final/pull/7).
This is a dashboard audit for Checkpoint 2 ([issue #4](https://github.com/ant728/Team-Pandas-Final/issues/4)).

| Check | Finding and response |
|---|---|
| Rebuild | Ran `python run_all.py` in an isolated checkout using the four supplied CRSP inputs. All seven stages completed and all nine hand checks passed. The regenerated final dataset matched the committed output to numeric precision. |
| Data source | The app reads only `outputs/final_dataset.csv`. There are 343 unique RSSD IDs and 323 in-sample rows, all with both plotted values. The other 20 stay in the table: 16 have no FDIC match and four have no event returns. |
| Return measure | The scatter uses `bhar_0_2`: compounded bank return minus compounded CRSP value-weighted market return over March 9, 10, and 13. Market-model CAR remains a separate output. |
| Delisting sensitivity | SVB and Signature each show a buy-and-hold return of −100% and a BHAR of −96.16%. Their points and tooltips identify the assumed delisting returns using `dlret_imputed`. These are estimates under the pipeline's assumption in `specs_tried.md` #5, not observed CRSP delisting returns. |
| Browser review | Opened Intro, Method, March 2023 Results, and Who's Next. Verified all 323 plot points, both imputed labels, bank inspection, ticker/name fallback, search, numeric sorting with missing values last, and the included/excluded filters. The axes cover the full plotted range. The color scale saturates at the 95th percentile; raw ratios still appear in the inspector and table. |
| Licensed inputs | The local server serves only the dashboard assets and the published final dataset. The four raw inputs and row-level interim files were used in the isolated rebuild and were not served, staged, or committed. |

**Limits:** Who's Next uses December 2022 balance sheets. It does not rank
current banks or report a validated failure prediction. The event scatter
shows associations; it does not establish causality. The loss measure,
data-vintage concerns, and sensitivity to assumed delisting returns remain
documented under “Threats to validity” in the main README.


## Morgan Waddell — accounting and proposal additions

Review date: November 10, 2026. These checks supplement Mason's audit above; they are not a replacement for the full team Skeptical review scheduled Friday.

| Check | Finding and response |
|---|---|
| One official pipeline | Removed the parallel pipeline, alternate datasets, preview server and duplicate lockfile. `python run_all.py` runs the official Steps 00–07. Mason's dashboard assets are preserved exactly and read only `outputs/final_dataset.csv`. |
| OCI versus AOCI | Renamed `aoci_to_equity` to `oci_2022_to_equity` in official Step 04 and updated the README/config comments. The calculation is unchanged and is not used in regressions. EQCCOMPI is an annual OCI flow, not accumulated AOCI. |
| Zions reconciliation | Step 07 reads the sourced disclosure CSV and official raw FDIC report. Five independently transcribed rounded values match within the stated tolerance; AOCI component arithmetic also passes. Output tables document the units, source locations and approximate transfer-loss assumption. |
| Official rebuild | Ran `python run_all.py` from the repo root with all four licensed CRSP files in `data/raw/crsp/`. All eight stages and all nine existing hand checks passed, as did the new reconciliation assertions. |
| Dataset preservation | Compared the full rebuilt dataset with its pre-change version after renaming the OCI header. Keys, flags, missingness and values match within absolute tolerance 1e-12; the largest observed float difference was below 7e-16. Retained the canonical numeric serialization after verification so the committed final-dataset diff changes only that header. The regression tables, summary statistics and original hand-check report are unchanged. |
| Proposal traceability | Real rows come from the official final dataset; regression entries match the published regression table and CSV; the mean comes from summary statistics; the passing-check count comes from the official hand-check report. The mockups are screenshots of Mason's running dashboard. No separate development results appear in the proposal. |
| Specification record | Retained existing #1–#10; added Zions entries #11–#12 and the dated retrospective historical-screen plan. Removed entries applying only to the abandoned pipeline. No new regression specifications or failed-bank policies were introduced. |
| Licensed inputs | Raw CRSP and row-level interim paths remain ignored. Only derived outputs are staged. Mason's route allowlist serves public dashboard assets and the official final CSV, never raw data. |

### Unresolved research limits

Exact remaining transferred-loss balances, cross-bank transfer collection and the original FFIEC bulk-file comparison remain outstanding. The approximate Zions ratio is not used as a special adjustment in the official regressions. The historical screen has not been validated and is not a live-quarter screen. Friday's team review should also reassess the README's existing validity threats and the sensitivity to imputed failed-bank outcomes.
