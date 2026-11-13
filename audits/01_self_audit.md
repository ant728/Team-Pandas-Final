# Checkpoint 2 self-audit

**Team Pandas:** Andrew Temo, Mason Friedman, Morgan Waddell, Ryan Carr
**Reviewed:** `main` at commit `8941d8a` (Nov 12, 2026), using the *Skeptical review* prompt (Quick Reference, Starter prompts for coding agents, #5):

> "Review this repo like a skeptical finance professor. Look for look-ahead bias and leakage, merges without validate, unit and frequency mismatches, hard-coded paths or keys, and steps that don't reproduce from run_all.py. List issues ranked by severity; don't fix anything yet."

The reviewer read all of `code/`, `run_all.py`, the README, `specs_tried.md` and the committed outputs. It also checked the data in `outputs/final_dataset.csv` and the raw FDIC files, and rebuilt the project from scratch in a separate checkout.

## 1. What it flagged, and which findings are real

| # | Finding | Severity | Real? | Our response |
|---|---|---|---|---|
| A | **Bank-level measures vs. company-level returns.** Measures are summed from the *bank subsidiaries'* call reports, but the outcome is the *whole company's* stock return. Non-bank-heavy firms (Schwab, Ameriprise, First American, Goldman, Morgan Stanley, AmEx, Synchrony, Discover, Ally, SoFi, LendingClub, ...) are in the sample, which produces impossible or extreme ratios: State Street's uninsured share is 101%; First American's securities losses are 29.1× equity (median 0.21). Nothing is winsorized. | High | **Yes.** One firm drives most of the variance of `sec_loss_to_equity`, so R2's "no effect of securities losses" may be an artifact. | Now disclosed and printed on every run. The fix changes the sample, so it's open (see section 2). |
| B | **The merge silently drops 10 real banks.** `RSSDHCR` is the *top-tier* holder. When a listed company sits under an unlisted parent (a mutual holding company, a controlling LLC, a union), its banks never match. 10 of the 16 unmatched entities are banks (Hilltop, Amalgamated, First Guaranty, Greene County, Lake Shore, TFS, Kentucky First, Broadway, South Plains, Sterling). The README said they were "mostly non-banks." | High | **Yes.** We confirmed it in the raw FDIC data, e.g. PlainsCapital Bank's ($13.5B) top holder is "Diamond HTH Stock Co GP LLC", not Hilltop Holdings. | README corrected. The fix changes the sample, so it's open. |
| C | **Standard errors are too small.** All 323 banks share the same three days, so residuals are cross-correlated. HC3 doesn't address that. Combined with R3 (the coefficient falls from −0.151 to −0.062 without SVB and Signature), the main result is weaker than its p = 0.03 suggests. | High | **Yes.** | Disclosed (README threat 10). Open. |
| D | **The window includes the rescue.** Day +2 (Mar 13) comes after the Mar 12 guarantee of SVB and Signature deposits and the BTFP, which target our two variables directly. | Medium | **Yes.** It's an interpretation issue, not a bug. | Disclosed (threat 9). Open: robustness window planned. |
| E | **Look-ahead in the data vintage.** The FDIC API serves today's revised Q4 2022 data, and the NY Fed link is the 2024 vintage. | Medium | **Partly.** The timing is fine: Q4 2022 reports were due Jan 30, 2023, before the event. But the values may include later amendments. Our FFIEC check (24/24 exact matches) can't detect revisions, because that file is also current. | Already disclosed (threat 2). We accept it: no free as-filed archive exists. |
| F | **Unit mismatches in the loss measures.** HTM losses are pre-tax while equity is after-tax; AFS losses already reduced equity through AOCI. `EQCCOMPI` is labeled accumulated AOCI but is the 2022 OCI flow. | Medium | **Yes.** | Label fix is in PR #8 (Morgan). Tax point disclosed (threat 11). Open. |
| G | **Inputs that might not reproduce.** Live downloads with no file hashes; a yfinance failure crashed `run_all.py`; unpinned package versions; the CRSP pull script wasn't in the repo; the FFIEC check needs a manual download. | Medium | **Yes.** | Mostly fixed in this PR (see below). Hashes and the FFIEC download are still open. |
| H | **"Choices fixed before looking at returns" overstated.** The outcome (compounded BHAR) was picked after seeing four banks' returns. | Medium | **Yes.** It's logged in `specs_tried.md` #1–#3, but the sentence overclaimed. | Fixed: `specs_tried.md` now states the exception. |
| I | **A missing return would count as 0%.** `prod()` skips NaN. | Low | **Real risk, no current case.** We checked: 0 missing returns in the window. | Fixed: step 3 now stops on any missing return. |
| J | **Stale output and a growing log.** The committed `hand_checks.md` lacked the FFIEC row; the provenance log gains 4 lines per run. | Low | **Yes.** | `hand_checks.md` regenerated. Log growth is open. |
| K | **Hard-coded values.** `00_build_universe.py` hard-codes `20240930`; `06_hand_checks.py` repeats dates, tickers and JPM's RSSD ID. | Low | **Partly.** The values in `06` are deliberate: a hand check should not read the settings it is checking. | `00`'s date moved to `config.py`. `06` left as is, on purpose. |

**What held up:**
- **Reproduces exactly.** A fresh `python run_all.py` reproduced `final_dataset.csv`, the regressions and the summary statistics exactly.
- **Merges are validated.** Every merge uses `validate=`, and the keys have uniqueness asserts.
- **No secrets or machine-specific paths.** There are no API keys or absolute paths in the code.
- **Licensed data stays private.** Raw CRSP data is not in git history.
- **No leakage.** The estimation window (−250 to −30) doesn't overlap the event, and no outcome data feeds a predictor.

## 2. What we fixed in this PR, and what's still open

### Fixed in this PR

1. **Hand checks now cover every pipeline step** (checklist item 8). Two new checks:
   - **Step 0:** the universe size, recounted from the raw NY Fed link with a plain loop (343 = 343).
   - **Step 5:** R1's uninsured-share coefficient and its HC3 standard error, recomputed in plain numpy with the sandwich formula (−0.1506 and 0.0692, both match).
2. **yfinance can no longer break the pipeline.** It's only a cross-check, so a failure is now a warning, and its checks are marked SKIPPED instead of crashing `run_all.py`. Tested with a simulated outage.
3. **Missing-return guard.** Step 3 stops if any event-window return is missing, instead of silently treating it as 0%.
4. **Range warnings.** Step 4 prints every in-sample entity with an uninsured share above 100%, or securities or HTM losses larger than equity, on every run.
5. **Pinned package versions** in `requirements.txt` (Python 3.12), matching the versions that built the committed outputs.
6. **CRSP pull code is now in the repo** at `code/wrds/pull_crsp.do`, linked from the README provenance table. It's only code; the data stays out.
7. **README corrections:**
   - The unmatched entities are 10 banks and 6 non-banks, not "mostly non-banks."
   - New threats 8–11: bank vs. company measurement, the rescue inside the window, correlated errors, pre-tax vs. after-tax.
   - The Python version is stated.
8. **`specs_tried.md`** now says the outcome definition was chosen after seeing four banks' returns.
9. **Smaller fixes:**
   - `hand_checks.md` regenerated;
   - the NY Fed vintage date moved into `config.py`;
   - the `.gitignore` comment no longer claims the code recreates the CRSP files.

### Still open, with our plan
Every item that changes the sample or the estimates will be written into `specs_tried.md` **before** it is run, and reported alongside the current baseline, not instead of it. Target: Checkpoint 3 (Sat Nov 21).

| Issue | Plan | Owner |
|---|---|---|
| B. 10 banks dropped by the merge | Map each bank to *every* holding company above it, using the FFIEC NIC relationships file (not just the top-tier `RSSDHCR`), so a listed mid-tier company gets its banks. Assert that every listed bank holding company matches, then rerun R1–R4. | Andrew |
| A. Non-banks and extreme ratios | Pre-specify a "bank-centric" sample: drop entities whose bank subsidiaries are a small share of the company's assets, with the cutoff written down before running. Add winsorized (1st/99th percentile) versions of the ratios as robustness. | Andrew |
| C. Correlated errors | Placebo inference: run R1 on many non-event three-day windows from 2022 to get the distribution of the coefficient when nothing happened, and compare the March coefficient to it. | Morgan |
| D. Rescue inside the window | Add a robustness spec using only Mar 9–10 (days 0 to +1), before the Mar 12 rescue. | Ryan |
| F. Units in the loss measure | After PR #8 merges (OCI label), add an after-tax version of the HTM loss (× (1 − 21%)) as robustness, together with the Zions transfer-aware measure. | Morgan |
| G. Provenance | Record a SHA-256 hash of every downloaded file in `data/provenance_log.csv`, and stop the log from growing on reruns that pull identical data. | Ryan |
| E. Data vintage | Accept and disclose. Free as-filed call report archives don't exist, and the timing itself is clean. | Ryan |

## 3. The 10-point checklist (`00_PROJECT_SEEDS`)

| # | Standard | Status | Note |
|---|---|---|---|
| 1 | It reproduces | **OK** | A fresh `run_all.py` rebuilt every output exactly. The licensed CRSP files must be placed by hand (README step 2). |
| 2 | Every input has a provenance | **OK (minor problem)** | Every input is in the README table and `data/provenance_log.csv`, including the CRSP pull code. No file hashes yet. |
| 3 | Unit of observation is right | **Problem** | Keys are asserted and every merge uses `validate=`. But 10 listed banks are dropped by the entity mapping, and non-bank companies are measured by their bank subsidiaries only (findings A and B). |
| 4 | No look-ahead | **OK (minor problem)** | Q4 2022 call reports were public before Mar 9, 2023. CRSP keeps the failed banks, so there's no survivorship bias. The FDIC values are the current (possibly amended) vintage. |
| 5 | No LLM leakage | **OK** | No LLM is used to build any variable or prediction. |
| 6 | No p-hacking | **OK** | `specs_tried.md` logs all 10 specifications, including the dropped ones, and the out-of-sample screen was written down before it was run. The BHAR choice was made after seeing four banks, which is now stated. |
| 7 | Magnitudes, not just stars | **OK** | A 1 SD (16 pp) higher uninsured share goes with a 2.4 pp lower three-day BHAR, against an average of −10.3%. The economic meaning for a regulator or investor still needs to go in the write-up. |
| 8 | Checks by hand | **OK** | Every step now has at least one independent recomputation (`outputs/hand_checks.md`), all passing. |
| 9 | Honest limits | **OK** | 11 threats to validity in the README, including everything this review found. |
| 10 | We understand it | **OK** | The team walked through every pipeline step together, so each member can explain each step, including the parts an AI agent wrote. |

---

## Dashboard audit (Mason Friedman)

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
