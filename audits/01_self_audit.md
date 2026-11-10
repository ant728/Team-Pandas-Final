# Self-audit 01: Checkpoint 2

Review date: November 10, 2026. Scope: the working 20-bank v0, proposal, dashboard and public-data boundary. This is an agent-assisted skeptical review, not an independent professor audit. The course Quick Reference prompt itself was not supplied; the review applies the supplied project audit checklist.

## Findings and responses

| Finding | Response | State |
|---|---|---|
| Existing summed CAR was described like an actual compounded crash loss | Headline is compounded stock return minus compounded CRSP VWRETD. Retain CAR as a labeled alternative. | Fixed |
| yfinance lost failed and later-merged banks | Use supplied CRSP delivery; retain all 20 entity rows. Comerica and PacWest have observed event outcomes. | Fixed for available CRSP data |
| SVB and Signature have missing delisting returns and incomplete event calendars | Preserve missing baseline outcomes; separately export terminal zero-value scenarios. No zero-return filling or silently shortened windows. | Disclosed, unresolved recovery values |
| EQCCOMPI was mislabeled as an accumulated AOCI balance in the handoff | Verify dictionary: OTHER COMPREHENSIVE INCOME. Zions raw field matches annual flow, not closing balance. Explain Schedule RC 26.b and use 10-K components. | Fixed interpretation |
| HTM-only gap misses earlier transferred losses | Recommend transfer-aware definition; produce sourced approximate Zions diagnostic. Do not apply a special correction in full-sample comparisons. | Exact remaining balance and cross-bank collection outstanding |
| Total AOCI gross-up would mix securities, hedges, pensions and taxes | Reject total-AOCI shortcut; do not use annual OCI tax benefits to gross up a stock balance. | Fixed design |
| Raw licensed daily returns could leak via processed files, dashboard or preview | Read raw input only from ignored directory; export event-level derived outcomes. Daily CRSP file writes stay under data/raw. Preview uses public-file allowlist. | Fixed; verify archive/staged paths before sharing |
| Original hand checks used SPY while the new analysis uses CRSP VWRETD | Replace benchmark-dependent checks with independent CRSP scalar arithmetic. Earlier interim run failed these old checks; corrected checks pass. | Fixed |
| Missing subsidiary uninsured values could produce an understated aggregate share | Mark aggregate uninsured share missing if any contributing subsidiary value is missing. Require positive equity; report coverage. | Fixed |
| Four-bank initial regression would have one residual degree of freedom | Expanded to 20 banks, 18 complete outcomes. Report descriptive coefficients only, without inference or predictive claims. | Small selected sample remains |
| Selected sample is not representative and complete-case OLS omits two failed outcomes | Label clearly; no inference claims. Full universe also contains nonbank financial groups requiring eligibility review. | Disclosed |
| API historical data can contain later amendments | Log vintage. Original FFIEC bulk-file comparison not completed; do not claim match. | Outstanding, permitted API use disclosed |
| Historical bank subsidiaries are not consolidated holding companies | Preserve entity type/ownership/crosswalk; disclose scope difference. | Disclosed; further manual matching review needed |
| Historical screen could be mistaken for a live validated model | Explicit December 2022 labels; no latest-quarter or accuracy claims. Record retrospective test design without claiming pristine preregistration. | Fixed labeling; test not run |
| Dense chart labels overlapped | Label a few reference banks; retain tooltips and full data table. | Fixed in browser QA |

## Verification performed

- Downloaded the NY Fed link and FDIC report-date financials. CRSP was read from the user-supplied licensed delivery.
- Pipeline produces 20 entity rows from 30 subsidiary reports; 18 observed event outcomes, with SIVB/SBNY explicitly missing.
- Eight independent checks in `outputs/hand_checks.md`: published SVB magnitudes, JPM aggregation, WAL compounding/benchmark arithmetic, two disclosed failure-scenario calculations, and Comerica coverage.
- Zions source-date, AOCI-component and rounded cost/fair-value assertions pass; unique keys, merge cardinality, CRSP share-class and report coverage checks execute in code.
- Browser checked overview, event chart/return selector and historical search/sort. Searched ZION and verified one matching row. Proposal mockup is a screenshot of the running dashboard.
- Preview serves only copied public files, never the repository root. Raw CRSP and local environment are excluded from the deliverable archive and Git staging.

## Limits and submission status

This is a reviewable Checkpoint 2 v0, not completed full-sample research. Exact transfer-loss balances, original FFIEC comparisons, historical screen performance and a live-quarter screen remain outside the verified results. Team review is still necessary, including source transcription, crosswalk matches, understanding the code, and checking the class HW8 submission instructions (not supplied here).
