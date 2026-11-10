# Specifications tried

Every specification we run goes here, including the ones we drop. The first four entries are the original six-bank proof of concept. Checkpoint 2 entries below record the expanded 20-bank v0. No hypothesis-test p-values are reported.

| # | Date | What | Sample | Outcome | Kept? |
|---|---|---|---|---|---|
| 1 | 2026-10-29 | CAR[0,+2], market model on SPY, estimation window [−250, −30], day 0 = Mar 9, 2023 | JPM, WAL, ZION, FRC | WAL −76%, FRC −89%, ZION −36%, JPM −2% | Baseline for now |
| 2 | 2026-10-29 | Same window, market-adjusted (stock − SPY, no beta) | same | Within 1.3 pp of #1 for all four | Robustness column |
| 3 | 2026-10-29 | Buy-and-hold return, Mar 8 close → Mar 13 close (raw, not abnormal) | same | WAL −64%, FRC −73%, ZION −36%, JPM −5% | **Likely switch to BHAR.** Summing daily returns overstates crashes this large (WAL: −76% summed vs −64% compounded) |
| 4 | 2026-10-29 | Two loss measures: HTM loss / equity vs. (HTM + AFS loss) / equity | all 6 | They rank banks very differently: Comerica is 0 on the first, 0.62 on the second; Zions is negative on the first | Undecided. See STATUS.md |

## Choices fixed before looking at returns
- Call report quarter: Q4 2022 (due Jan 30, 2023, public before the event).
- Day 0: Mar 9, 2023 (SVB's announcement came after the close on Mar 8).
- Uninsured share denominator: domestic deposits (the uninsured estimate only covers domestic offices).

## Checkpoint 2 additions: November 10, 2026

| # | Specification | Sample / outcome | Decision |
|---|---|---|---|
| 5 | Raw compounded stock return and stock minus SPY compounded return | Original 6 banks; 4 observed returns; WAL raw -63.50%, adjusted -60.10% | Verified interim implementation; superseded benchmark by CRSP |
| 6 | CRSP RET compounded over March 9/10/13; observed DLRET compounded on its date; subtract compounded VWRETD | Selected 20 banks; 18 complete event returns | Checkpoint 2 headline; see generated CSV for exact values |
| 7 | Missing failed-bank delisting return: keep unknown vs terminal zero-value scenario | SIVB and SBNY remain in rows; baseline outcome missing; separate scenario assumes total stock loss of 100% | Neither missing DLRET nor missing days silently become zero returns |
| 8 | CRSP market-model summed CAR and simple summed market-adjusted CAR | Same observed-return sample; estimation [-250,-30], minimum 150 observations | Retained alternatives, not selected for significance |
| 9 | Zions HTM-only, HTM+AFS, and HTM+AFS+approximately $2.4B transferred loss | Approximately -2.31%, 30.86%, 79.90% of equity using rounded 10-K disclosures | Transfer-aware definition recommended; third value is a diagnostic, not exact year-end adjustment |
| 10 | Total AOCI gross-up | Considered but not calculated: taxes, non-securities components, and OCI-flow/AOCI-stock confusion | Rejected on accounting grounds; no assumed tax-rate experiments |
| 11 | OLS of market-adjusted BHAR on uninsured share and baseline securities loss/equity, with intercept | 18 complete event outcomes in selected 20-bank sample; coefficients in outputs/regression_diagnostic.json | Descriptive plumbing check only; no p-values, causal or predictive claim |

## Historical screen test design (not yet run)

This is a retrospective design: the team already knows famous 2023 cases, so it is not an untouched prospective preregistration. Record this plan before calculating screen performance; do not tune cutoffs to make known cases pass.

- Eligible universe: 2022-12-31 NY Fed-linked listed bank entities with valid pre-event measures and positive equity; report every exclusion and missing value. The current 20-bank sample is a development sample, not the target test universe.
- Proposed screen: average percentile ranks of uninsured domestic share and a consistently available securities exposure measure. Freeze the transfer-loss collection/availability rule before scoring; do not use a special Zions-only correction in cross-bank ranks.
- Flag: top 10% of the eligible universe by score; ties broken by regulator ID, reported transparently.
- Later distress: regulatory bank failure after March 13 and by December 31, 2023, based on the FDIC list with documented entity matching. PacWest's merger is not automatically a bank failure; report merger cases separately rather than relabel them.
- Report flag rate, coverage, false positives and missed failures. Do not optimize on these outcomes. The current dashboard only sorts historical measures; it does not claim validation or use latest-quarter data.
