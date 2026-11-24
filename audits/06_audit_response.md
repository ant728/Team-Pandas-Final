# Response to the instructor audit (Checkpoint 3)

Team Pandas · November 24, 2026 · responds to [`05_instructor_audit.md`](05_instructor_audit.md) (audited commit `e8169a9`), tracked in [issue #22](https://github.com/ant728/Team-Pandas-Final/issues/22).

| ID | Finding | Response | Where |
|---|---|---|---|
| B1 | "Who's next" ranks banks on December 2022 data, not today's | **Fixed:** the same pre-specified score now also runs on the Sep 30, 2026 call reports, with a limitation disclosed | Commit `ef66cd2`; `specs_tried.md` #26–#27 (logged in `7f00315`, before any 2026 data was downloaded); `code/09_screen_today.py` |
| B2 | v1 results live in files named `v0` | **Fixed** | Commit `bde298d` |

## B1 · Fixed, with one limitation disclosed

**What we added.** Step 9 (`code/09_screen_today.py`) applies the Dec 2022 screen's rules (#21–#22) to the latest call reports in the FDIC API, Sep 30, 2026:
- the same NIC ownership link and bank-owned-bank rule (#13, #15), with relationships active on that date;
- the same measures, percentile-rank score and top-10% flag.

It writes `outputs/fragility_screen_20260930.csv` (one row per bank, ranked) and a report, `outputs/fragility_screen_today.md`. The dashboard's Who's Next page shows the list in a "Who's next today" card labeled "Call reports of Sep 30, 2026", next to the 2023 test.

**Why we also compare levels with Dec 2022 (#27).** The score ranks banks against each other, so it always flags a top 10%, however safe banks are. A regulator or investor needs to know how fragile that group is, not just who's in it. So the report and dashboard put the two dates side by side:

| | Dec 31, 2022 | Sep 30, 2026 |
|---|---|---|
| Banks ranked | 337 | 276 |
| Median uninsured share | 36.5% | 36.3% |
| 90th percentile, uninsured share | 56.0% | 52.3% |
| Median securities loss / equity | 0.21 | 0.13 |
| 90th percentile, securities loss / equity | 0.54 | 0.31 |
| Banks at or above First Republic's Dec 2022 levels on both measures | 8 | **0** |

Bond losses relative to equity have roughly halved, while uninsured deposits are as high as ever at the median. No bank today matches First Republic's Dec 2022 profile on both measures. Today's top 10% (28 banks, led by First American, Cullen/Frost and Lakeland Financial) is therefore a list of the *relatively* most exposed banks, not of banks as exposed as the 2023 failures.

**Limitation (disclosed in `specs_tried.md` #26, the report, the dashboard and the README).** The universe is the NY Fed CRSP–FRB link at the end of its latest vintage, Sep 30, 2024; no newer vintage is published. Banks listed after that date are missing. The 48 entities with no insured bank linked on Sep 30, 2026 are listed with that reason in the report, never silently dropped: banks acquired or delisted since 2024, plus the 6 non-banks.

**Checks.** A new hand check sums JPMorgan's Sep 2026 uninsured deposits from the raw FDIC rows by hand. A full `python run_all.py` passes all 19 checks, and the Dec 2022 outputs are unchanged.

## B2 · Fixed

`outputs/regressions_v0.csv` and `.md` are now `outputs/regressions.csv` and `.md`, titled "Regressions". `05_regressions.py`, `06_hand_checks.py`, the dashboard (its fetch path and the local server's file list), `app/README.md` and `README.md` all use the new names. The numbers are unchanged. Our earlier audit files (`01`–`04`) keep the old name, because they describe the repo as it was.
