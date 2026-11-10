# Specifications tried

Every specification we run goes here, including the ones we drop. Count so far: **4 variants** on a 6-bank proof-of-concept sample (4 with returns). No hypothesis tests have been run yet, so nothing here is a result.

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

## Pre-specified out-of-sample fragility screen

**Written 2026-11-10, before calculating the screen ranks or checking the named banks' ranks.** Run this only after the CRSP data and the full Q4 2022 bank-measure dataset are available.

### Question and sample

Would a screen formed solely from December 31, 2022 call-report data have flagged First Republic or PacWest before their later 2023 distress? The evaluation universe is the listed-bank entities linked to CRSP by the NY Fed link on 2022-12-31 (the target is the 343 PERMCOs in `requests/crsp_permcos.csv`). Use one row per listed entity, aggregating subsidiary-bank call reports according to the dated crosswalk. Do not filter on whether the entity survived or had a usable 2023 return.

The ranking sample includes entities with non-missing values for both predictors below. Report the full universe size, the number ranked, and each exclusion with its reason. Never silently drop missing predictor data.

### Predictors and flag rule

Use the two existing Q4 2022 predictors: `uninsured_dep_share` and `sec_loss_to_equity`, where the latter is `(HTM amortized cost - HTM fair value + AFS amortized cost - AFS fair value) / total equity`. Within the eligible ranking sample, convert each predictor to a percentile rank (higher values mean greater fragility) and take their unweighted mean as the fragility score. Rank from highest to lowest. The pre-specified flag is the top 10%; include ties at the cutoff and report the resulting flagged count/share. Top 5% and top 20% may be shown as secondary sensitivity cutoffs only; do not select a cutoff based on which one flags First Republic or PacWest.

This version uses the repository's existing securities-loss measure. It does not claim to capture losses transferred from AFS to HTM; if the team adopts a revised measure after documenting the Zions issue, date and record that exact formula as a new specification before computing any out-of-sample ranks.

### Outcomes and reporting

1. **Named cases:** report whether First Republic and PacWest appear in the top-decile flag group, with each entity's predictor values, score, percentile rank, and cutoff. These two cases were specified from Professor Bowen's feedback, not selected after examining the screen.
2. **Broader failure outcome:** identify banks that entered FDIC receivership from 2023-03-14 through 2023-12-31 using the FDIC failed-bank records. Report the number of failures, the fraction in the top-decile group (recall), and the fraction of top-decile flags that failed (precision), with a case list.
3. **Secondary severe-return outcome:** for listed entities, calculate CRSP buy-and-hold return from the 2023-03-13 close through the 2023-12-29 close, incorporating delisting returns. March 13 is the last close in the original SVB event window, so this outcome measures subsequent performance. Define severe loss as a return of -50% or lower. Report missing-return cases and do not treat a missing/delisted quote as a zero return. Show this outcome separately from FDIC failures.

The March 9-13 event return is not used to build the 2022 score. These are descriptive screening results on a small number of crisis outcomes, not a causal test or proof of forecasting ability. Do not combine outcomes or change thresholds after inspecting results. Log any deviation below with its date and reason.
