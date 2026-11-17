# A2 response: failed-bank sensitivity in the dashboard

**Owner:** Mason Friedman · **Date:** November 17, 2026

**Status:** Partially addressed; the economic main-sample decision remains open.

This responds to A2 in the [instructor audit, PR #14](https://github.com/ant728/Team-Pandas-Final/pull/14), tracked in [issue #15](https://github.com/ant728/Team-Pandas-Final/issues/15). The instructor audit file is not yet on `main`; PR #14 is the review reference. This response covers the dashboard disclosure and regression comparison only. It does not mark A2 fully fixed or close issue #15, and it makes no completion claim for A1, A3, or A4.

## What this PR changes

- `code/05_regressions.py` adds **R5 R1 without SVB (event trigger)**, using R1's formula (`bhar_0_2 ~ uninsured_dep_share + htm_loss_to_equity + log_assets`) and HC3 standard errors. R1 and the existing R3 specification remain unchanged. `specs_tried.md` records the additional sensitivity.
- Generated `outputs/regressions_v0.csv` and `outputs/regressions_v0.md` report the additional fit alongside the existing specifications.
- The Results comparison in `app/index.html`, populated by `app/dashboard.mjs` and the regression parser in `app/data.mjs`, reads coefficients, standard errors, and N from `outputs/regressions_v0.csv`. It compares R1 (all banks), R5 (exclude SVB), and R3 (exclude SVB and Signature). Verified sample sizes are 323, 322, and 321 respectively. Audit coefficients are not hard-coded into the interface.

SVB triggered the event, so excluding it asks how the association looks among the other banks. Excluding both SVB and Signature also removes the two banks whose missing delisting returns are imputed as total losses. These comparisons expose sample sensitivity; they do not resolve the economic choice of the main sample or validate the imputation assumption. HC3 also does not resolve correlated errors across banks during the shared event window.

## Verification record

| Check | Evidence |
|---|---|
| Regenerate regression outputs | Ran Step 05 in an isolated copy using the existing working Anaconda environment. The R1 / R5 / R3 sample sizes are 323 / 322 / 321. Independent NumPy least-squares and HC3 covariance calculations reproduce R5's coefficients and standard errors. This does not verify a fresh pinned-environment install; A1 remains separate. |
| Preserve the existing results | The regenerated R1–R4 CSV rows match the prior committed rows exactly at published precision. The old regression Markdown is an unchanged prefix of the regenerated report. The bank dataset and its sample flags are byte-for-byte unchanged. |
| Dashboard data and behavior | Verified all three displayed N, coefficient, and SE values against the generated CSV. The table fits the narrow browser width without horizontal scrolling. Removing the regression CSV showed an explicit error while all 323 chart points remained usable; restoring it restored the table. Intro, Method, the historical table, and search still work. No console errors or warnings were reported after restoration. Parser checks reject missing, duplicate, or incompatible comparison rows and invalid numbers. |
| Published-file boundary | The preview server returns the regression CSV unchanged and rejects raw CRSP paths, interim paths, directory listings, and Git metadata with HTTP 404. No raw or row-level licensed data was needed for this change. |

[Verified dashboard preview](../docs/images/a2_regression_comparison.jpg).

## Remaining team decision

The team must choose and justify whether the main contagion analysis includes the event-trigger bank, and how the two imputed failed-bank returns enter the main analysis. R1 remains the current baseline in this PR. The three displayed fits preserve the comparison while that decision is open; showing them is not an economic resolution of A2.
