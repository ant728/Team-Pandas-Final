# Checkpoint 3 self-audit (v1)

**Team Pandas:** Andrew Temo, Mason Friedman, Morgan Waddell, Ryan Carr
**Reviewed:** branch `v1/part-a-robustness` on Nov 18, 2026, covering everything since the instructor-audited commit `88005d3`: the audit fixes (PRs #16–#18), the main-sample decision, robustness specs R7–R10, and the who's-next screen (step 8). We used the *Skeptical review* prompt (Quick Reference, Starter prompts for coding agents, #5):

> "Review this repo like a skeptical finance professor. Look for look-ahead bias and leakage, merges without validate, unit and frequency mismatches, hard-coded paths or keys, and steps that don't reproduce from run_all.py. List issues ranked by severity; don't fix anything yet."

The reviewer read every changed file in `code/` and `app/`, `run_all.py`, the README, `specs_tried.md` and the committed outputs. It also rebuilt the project from a fresh checkout in a new Python environment created only from `requirements.txt`.

## 1. What it flagged, and which findings are real

Ranked by severity. Nothing found is a coding error that changes a number; the issues are about inference, choices made after seeing data, and reproducibility.

| ID | Finding | Severity | Real? | Status |
|---|---|---|---|---|
| A | **The main result is fragile, and it's a Monday effect.** R1's uninsured-share coefficient is −0.112 with p = 0.047. Over Mar 9–10 alone (R7) it's −0.053 (p = 0.35); the sorting appears on Mon, Mar 13, after the rescue. There is one event, and HC3 still treats residuals as independent across banks (R5's KRE control helps but doesn't fix that). | Medium | **Yes.** | Disclosed (README threats 1, 9, 10; `specs_tried.md` results). Open: placebo windows for honest p-values. |
| B | **Some choices were made after seeing data.** The main sample (#17) came after the instructor's leave-out table; the bank-centric 20% cutoff (#20) came after seeing the ratio distribution; the compounded BHAR came after the 4-bank proof of concept. | Medium | **Yes**, a forking-paths risk. | Each is disclosed where it's logged, and the alternatives are reported next to the choice (R6 and R3 next to R1; R1 next to R10). No further action. |
| C | **Two inputs drift between runs, and the run now needs yfinance.** KRE prices come from yfinance, whose adjusted closes shift slightly each download (in the fresh rebuild `kre_beta` moved by up to 0.000006, and one rounded number in `regressions_v0.md` changed in the 4th decimal). The FDIC API also revises old data (CrossFirst's uninsured share moved by 8e-8 since Nov 10). Because `kre_beta` is now required, step 2 stops the run if yfinance is down, where before it failed soft. Four inputs are manual: the licensed CRSP files and three CAPTCHA-protected NIC files. | Medium | **Yes.** | **KRE part fixed in this PR:** the KRE prices are committed and hash-checked, so `kre_beta` no longer drifts and the run no longer needs yfinance. Open: the FDIC revisions (accepted, threat 2) and full hashes for the manual inputs. |
| D | **The NIC industry codes are today's, not Dec 2022's.** R10 uses `ACT_PRIM_CD` from the current attributes files. (The relationships file used for the A4 link is dated, so it has no such issue.) | Low | **Yes**, but small: the code only decides 3 entities (Goldman, Morgan Stanley, Ally), and none of them plausibly changed industry. | Disclosed in `specs_tried.md` #20. Accept. |
| E | **Some documents quote numbers that are no longer in `outputs/`.** `PROPOSAL.md` (323 banks, −0.151, 12 checks) and the Checkpoint 2 audits are dated snapshots; the results have changed since (A4 fix, main sample). | Low | **Yes**, for "every number traces to `outputs/`". | Partly fixed: the README now labels the proposal as dated Nov 14. Open: a one-line note at the top of `PROPOSAL.md`. |
| F | **The screen ranks non-banks too.** First American is #2 only because of its 29× securities-loss ratio. Precision is low (1 failure among 34 flags), and the failure outcome has a single listed event, so recall of 1/1 says little. | Low | Real, but it's the pre-specified rule and the report says so. | Disclosed in `outputs/fragility_screen.md` and `specs_tried.md`. Not changed: changing the rules after seeing the results would be p-hacking. |
| G | **Stale dashboard labels.** The header badge says "Checkpoint 2 · Prototype", the footer says "Checkpoint 2 dashboard", and the A2 screenshot in `docs/images/` shows the old numbers. The Intro counts the 333 in-sample banks while the main regressions use 332 (no SVB). | Low | **Yes.** | Open (Mason). |
| H | **File names say v0.** `outputs/regressions_v0.*` now hold the v1 results. | Low | Cosmetic. | Accept for now; renaming means changing the dashboard and the README together. |
| I | **Magnitude lines use one SD for every spec.** The one-SD effect for R3 and R6 uses the main sample's SD, not that spec's own sample. The difference is tiny (one bank). | Low | Real, cosmetic. | Open, trivial. |
| J | **Hard-coded tickers and dates in the hand checks** (WAL, FRC, SCHW, TFSL; Mar 13 and Dec 29). | — | No. They're deliberate: a check that imports the pipeline's settings isn't independent. Same as finding K at Checkpoint 2. | No action. |

**What held up:**
- Every merge uses `validate=`, and every lookup map is keyed on something asserted unique. Keys `rssd_id` and `permco` are asserted unique.
- **No look-ahead in the predictors or the screen.** Call reports are Q4 2022, market values are from Dec 30, 2022, betas use trading days −250 to −30, and every screen outcome starts after Mar 13, 2023. The NIC ownership walk uses relationships dated as of Dec 31, 2022.
- **Units match.** `bank_eq_to_mcap` divides $ thousands by $ thousands (CRSP `shrout` is in thousands of shares); the hand check on Schwab confirms 5.45%. KRE and CRSP returns are both daily total returns on the same trading calendar, and step 3 stops if a KRE day is missing.
- **Every new specification was written into `specs_tried.md` and committed before it was run** (#13–#25); the commit history shows the order.
- **Licensing holds.** The market values derived from CRSP stay in `data/interim/` (git-ignored); only per-company aggregates (returns, betas, ratios) are published.
- **18 hand checks**, at least one for every step, including two new ones for the screen.
- No API keys, passwords or absolute paths in the code.

## 2. What we fixed in this PR, and what's still open

### Fixed in this PR
1. **README cleanup.** The Checkpoint 0 candidate ideas (about 200 lines on two projects we didn't pick) moved to `docs/checkpoint0_candidates.md`. The README is now about the project as it is.
2. **The question in the README matches what we do.** It said "which listed banks look like that today?", but the screen is an out-of-sample test on Dec 2022 data, not a ranking of banks today.
3. **Stale labels:** "Checkpoint 2 dashboard", "Threats to validity (so far)", the dashboard's file list, the repo-structure tree (steps 07–08, `docs/`, `inputs/`, the NIC files) and the specification count at the top of `specs_tried.md`.
4. **Status line** links every audit and marks `PROPOSAL.md` as dated Nov 14 (finding E, in part).
5. **KRE drift (finding C):** `data/raw/kre_daily.csv` is now committed, the one raw file in git (312 public ETF prices). Step 2 uses it instead of re-downloading, and step 3 checks its sha256 against `config.KRE_SHA256` and stops on a mismatch. `.gitattributes` keeps its bytes identical on every operating system. A full rerun now reproduces the committed outputs byte for byte.

### Still open, with our plan
Target: the final audit (presentations Dec 1/3). Anything that changes the sample or the estimates goes into `specs_tried.md` before it's run.

| Issue | Plan | Owner |
|---|---|---|
| A. Inference with one event | Placebo windows: run R1 on many non-event three-day windows in 2022 and compare the March coefficient to that distribution. | Morgan |
| C. Remaining inputs | Record full sha256 hashes for every raw input, especially the manual CRSP and NIC files, and check them in the pipeline the way step 3 checks KRE. | Ryan |
| E. Dated numbers in the proposal | One line at the top of `PROPOSAL.md` saying its numbers are from Nov 14 and pointing to the README for current results. The proposal's text stays as written. | Andrew |
| G. Dashboard labels | Update the header badge and footer, retake the A2 screenshot, and show the main-sample count (332) next to the in-sample count. | Mason |
| I. Magnitude SDs | Use each spec's own sample SD. | Andrew |

## 3. The 10-point checklist (`00_PROJECT_SEEDS`)

| # | Standard | Status | Note |
|---|---|---|---|
| 1 | It reproduces | **OK (minor problem)** | A fresh checkout in a new environment built only from `requirements.txt` ran `run_all.py` end to end with all 18 checks passing. The only differences from the committed outputs came from KRE's yfinance drift: `kre_beta` moved by up to 0.000006, and one rounded number (R5's intercept SE, 0.0873 vs 0.0872) changed in the 4th decimal. The licensed CRSP files and three NIC files are placed by hand ("How to run"). After committing the KRE prices, a rerun reproduces the committed outputs byte for byte; only the FDIC API's own revisions could still move a number (finding C). |
| 2 | Every input has a provenance | **OK** | Every input is in the README table and `data/provenance_log.csv`, the manual ones with sha256 prefixes. Full hashes are planned. |
| 3 | Unit of observation is right | **OK** | One row per listed entity, keys asserted, every merge validated. The NIC walk now matches 337 of 343 (all 6 misses are non-banks), bank-owned banks aren't double-counted, and R10 tests the bank-only sample. |
| 4 | No look-ahead | **OK (minor problem)** | All predictors are from before Mar 9, 2023 and all screen outcomes after Mar 13. The FDIC data and the NIC industry codes are current vintages (findings C, D). |
| 5 | No LLM leakage | **OK** | No LLM builds any variable, prediction or screen rule. The screen's predictors were chosen knowing the SVB story, which the rules say: it's a retrospective test, not a blind forecast. |
| 6 | No p-hacking | **OK (minor problem)** | Every specification is logged before running, including the screen. Two choices came after seeing data and are disclosed with their alternatives reported (finding B). |
| 7 | Magnitudes, not just stars | **OK** | A 1 SD (16 pp) higher uninsured share goes with a 1.8 pp lower three-day BHAR, against an average of −10.0% (`outputs/regressions_v0.md`). The screen reports recall and precision against base rates. |
| 8 | Checks by hand | **OK** | 18 independent recomputations, at least one per step, all passing (`outputs/hand_checks.md`). |
| 9 | Honest limits | **OK** | 11 threats in the README, updated with R5–R10; the Monday effect and the screen's low precision are stated where the results are. |
| 10 | We understand it | **Not yet** | The new pieces (NIC walk, main sample, KRE beta, bank-centric rule, the screen) need a team walkthrough before Saturday. |
