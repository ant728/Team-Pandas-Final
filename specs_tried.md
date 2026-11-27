# Specifications tried

Every specification we run goes here, including the ones we drop. Each change to the sample, the measures or the regressions is written down and committed **before** it is run (the commit history shows the order). Count so far: **4 return/measure variants** on the 6-bank proof of concept (Oct 29); **10 regressions (R1–R10)** and the measurement choices #5–#6, #13, #15 and #17 on the full sample; Zions diagnostics #11–#12; the pre-specified out-of-sample screen (#21–#25); today's screen (#26–#27); and the placebo windows (#28). No other control, sample or cutoff variants have been tried.

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
| 16 | 2026-11-17 | R6 (numbered R5 and #13 when first run; renumbered because #13–#15 and R5 were taken by the A3/A4 fixes): R1 without SVB (event trigger), retaining Signature and its existing imputed delisting return; same controls and HC3 SEs | In-sample entities with ticker != SIVB (N = 322) | Uninsured −0.1113 (SE 0.0593, p = 0.060); HTM loss −0.0165 (p = 0.806); R² 0.133 | Additional A2 sensitivity; R1 remains the baseline |

**Magnitude (R1):** a one-standard-deviation higher uninsured share (16 pp) goes with a 2.4 pp lower BHAR over the three days. The average bank's BHAR was −10.3%.

**A2 sensitivity recorded November 17, 2026:** R6 (#16) was added after reading the instructor audit, including its reported leave-SVB-out estimate. It is motivated by SVB's role as the event trigger, not an independent pre-registered test. Compare R1 (all banks), R6 (without SVB), and R3 (without SVB and Signature) with the same R1 formula and HC3 standard errors. This addition does not change the main sample, the existing R1–R4 specifications, or the delisting-return assumption; the team's final economic justification of the main sample remains a separate decision.

## Choices fixed before looking at returns
One exception: the outcome definition itself (compounded BHAR rather than summed CAR) was chosen *after* seeing four banks' event returns in the proof of concept (#1–#3). The reason was mechanical (summing overstates large crashes), but it was not fixed blind.

- Call report quarter: Q4 2022 (due Jan 30, 2023, public before the event).
- Day 0: Mar 9, 2023 (SVB's announcement came after the close on Mar 8). Window: trading days 0 to +2.
- Uninsured share denominator: domestic deposits (the uninsured estimate only covers domestic offices).
- Sample: every entity in the NY Fed CRSP–FRB link on Dec 31, 2022, matched to FDIC data, with event returns and positive equity.
- Market: CRSP value-weighted index (`vwretd`).

## Not yet run (planned, and to be written down before running)
- Any winsorizing of the loss ratios.
- The transfer-aware loss measure for all banks (Morgan). The Zions-only version is #11 below; the total-AOCI version was rejected (#12).

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

## Zions measurement additions

| # | Date | What | Sample / outcome | Decision |
|---|---|---|---|---|
| 11 | 2026-11-10 | HTM gap/equity; HTM+AFS gaps/equity; add approximately $2.4B of disclosed transferred losses | Zions only; generated by official Step 07 in outputs/zions_measure_comparison.csv | Recommend the transfer-aware definition, but the displayed third value is approximate; not used as a Zions-only regression correction |
| 12 | 2026-11-10 | Use total AOCI, or an assumed-tax-rate gross-up, as securities losses | Considered, not calculated: non-securities items and tax/stock-flow mixing make it inappropriate | Rejected; EQCCOMPI is an annual OCI flow, not accumulated AOCI |

## Instructor audit responses (written 2026-11-17, before running either change)

| # | Date | What | Sample / outcome | Decision |
|---|---|---|---|---|
| 13 | 2026-11-17 | **Entity link (audit A4).** Assign each FDIC-insured bank to the *highest* listed entity that controls it on 2022-12-31, walking the FFIEC NIC relationships file upward (relationships with `CTRL_IND = 1` that are active on 2022-12-31). Until now we used only the bank's top-tier holder (`RSSDHCR`), which misses a listed company that sits below an unlisted parent. A bank that is itself the listed entity is still assigned to itself. | All entities; becomes the **main sample** for every specification | Main. Report the FDIC match rate before and after, and R1–R4 before and after, whichever way the results move |
| 14 | 2026-11-17 | **R5: common-shock control (audit A3).** R1 plus `kre_beta`: each bank's slope from regressing its daily return on the daily return of KRE (SPDR S&P Regional Banking ETF, yfinance adjusted closes) over trading days −250 to −30, at least 150 days, the same window as the market model. HC3 SEs. | Main sample (#13); banks without 150 estimation days drop out, as in R4 | Robustness. Report whether the uninsured-share coefficient keeps its sign and significance, whichever way it goes. KRE comes from yfinance because our CRSP pull doesn't include it |
| 15 | 2026-11-17 | **Bank-owned banks (found while building #13, before any regression was rerun).** Nine insured banks are controlled by another insured bank (e.g. Pioneer Commercial Bank by Pioneer Bank, Greene County Commercial Bank by Bank of Greene County). A bank's call report is consolidated, so the parent bank's figures already include the child: Bank of Greene County alone reports $2.61B of assets, about Greene County Bancorp's consolidated total. Summing both double-counts. Rule: drop a bank from the sums when its controlling parent on 2022-12-31 is itself an insured bank in the FDIC file. | Affects 4 sample entities: STT and C (small trust-bank subsidiaries, already summed under the old rule), and GCBC and PBFS (newly matched) | Main; part of #13 |

### Results of #13–#15 (run 2026-11-17, after the entries above were committed)

**Match rate (#13, #15):** 327 → **337** of 343 entities matched to FDIC data; all 10 previously dropped banks now match, and only the 6 non-banks remain unmatched. In-sample: 323 → **333**. Four bank-owned banks are left out of the sums (#15): small trust-bank subsidiaries of State Street and Citi, and the municipal-deposit banks of Greene County and Pioneer.

| Spec | Uninsured share, before (N = 323) | Uninsured share, after (N = 333) | Loss measure, after |
|---|---|---|---|
| R1 | −0.151 (SE 0.069, p = 0.030) | −0.149 (SE 0.066, p = 0.023) | HTM loss −0.076 (p = 0.49) |
| R2 | −0.164 (p = 0.025) | −0.163 (SE 0.069, p = 0.019) | securities loss +0.005 (p = 0.82) |
| R3 (without SVB, Signature) | −0.062 (p = 0.051) | −0.065 (SE 0.030, p = 0.032) | HTM loss −0.021 (p = 0.74) |
| R4 (CAR) | −0.201 (p = 0.032) | −0.198 (SE 0.089, p = 0.026) | HTM loss −0.127 (p = 0.46) |

**R5 (#14), N = 332:** uninsured share −0.142 (SE 0.059, p = 0.016); `kre_beta` −0.158 (SE 0.039, p < 0.001); R² rises from 0.17 to 0.29. Banks that moved more with regional banks before the event fell more during it, but controlling for that leaves the uninsured-share coefficient almost unchanged. This addresses the common-shock concern only partly: it controls for each bank's exposure to the regional-bank factor, but the standard errors still treat residuals as independent.

## Main sample decision (audit A2, written 2026-11-17, before rerunning)

| # | Date | What | Sample / outcome | Decision |
|---|---|---|---|---|
| 17 | 2026-11-17 | **Main sample excludes SVB; Signature stays in with its −100% delisting return.** (1) SVB is the event, not a response to it: its Mar 8 announcement and Mar 10 failure *are* the shock, and our question is how the shock spread to *other* banks, so SVB's own return doesn't belong on the left-hand side. (2) Signature is a separate bank that suffered a run after SVB and was closed on Mar 12, the kind of outcome we want to explain, so it stays. (3) −100% is the economically right value for Signature: shareholders of a bank in FDIC receivership are wiped out; CRSP has no delisting return because trading stopped, not because the value is unknown. | Main sample = `in_sample` minus SVB. R1, R2, R4 and R5 run on it. Robustness: R6 = R1 including SVB (the earlier baseline); R3 = R1 also without Signature | Main. **Disclosure:** decided after seeing the instructor audit's leave-out table (and #16), which showed the coefficient weakening without SVB. The reasons above are economic, and all three rows are reported in the README and the dashboard whatever they show |

**Results of #17 (run 2026-11-17, after the entry above was committed).** Uninsured-share coefficient, HC3:

| Spec | Sample | N | Coef (SE) | p |
|---|---|---|---|---|
| **R1 (main)** | without SVB | 332 | **−0.112 (0.056)** | **0.047** |
| R2 | without SVB, all securities loss | 332 | −0.119 (0.056) | 0.033 |
| R3 | also without Signature | 331 | −0.065 (0.030) | 0.032 |
| R4 | without SVB, market-model CAR | 331 | −0.133 (0.063) | 0.035 |
| R5 | without SVB, + KRE beta | 331 | −0.109 (0.053) | 0.038 |
| R6 | including SVB (earlier baseline) | 333 | −0.149 (0.066) | 0.023 |

Magnitude (R1): a one-SD higher uninsured share (16.0 pp) goes with a 1.8 pp lower BHAR; the average main-sample bank's BHAR was −10.0%. The loss measures stay insignificant in every spec. The main estimate is about three-quarters of the old baseline, and only just clears 5%.

## Part A robustness for v1 (written 2026-11-18, before running)

| # | Date | What | Sample / outcome | Decision |
|---|---|---|---|---|
| 18 | 2026-11-18 | **R7: window that ends before the rescue.** R1 with `bhar_0_1` as the outcome: buy-and-hold abnormal return over trading days 0 to +1 (Mar 9 and 10), computed exactly like `bhar_0_2` but stopping before the Sunday, Mar 12 deposit guarantee and BTFP (README threat 9). | Main sample (#17) | Robustness. Report whether the uninsured-share coefficient keeps its sign and significance, whichever way it goes |
| 19 | 2026-11-18 | **R8, R9: winsorized ratios.** R1 (R8) and R2 (R9) with `uninsured_dep_share`, `htm_loss_to_equity` and `sec_loss_to_equity` winsorized at their 1st and 99th percentiles, computed on the main sample. Targets the extreme loss ratios (README threat 5: First American at 29× equity). The 1/99 cutoff is the one written in the self-audit plan on Nov 12. | Main sample (#17) | Robustness. Report both, whichever way they go; no other cutoffs will be tried |

**Results of #18–#19 (run 2026-11-18, after the entries above were committed).** Main sample, HC3:

| Spec | N | Uninsured share coef (SE) | p | Loss measure |
|---|---|---|---|---|
| R1 (main, Mar 9–13) | 332 | −0.112 (0.056) | 0.047 | HTM −0.017 (p = 0.80) |
| **R7 (Mar 9–10 only)** | 332 | **−0.053 (0.057)** | **0.346** | HTM −0.009 (p = 0.82) |
| R8 (R1, winsorized) | 332 | −0.113 (0.054) | 0.037 | HTM −0.052 (p = 0.34) |
| R9 (R2, winsorized) | 332 | −0.115 (0.054) | 0.033 | securities +0.011 (p = 0.60) |

- **R7:** before the rescue, the uninsured-share coefficient is less than half of R1's and not significant. The cross-sectional sorting on uninsured deposits shows up on **Monday, Mar 13**, the first trading day *after* the deposit guarantee and BTFP. The average bank's BHAR was −3.9% over Mar 9–10 and −10.2% over Mar 9–13, so most of the decline came on Monday too. We report this as it is: the main result is a Monday effect, which fits contagion to similar banks (First Republic, PacWest and Western Alliance fell hardest that day) more than a reaction to SVB's news alone.
- **R8–R9:** winsorizing 4–8 extreme values per ratio leaves the uninsured coefficient unchanged, and the loss measures stay insignificant.
| 20 | 2026-11-18 | **R10: bank-centric sample (README threat 8).** R1 on the main sample, dropping an entity if **(a)** its bank subsidiaries' total equity (`EQTOT`, Q4 2022) is under 20% of the company's market value on Dec 30, 2022 (CRSP price × shares), meaning the bank is a small part of what the stock prices, **or (b)** the FFIEC NIC attributes file codes its primary activity (`ACT_PRIM_CD`) as something other than banking: not 5221xx (depository credit) and not 551111/551112 (offices of bank / savings-and-loan holding companies). A missing code counts as banking. | Main sample minus 8 entities: First American, Ameriprise, Schwab, Amex, Raymond James (a); Goldman Sachs, Morgan Stanley, Ally (b; Amex also fails b) | Robustness. **Disclosure:** the 20% cutoff was set after looking at the distribution of the equity-to-market-value ratio (the five lowest are 0.5%–15%, then 23% for an ordinary bank) and the NIC codes, but before running any regression on this sample. NAICS code 551112 alone could not be used: it covers every savings-and-loan holding company, including ordinary thrifts. NIC attributes are today's values, not Dec 2022's |

**Results of #20 (run 2026-11-18, after the entry above was committed).** R10 drops exactly the 8 entities named in #20. N = 324: uninsured share **−0.130 (SE 0.058, p = 0.025)**, against −0.112 (p = 0.047) in R1; HTM loss +0.015 (p = 0.84); R² 0.14. Removing the companies whose banks are a small part of the business makes the uninsured-deposit effect slightly larger, not smaller.

## Fragility screen: implementation details (written 2026-11-18, before computing any rank)

The screen follows the pre-specified rules above (written 2026-11-10). These are the points those rules leave open, decided before running `code/08_fragility_screen.py`:

| # | Date | Detail | Decision |
|---|---|---|---|
| 21 | 2026-11-18 | **Bank data.** The screen uses the current `final_dataset.csv`, so it includes the NIC link fix (#13) and the bank-owned-bank rule (#15). This is the "dated crosswalk" aggregation the rules ask for. | As stated |
| 22 | 2026-11-18 | **Percentile ranks.** `rank(pct=True)` with ties averaged, highest value = most fragile, within the ranking sample. Top-10% cutoff: the score of the ⌈0.10 × N⌉-th highest entity; every entity at or above it is flagged, so ties at the cutoff are included. Same for 5% and 20%. | As stated |
| 23 | 2026-11-18 | **SVB and Signature** stay in the ranking sample (the rules don't exclude them). They failed before the outcome window starts, so they count as "not a failure in the window" and have a missing severe-return outcome (no Mar 13 close). Their flags are reported, and the table notes how many flagged entities had already failed by Mar 12. | As stated; the main regression sample (#17) is unrelated to the screen |
| 24 | 2026-11-18 | **FDIC failure outcome.** Failures come from the FDIC BankFind `failures` endpoint (all 2023 failures, downloaded by step 1). A failed bank is matched to a listed entity with the same bank-to-entity assignment as step 4. Recall = flagged ÷ listed failures in the ranking sample; precision = failures ÷ flagged. Unlisted failed banks are counted and listed but can't be flagged. | As stated |
| 25 | 2026-11-18 | **Severe-return outcome.** Compounded CRSP return from the Mar 13, 2023 close through the Dec 29, 2023 close, including the delisting return on the delisting date; after a delisting the holder has the proceeds (0% afterwards). Missing if there is no Mar 13 close, or if a delisting has no delisting return; missing cases are reported and left out of that outcome's recall and precision. A company with several share classes uses the one with the most trading days. | As stated |

**Results of the screen (run 2026-11-18, after #21–#25 were committed).** Full report: `outputs/fragility_screen.md`.
- Ranked 337 of 343 entities; the 6 excluded are the non-banks with no FDIC data. Top 10% = 34 entities (score ≥ 0.788).
- **First Republic: rank 28, flagged** (uninsured share in the 96th percentile, securities losses in the 68th). It failed May 1, 2023, the only listed bank to fail in the window. **PacWest: rank 65, not flagged** (it's in the top 20%, a secondary cutoff only).
- FDIC failures, top 10%: recall 1 of 1; precision 1 of 34 (2.9%), against a 0.3% base rate. The other two failures in the window (Heartland Tri-State, Citizens Bank of Sac City) weren't part of any listed company.
- Return ≤ −50% from Mar 13 to Dec 29, top 10%: recall 2 of 4 (First Republic, Republic First); precision 2 of 32 (6.3%), against 1.2%. Six entities have no return (SVB and Signature delisted Mar 10; four had no CRSP data).
- SVB and Signature rank 1 and 9; both had failed before the window. First American ranks 2 because of its 29× securities-loss ratio (threat 8): the score has no bank-centric filter, as the rules were written.

## Today's screen (instructor audit B1, written 2026-11-24, before downloading any 2026 data)

The Dec 2022 screen (#21–#25) answers "would this have worked before?" The seed's second question is "which banks look like that **today**?" These rules apply the same score to the latest call reports. Because the score is a *relative* ranking (it always flags a top 10%, however safe the system is), #27 adds absolute comparisons with Dec 2022.

| # | Date | What | Decision |
|---|---|---|---|
| 26 | 2026-11-24 | **Today's screen.** As-of date: the latest call reports in the FDIC API, **Sep 30, 2026** (`TODAY_CALL_REPORT_DATE`). Universe: every entity in the NY Fed CRSP–FRB link active at the end of its latest vintage, **Sep 30, 2024** (325 entities; no newer vintage exists). An entity controlled on the as-of date by another entity in the universe is folded into that parent (one case known before running: Bank of Princeton under Princeton Bancorp, which share one stock). Banks are linked, summed and measured exactly as in step 4 (#13, #15), using NIC relationships active on Sep 30, 2026. Score and flags exactly as #22: percentile ranks of `uninsured_dep_share` and `sec_loss_to_equity` within the ranked sample, averaged, top 10% flagged with ties included. There are no outcomes: this is a current list, not a test. Entities with no current call reports (acquired or delisted since Sep 2024) are listed with that reason, never silently dropped. **Limitation:** banks listed after Sep 2024 are missing. | Main for B1 |
| 27 | 2026-11-24 | **Did the system get safer? (absolute comparison).** (a) Median and 90th percentile of each predictor in the Dec 2022 ranked sample (337) vs. today's ranked sample. (b) First Republic benchmark: the number of banks at or above First Republic's Dec 2022 values (uninsured share 67.7%, securities loss / equity 0.30) on both measures, and on each one alone, on both dates. No other thresholds will be tried. | Reported next to the ranking, whatever it shows |

**Results of #26–#27 (run 2026-11-24, after the entries above were committed).** Full report: `outputs/fragility_screen_today.md`.
- Universe 325 entities (Sep 30, 2024 link); Bank of Princeton folded into Princeton Bancorp; **276 ranked** on the Sep 30, 2026 call reports; 48 not ranked (no insured bank linked on that date: acquired or delisted since 2024, or one of the 6 non-banks). Top 10% = 28 banks (score ≥ 0.810).
- **Did the system get safer?** Median uninsured share 36.5% → 36.3% (unchanged); 90th percentile 56.0% → 52.3%. Median securities loss / equity 0.21 → 0.13; 90th percentile 0.54 → 0.31. Banks at or above First Republic's Dec 2022 levels on **both** measures: **8 → 0** (uninsured alone 14 → 4; losses alone 110 → 29).
- So today's top 10% is a *relative* list: bond losses have roughly halved and no bank matches First Republic's 2022 profile on both measures, though uninsured deposits are as high as ever at the median.

## Placebo windows (self-audit finding A, written 2026-11-27, before running)

HC3 standard errors treat banks as independent, but every bank shares the same three trading days (README threat 10). This entry asks how often R1 finds a "significant" uninsured-share effect in ordinary three-day windows, when there is no bank run.

| # | Date | What | Decision |
|---|---|---|---|
| 28 | 2026-11-27 | **Placebo windows.** Every trading day of 2022 is a placebo day 0, as long as days 0, +1 and +2 all fall in 2022 (first Jan 3, last Dec 28). For each window, each main-sample bank's (#17) BHAR over days 0 to +2 is computed exactly like `bhar_0_2` (compounded CRSP returns, including delisting returns, minus the compounded `vwretd`); a bank without a return on all three days is left out of that window. R1's formula is run on each window with the same Dec 2022 predictors and HC3. We report, for the uninsured-share coefficient: **(a)** the share of placebo windows with HC3 p < 0.05 (the true false-positive rate, nominally 5%); **(b)** the placebo p-value for March: the share of windows with \|t\| ≥ R1's \|t\|. We compare t-statistics, not coefficients, because March 2023 was far more volatile than 2022; **(c)** secondary: the share of windows whose coefficient is ≤ R1's. (a)–(c) are also reported on the non-overlapping subset (every third window from Jan 3), since overlapping windows share days. Why 2022: it is before the event and inside our CRSP pull; April–December 2023 is not a quiet period (First Republic failed May 1). The predictors are measured Dec 31, 2022, after these windows, which is fine for a null distribution because nothing is being predicted. No other year, window length or statistic will be tried. | Inference check for R1, reported whichever way it goes. If (b) is above 0.05, the README, dashboard and slides say R1's significance doesn't survive the placebo test |

**Results of #28 (run 2026-11-27, after the entry above was committed).** Full report: `outputs/placebo_windows.md`.
- 249 placebo windows (83 non-overlapping), 329–332 banks each.
- **(a) False positives:** R1's HC3 test finds a "significant" uninsured-share coefficient (p < 0.05) in **9.6%** of the 2022 windows (24 of 249; 10 negative, 14 positive), about twice the nominal 5%. On the non-overlapping windows it's 6.0%. So HC3 p-values are too small here, as README threat 10 says.
- **(b) Placebo p-value for March: 0.084** (all windows); 0.048 on the non-overlapping ones. By the rule written above (all windows), **R1's significance doesn't survive the placebo test.**
- **(c) Size:** no 2022 window has a coefficient as negative as March's −0.112 (the most negative is −0.046, on Mar 16, 2022; 5th–95th percentile −0.019 to 0.020). March was also far more volatile, which is why we rank on t-statistics.
- What we take from it: the March sorting on uninsured deposits is unusually large, but with one event and correlated returns we can't call it statistically significant at 5%. It is borderline (p between 0.05 and 0.10).
