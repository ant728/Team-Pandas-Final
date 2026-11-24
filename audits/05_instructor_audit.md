# Instructor audit: Team Pandas, Checkpoint 3

**Repo:** ant728/Team-Pandas-Final · **Audited commit:** `e8169a9` (2026-11-20, `main`, merge of PR #20) · **Seed:** 6, bank fragility: SVB, and who's next · **CP2 audit:** `audits/02_instructor_audit.md` (commit `88005d3`)

> Note from your human teacher: This review is generated with minimal supervision from Opus 5.5-high. It is thorough, but can be too generous at times and doesn't know my taste for what is "good". Grades it and I would assign are correlated, but noisy, ok? If you want additional feedback from _me_, you need to find me before/after/during class or during office hours for a guaranteed speedy reply. I will try to respond to emails and issues, but can not respond to student inquiries around the clock across the final weeks of class. Response times will be unpredictable, though during Thanksgiving week, I will do my best to respond quickly virtually, as in person options will be nil.

## Summary

A strong v1, and your CP2 follow-up is thorough.
- **Reproduction.** A clean environment built only from `requirements.txt` now runs `05_regressions.py`, and the outputs are byte-identical (the CP2 Blocking finding is fixed).
- **Independent checks.** My own code reproduces:
  - all four headline regressions (R1, R3, R5, R6);
  - the returns and KRE betas, from a fresh yfinance pull;
  - the uninsured shares, from the raw FFIEC call reports.
- **Each fix is logged.** Every CP2 fix has a dated `specs_tried.md` entry, and you disclosed that the SVB decision came after seeing the audit's table.
- **The dashboard** serves and renders every page with no errors, from `outputs/`.

What's left is small: the "today" half of the seed (B1), and naming (B2).

## Follow-up on your Checkpoint 2 audit

Response file: `audits/03_audit_response.md` found (on `main`).

| CP2 finding | Status | Evidence |
|---|---|---|
| A1 · Pinned requirements don't install | fixed | Commit `23c0814`. `uv venv --python 3.12 && uv pip install -r requirements.txt` (scipy 1.13.1, statsmodels 0.14.2, patsy 0.5.6), then `python code/05_regressions.py`: exit 0, 2.3 s. `regressions_v0.csv`, `regressions_v0.md` and `summary_stats.csv` are byte-identical to the committed files |
| A2 · Result depends on SVB/Signature | fixed | `specs_tried.md` #17 names the main sample (without SVB, Signature at −100%) and discloses that the decision followed the audit's table. `regressions_v0.csv` has all three rows (R1 n = 332: −0.112, SE 0.056; R6 n = 333: −0.149; R3 n = 331: −0.065), and the dashboard's Results page shows the same three rows |
| A3 · SEs ignore the common shock | fixed | `specs_tried.md` #14. R5 adds `kre_beta`: uninsured share −0.109 (SE 0.053), `kre_beta` −0.141 (SE 0.036). The remaining limitation is in README threat 10. My own HC3 gives the same numbers |
| A4 · Ten banks dropped by the link step | fixed | Commit `80d3983`. `outputs/final_dataset.csv`: `has_fdic` is True for 337 of 343. HTH, AMAL, FGBI, GCBC, LSBK, TFSL, KFFB, BYFC, SPFI and SBT all have `has_fdic` = `in_sample` = True. The 6 unmatched are AIG, SEIC, BEN, IMH, TROW and MET. Checked on the committed outputs. Step 04 itself needs the FDIC API and the manual NIC file, so it wasn't rerun |

**4 of 4 fixed, 0 still open.**

## Checkpoint 3 checks

| Check | Result |
|---|---|
| Reruns from scratch (full sample) | ⚠️ `00`, `02` and `05` rerun, with outputs identical. `01`, `04`, `07` and `08` need the FDIC API (a host the audit doesn't use) or CRSP, and `06` needs the FDIC raw file (see below) |
| Inputs have provenance | ✅ `data/provenance_log.csv`, README provenance table, a KRE SHA-256 check in step 3 |
| Keys unique, merges validated | ✅ `rssd_id`/`permco` asserted. The bank-owned-bank double count was found and fixed (#15) |
| No look-ahead / survivorship | ✅ Q4 2022 reports, the Dec 31, 2022 link universe, failed banks kept with delisting returns |
| LLM leakage handled | n/a |
| `specs_tried.md` complete | ✅ #13–#25, each committed before its run (e.g. `c9b6428` "logged before running", then `2890de8`) |
| Magnitudes discussed | ✅ one-SD effects (`regressions_v0.md`): −1.8% BHAR per SD of uninsured share (R1) |
| Hand checks | ✅ 14 in `outputs/hand_checks.md` (WAL's KRE beta, TFS assets, and more) |
| Threats to validity | ✅ README threats, including 10 (common shock) and 8 (non-bank-centric entities) |
| Every number traces to `outputs/` | ✅ README "Current outputs" and the response file's tables match `regressions_v0.csv` |
| Dashboard matches `outputs/` | ✅ Results page: "Main: excluding SVB 332 −0.112 0.056", "Including SVB 333 −0.149 0.066", "Excluding SVB and Signature 331 −0.065 0.030", read from `regressions_v0.csv` |

Steps not rerun by design: `01_download_fdic.py` and everything that reads its output (`04`, `06`, `07`, the FDIC failures in `08`), because `api.fdic.gov` was blocked at CP2 and the audit doesn't use it. `03_crsp_returns.py` and the CRSP part of `08` use instructor-provided WRDS/CRSP data. I started from your committed `final_dataset.csv`, `bank_returns.csv` and screen outputs. These are not counted against you.

## Getting ready for Dec 1

Presentations run only from URLs, with a hard cutoff at 9 minutes (10:45 section) or 10 minutes (12:10 section). Put your URL(s) in column G of the Team Projects sheet.

| Check | Result |
|---|---|
| Dashboard launches from a clean clone | ✅ static site. `python app/serve.py --port 8765` on a clean export of `e8169a9`, then `/app/` returned 200. A headless browser loaded `#intro`, `#results` and `#screen`: 0 console errors, 0 page errors, 0 failed requests |
| Dashboard shows the v1 numbers from `outputs/` | ✅ it fetches `outputs/final_dataset.csv`, `regressions_v0.csv` and the two screen files (`app/dashboard.mjs:5,305,367`). "343 / 333 / 332" on the intro page matches `final_dataset.csv` |
| README links the live URL(s) | ✅ `README.md:3` links https://ant728.github.io/Team-Pandas-Final/app/ (the live site itself wasn't checked). A static site has no requirements to drift, but make sure GitHub Pages builds from `main` |

**Core story for 9–10 minutes:** the question; the 332-bank main regression and its one-SD magnitude; the three-row SVB/Signature table (it is your honesty slide); then "Who's next". The HTM-loss coefficient is small and insignificant in every row. Say so plainly: it is a finding.

## What holds up

- **A clean install works**, and step 05 reproduces byte for byte (A1).
- **Independent regressions.** My own OLS with HC3 errors reproduces R1 (−0.1120, SE 0.0563, n = 332), R3 (−0.0653, SE 0.0304), R5 (−0.1091, SE 0.0526) and R6 (−0.1492, SE 0.0657) to 4 decimals.
- **Independent returns and betas.** From a fresh yfinance pull, `bhr_0_2` (Mar 8 close to Mar 13 close) matches for all 15 of 20 sampled banks that Yahoo still has, within 0.0005 (e.g. UMBF −0.2414 vs −0.2412). `kre_beta` over sessions −250 to −30, against your committed KRE closes, matches with a median absolute difference of 0.0000 (max 0.0011, UNB). The other 5 (SBNY, BRKL, OBNK, CFB, AMNB) are no longer on Yahoo, which is why CRSP is the right source.
- **Independent measures.** For the 10 single-bank entities whose own RSSD files a call report, `RCON5597 / RCON2200` from the FFIEC CDR 12/31/2022 bulk files equals your `uninsured_dep_share` (max difference 5.6e-17).
- **A careful A4 fix,** including the double-counting problem you found while building it (#15).
- **Seed 6 items:**
  - **Call-report date:** the quarter before the event.
  - **ID links:** NIC relationships walked as of 2022-12-31.
  - **Small illiquid banks:** R10 (bank-centric) and the winsorized R8–R9.

## New findings

### B1 · Minor · "Who's next" ranks banks on December 2022 data, not today's

**Evidence:** `outputs/fragility_screen.md`: "The score uses only Dec 31, 2022 call reports". The dashboard's "Who's Next" page shows "343 of 343 entities · December 2022 Call Reports". Seed 6's second question is "Which banks look like that **today**?", and its dashboard is "a 'fragility screen' of today's listed banks".

**Why it matters:** Your out-of-sample check (would December 2022 have flagged the 2023 failures?) is a good validation of the screen. But the reader the seed names, a regulator or investor, wants the current list.

**Fix:** Run steps 01 and 04 for the latest quarter (`CALL_REPORT_DATE`, e.g. 2026-09-30) and apply the same pre-specified score (#21–#22) to today's listed banks. Show it as a second tab, labeled with its report date.

**How to show it's fixed:** `outputs/fragility_screen_<latest date>.csv` exists, and the dashboard shows the report date.

### B2 · Minor · v1 results live in files named `v0`

**Evidence:** The Checkpoint 3 regressions are in `outputs/regressions_v0.csv` and `regressions_v0.md` ("# v0 regressions"), while the dashboard header says "v1 · Checkpoint 3".

**Fix:** Rename to `regressions.csv`/`.md` (or `_v1`), and update `app/dashboard.mjs`, `06_hand_checks.py` and the README.

**How to show it's fixed:** No v1 output is labeled v0.

## How to respond

This audit is `audits/05_instructor_audit.md` in your repo (`04` is your own `04_self_audit.md`). Fix what you can, then add `audits/06_audit_response.md`, replying to each **B** finding (no CP2 findings are still open): fixed (the commit), disputed (why), or disclosed as a limitation (where).

There's no separate deadline for this response. Keep working through these until your final deliverables are due: the final repo is audited again then.
