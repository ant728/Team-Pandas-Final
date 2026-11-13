# Specifications tried

Every specification we run goes here, including the ones we drop. Count so far: **4 return/measure variants** on the 6-bank proof of concept (Oct 29), plus **2 measurement choices and 4 regressions** on the full sample (Nov 10). Each regression was run once, as listed; none was re-run with different controls or samples beyond what's here.

## Proof of concept (6 banks, yfinance returns)

| # | Date | What | Sample | Outcome | Kept? |
|---|---|---|---|---|---|
| 1 | 2026-10-29 | CAR[0,+2], market model on SPY, estimation window [−250, −30], day 0 = Mar 9, 2023 | JPM, WAL, ZION, FRC | WAL −76%, FRC −89%, ZION −36%, JPM −2% | Became the secondary outcome (`car_0_2`, now on the CRSP market) |
| 2 | 2026-10-29 | Same window, market-adjusted (stock − SPY, no beta) | same | Within 1.3 pp of #1 for all four | Dropped |
| 3 | 2026-10-29 | Buy-and-hold return, Mar 8 close → Mar 13 close (raw, not abnormal) | same | WAL −64%, FRC −73%, ZION −36%, JPM −5% | **Yes: became the main outcome (BHAR).** Summing daily returns overstates crashes this large (WAL: −76% summed vs −64% compounded) |
| 4 | 2026-10-29 | Two loss measures: HTM loss / equity vs. (HTM + AFS loss) / equity | all 6 | They rank banks very differently: Comerica is 0 on the first, 0.62 on the second; Zions is negative on the first | Both kept (R1 vs. R2 below); Zions question open |

## Full sample (CRSP returns, 323 banks)

| # | Date | What | Sample | Outcome | Kept? |
|---|---|---|---|---|---|
| 5 | 2026-11-10 | **Delisting choice:** SVB and Signature have no CRSP delisting return; set it to −100% | 323 | Their BHAR becomes −96% (vs. −82% and −28% if the missing delisting return is ignored) | **Main.** Alternative is dropping them (R3) |
| 6 | 2026-11-10 | **Uninsured deposits for banks without the FDIC estimate:** amount in accounts > $250K − $250K × count | ~50 of 4,773 banks | Correlation with the FDIC estimate where both exist: 0.95 | Used only as a fallback |
| 7 | 2026-11-10 | R1: BHAR[0,+2] on uninsured share + HTM loss/equity + log assets, HC3 SEs | 323 | Uninsured −0.151 (p = 0.03); HTM loss −0.077 (p = 0.50); log assets −0.015 (p = 0.002); R² 0.18 | Baseline |
| 8 | 2026-11-10 | R2: R1 with (HTM + AFS loss)/equity instead | 323 | Uninsured −0.164 (p = 0.03); securities loss +0.005 (p = 0.83) | Robustness |
| 9 | 2026-11-10 | R3: R1 without SVB and Signature | 321 | Uninsured −0.062 (p = 0.05); HTM loss −0.021 (p = 0.74) | Robustness: **the uninsured effect leans heavily on the two failed banks** |
| 10 | 2026-11-10 | R4: R1 with market-model CAR as the outcome | 322 | Uninsured −0.201 (p = 0.03); HTM loss −0.128 (p = 0.47) | Robustness |

**Magnitude (R1):** a one-standard-deviation higher uninsured share (16 pp) goes with a 2.4 pp lower BHAR over the three days. The average bank's BHAR was −10.3%.

## Choices fixed before looking at returns
One exception: the outcome definition itself (compounded BHAR rather than summed CAR) was chosen *after* seeing four banks' event returns in the proof of concept (#1–#3). The reason was mechanical (summing overstates large crashes), but it was not fixed blind.

- Call report quarter: Q4 2022 (due Jan 30, 2023, public before the event).
- Day 0: Mar 9, 2023 (SVB's announcement came after the close on Mar 8). Window: trading days 0 to +2.
- Uninsured share denominator: domestic deposits (the uninsured estimate only covers domestic offices).
- Sample: every entity in the NY Fed CRSP–FRB link on Dec 31, 2022, matched to FDIC data, with event returns and positive equity.
- Market: CRSP value-weighted index (`vwretd`).

## Not yet run (planned, and to be written down before running)
- Any winsorizing of the loss ratios.
- The AOCI-based loss measure for the Zions question (Morgan).

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
