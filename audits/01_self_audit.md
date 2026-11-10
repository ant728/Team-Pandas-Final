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
