# FIN 331 Final Project: Team Pandas

**Live dashboard:** https://ant728.github.io/Team-Pandas-Final/app/

**Team:** Andrew Temo (ant728), Mason Friedman (MasonF9897897), Morgan Waddell (mow228-boop), Ryan Carr (rcarr37)

**Status (final, in progress):** the March 2023 event study on the full sample (333 banks, 10 specifications), the out-of-sample who's-next screen, and the same screen on today's call reports (Sep 30, 2026). Audits: [self-audit, CP2](audits/01_self_audit.md) · [instructor, CP2](audits/02_instructor_audit.md) · [our response](audits/03_audit_response.md) · [self-audit, CP3](audits/04_self_audit.md) · [instructor, CP3](audits/05_instructor_audit.md) · [our response](audits/06_audit_response.md). Proposal: [`PROPOSAL.md`](PROPOSAL.md) (HW8, Nov 14; its numbers are from that date).

## Our project: bank fragility (Seed 6)

**Question:** When Silicon Valley Bank failed in March 2023, did banks that relied more on uninsured deposits and had larger hidden losses on their bonds fall more? And would those two traits, measured before the crisis, have flagged the banks that got into trouble next?

**One row of the final dataset = one listed bank entity**: the holding company, or the bank itself if it has none. Each row has the entity's Q4 2022 call report measures and its stock's abnormal return over Mar 9–13, 2023. Key: `rssd_id` (also unique on `permco`; both asserted). The sample is every entity in the NY Fed CRSP–FRB link on Dec 31, 2022 (343), including banks that later failed or merged.

### How to run
1. `pip install -r requirements.txt` (Python 3.12; package versions are pinned to the ones that built the committed outputs)
2. Put the four CRSP files in `data/raw/crsp/`: `crsp_daily_2022_2023.csv`, `crsp_market_vwretd.csv`, `crsp_delistings.csv`, `crsp_permcos.csv`. They are **licensed (Lehigh users only)** and not in the repo. Get them from the Google Drive folder Prof. Bowen shared with the team.
3. Download three FFIEC NIC files (CSV) from the [NIC data download page](https://www.ffiec.gov/npw/FinancialReport/DataDownload), **Relationships**, **Attributes- Active** and **Attributes- Closed**, and save the ZIPs in `data/raw/nic/` with their default names. It's public, but the site blocks scripts with a CAPTCHA, so this is a manual step.
4. `python run_all.py`

`run_all.py` downloads everything else, builds the dataset, runs the regressions, and runs the hand checks. It stops if any check fails. If yfinance can't deliver the three cross-check banks, the run continues and those checks are marked SKIPPED. KRE's daily prices (the regional-bank ETF used for `kre_beta`) are **committed** in `data/raw/kre_daily.csv`, because yfinance re-adjusts them slightly on every download; step 2 doesn't re-download them, and step 3 stops if the file's sha256 doesn't match `config.KRE_SHA256`.

Current outputs:
- [`outputs/final_dataset.csv`](outputs/final_dataset.csv): all 343 entities, with flags for why any are out of the sample
- [`outputs/regressions.md`](outputs/regressions.md): the cross-sectional regressions, with magnitudes. **Main result (R1, 332 banks, SVB left out as the trigger):** a one-SD higher uninsured share (16 pp of domestic deposits) goes with a 1.8 pp lower three-day BHAR (coefficient −0.112, p = 0.047); the average bank's BHAR was −10.0%. With SVB included it's −0.149 (p = 0.023); without SVB and Signature, −0.065 (p = 0.032).
- [`outputs/summary_stats.csv`](outputs/summary_stats.csv): descriptive statistics
- [`outputs/fragility_screen.md`](outputs/fragility_screen.md): **who's next.** A screen built only from Dec 2022 call reports (uninsured share and securities losses, top 10% flagged) flags First Republic (rank 28 of 337), the only listed bank that failed after Mar 13, 2023, but not PacWest (rank 65). It catches 2 of the 4 stocks that lost half their value by year-end. The flagged group's precision is low (1 failure among 34 flags), so this is a shortlist, not a forecast. Rules written before ranking: `specs_tried.md`.
- [`outputs/fragility_screen_today.md`](outputs/fragility_screen_today.md): **who's next today.** The same score on the Sep 30, 2026 call reports ranks 276 listed banks; the top 10% is 28 banks. Because the score is relative, we also compare levels with Dec 2022: securities losses relative to equity roughly halved (median 0.21 → 0.13), uninsured shares are unchanged at the median (36%), and **no bank today matches First Republic's Dec 2022 profile on both measures (8 did in Dec 2022)**. It covers companies listed on Sep 30, 2024, the end of the latest NY Fed link (`specs_tried.md` #26–#27).
- [`outputs/hand_checks.md`](outputs/hand_checks.md): independent recomputations, at least one for every step, all passing

### Dashboard

From the repository root, run `python3 app/serve.py` and open
`http://127.0.0.1:8765/app/`. The app reads the committed
[`outputs/final_dataset.csv`](outputs/final_dataset.csv) and requires no package
install. The local server serves only the dashboard assets and four published
output CSVs (the dataset, the regressions, and the two screen files). See [dashboard instructions](app/README.md) for the data contract.

Pages: Intro, Method, March 2023 Results (scatter, bank inspector, and the failed-bank sensitivity table), and Who's Next (the screen's results and a sortable table of every bank). Also see the [Zions measurement note](docs/zions_measurement.md).

### Pipeline
| Step | Script | Reads | Writes |
|---|---|---|---|
| 0 | `code/00_build_universe.py` | NY Fed CRSP–FRB link | `data/processed/universe_20221231.csv` (one row per entity), `requests/crsp_permcos.csv` |
| 1 | `code/01_download_fdic.py` | FDIC API | `data/raw/fdic_financials_20221231.csv` (one row per bank), `data/raw/fdic_institutions.csv`, `data/raw/fdic_failures_2023.csv` |
| 2 | `code/02_download_prices.py` | yfinance | `data/raw/kre_daily.csv` (KRE, for `kre_beta`), `data/raw/prices_check.csv` (3 banks, cross-check only) |
| 3 | `code/03_crsp_returns.py` | `data/raw/crsp/`, KRE | `data/processed/bank_returns.csv` (one row per bank: BHAR, CAR, market beta, KRE beta), `data/interim/crsp_event_days.csv` (git-ignored) |
| 4 | `code/04_build_dataset.py` | steps 0, 1, 3, NIC files | `data/processed/bank_measures.csv`, `data/processed/bank_entity_map.csv`, `outputs/final_dataset.csv` |
| 5 | `code/05_regressions.py` | `outputs/final_dataset.csv` | `outputs/regressions.*`, `outputs/summary_stats.csv` |
| 6 | `code/06_hand_checks.py` | raw files, outputs | `outputs/hand_checks.md` (`run_all.py` runs this step **last**, so it can recheck step 8 too) |
| 7 | `code/07_zions_reconciliation.py` | sourced Zions disclosures and raw FDIC report | `outputs/zions_reconciliation.csv`, `outputs/zions_measure_comparison.csv` |
| 8 | `code/08_fragility_screen.py` | `outputs/final_dataset.csv`, FDIC failures, CRSP after Mar 13 | `outputs/fragility_screen.csv` (one row per bank), `outputs/fragility_screen.md` (report), `outputs/fragility_screen_scorecard.csv` |
| 9 | `code/09_screen_today.py` | `outputs/final_dataset.csv`, `outputs/fragility_screen.csv`, Sep 30, 2026 call reports, NIC relationships | `outputs/fragility_screen_20260930.csv` (today's ranking), `outputs/fragility_screen_today.md` (report), `outputs/fragility_screen_today_summary.csv` (Dec 2022 vs. today) |

Settings (event dates, windows, call report quarter, field list, delisting assumption) live in one place: `code/config.py`.

**Linking banks to listed entities (step 4).** Every FDIC-insured bank is assigned to a sample entity: to itself, if the bank itself is listed (e.g. First Republic, Signature, Zions), or otherwise to the *highest listed company that controls it* on Dec 31, 2022, found by walking up the FFIEC NIC relationships file (specs_tried.md #13). A bank controlled by another insured bank is left out of the sums, because its parent bank's consolidated call report already includes it (#15). Call report fields are summed across each entity's banks.

**Match rate: 337 of 343 entities (98%).** Our first rule used only each bank's top-tier holder (`RSSDHCR`) and matched 327. It missed **10 real banks** (Hilltop, Amalgamated, First Guaranty, Greene County, Lake Shore, TFS, Kentucky First, Broadway, South Plains, Sterling) whose top-tier holder is an unlisted parent above the listed company, such as a mutual holding company. The NIC walk matches all 10 (instructor audit A4). The 6 still unmatched are non-banks that own a thrift (AIG, MetLife, T. Rowe Price, Franklin, SEI, Impac), flagged `has_fdic = False`. Step 4 prints both match rates on every run.

### Data provenance
| Input | Source | How we get it again | Pulled |
|---|---|---|---|
| Sample universe (bank ↔ CRSP link) | NY Fed CRSP–FRB link, Sep 30, 2024 vintage ([page](https://www.newyorkfed.org/research/banking_research/crsp-frb)) | `code/00_build_universe.py` | See `data/provenance_log.csv` |
| Call report fields, Q4 2022 and Q3 2026 (for today's screen), all banks | FDIC BankFind API, `https://api.fdic.gov/banks/financials` ([field definitions](https://api.fdic.gov/banks/docs/risview_properties.yaml)) | `code/01_download_fdic.py` | See `data/provenance_log.csv` (logs the API's data vintage too) |
| Bank IDs (CERT → RSSD) | FDIC BankFind API, `https://api.fdic.gov/banks/institutions` | `code/01_download_fdic.py` | See `data/provenance_log.csv` |
| 2023 bank failures | FDIC BankFind API, `https://api.fdic.gov/banks/failures` | `code/01_download_fdic.py` | See `data/provenance_log.csv` |
| CRSP daily returns, delistings, market return | Pulled by Prof. Bowen from WRDS (legacy CRSP daily: `dsf`, `dsenames`, `dsedelist`, `dsi`) on 2026-11-06, at our request: the 343 PERMCOs in `requests/crsp_permcos.csv`, Jan 2022–Dec 2023; variables RET, RETX, DLRET/DLSTCD (delisting), PRC, SHROUT, VOL, TICKER, COMNAM, SHRCD, EXCHCD, and VWRETD (market) | With WRDS access, run [`code/wrds/pull_crsp.do`](code/wrds/pull_crsp.do) (the Stata script used for the pull) next to `requests/crsp_permcos.csv` | Received Nov 10, 2026 |
| KRE daily prices (regional-bank index for `kre_beta`) | yfinance (adjusted closes), Jan 2022–Mar 2023 | **Committed** in `data/raw/kre_daily.csv` (sha256 in `code/config.py`). To re-download: `python code/02_download_prices.py --refresh-kre`, which will change `kre_beta` slightly | Downloaded Nov 18, 2026 (see `data/provenance_log.csv`) |
| Prices for 3 banks (cross-check only) | yfinance (adjusted closes) | `code/02_download_prices.py` | See `data/provenance_log.csv` |
| Each company's primary activity (NAICS), for R10 | FFIEC NIC Attributes- Active and Attributes- Closed files (CSV) | Manual (CAPTCHA), same page as the relationships file; save both ZIPs in `data/raw/nic/` | Downloaded Nov 18, 2026 (see `data/provenance_log.csv`) |
| Ownership links (who controls which bank, with dates) | FFIEC National Information Center (NIC), Relationships file (CSV) | Manual (CAPTCHA): on the [NIC data download page](https://www.ffiec.gov/npw/FinancialReport/DataDownload), click CSV → Relationships and save the ZIP in `data/raw/nic/` | Downloaded Nov 17, 2026 (see `data/provenance_log.csv`) |
| Q4 2022 FFIEC comparison file | FFIEC CDR Bulk Data, Call Reports -- Single Period | On the CDR page, select Call Reports -- Single Period, report date 12/31/2022, and Tab Delimited. Download the ZIP and save as `data/raw/ffiec_call_20221231.zip`. | Downloaded Nov 10, 2026 |

`data/raw/` (except `kre_daily.csv`, above) and `data/interim/` are git-ignored. The scripts recreate them, except the CRSP files (licensed, from Prof. Bowen) and the two manual FFIEC downloads (NIC relationships, and the optional CDR comparison file). **Licensing:** we publish only results computed from CRSP (BHARs, CARs, betas, regressions), never CRSP rows (daily returns, prices, shares outstanding). That includes anything the dashboard loads.

### FDIC API vs. FFIEC check

For four banks, all 24 comparisons of total assets, uninsured deposits, and the four securities fields matched exactly between the FDIC API and the FFIEC CDR Q4 2022 bulk snapshot. Amounts are in $ thousands.

| Bank | Fields compared | Exact matches |
|---|---|---:|
| First Republic (FRC) | ASSET, DEPUNINS, SCHA, SCHF, SCAA, SCAF | 6 / 6 |
| Silicon Valley Bank (SIVB) | ASSET, DEPUNINS, SCHA, SCHF, SCAA, SCAF | 6 / 6 |
| Western Alliance (WAL) | ASSET, DEPUNINS, SCHA, SCHF, SCAA, SCAF | 6 / 6 |
| Zions (ZION) | ASSET, DEPUNINS, SCHA, SCHF, SCAA, SCAF | 6 / 6 |

The detailed bank-by-bank values are in [`outputs/ffiec_fdic_comparison.md`](outputs/ffiec_fdic_comparison.md). `code/06_hand_checks.py` reruns this comparison when the local FFIEC ZIP is present. Without the ZIP, the check is recorded as **SKIPPED** and the committed comparison in `outputs/ffiec_fdic_comparison.md` is left unchanged.

### Variables
| Column | Definition |
|---|---|
| `uninsured_dep_share` | Uninsured domestic deposits / domestic deposits (`DEPUNINS / DEPDOM`, FDIC fields in $ thousands, summed across the entity's banks). For the ~50 banks without `DEPUNINS`: amount in accounts over $250K − $250K × number of those accounts |
| `htm_loss_to_equity` | `(SCHA − SCHF) / EQTOT`: held-to-maturity loss not yet in book equity |
| `sec_loss_to_equity` | `((SCHA − SCHF) + (SCAA − SCAF)) / EQTOT`: all securities losses |
| `oci_2022_to_equity` | `EQCCOMPI / EQTOT`: 2022 other comprehensive income flow / equity (after tax); not accumulated AOCI and not a securities-only loss measure. Not used in the regressions |
| `htm_share_of_securities` | `SCHA / (SCHA + SCAF)` |
| `log_assets` | log of total assets (`ASSET`) |
| `bhr_0_2` | Buy-and-hold return over trading days 0 to +2 (Mar 9, 10, 13, 2023), including the delisting return on the delisting date |
| `bhar_0_2` | **Main outcome.** `bhr_0_2` minus the CRSP value-weighted market's buy-and-hold return over the same days (−3.84%) |
| `bhar_0_1` | The same BHAR over Mar 9–10 only (days 0 to +1), before the Mar 12 rescue. Outcome of R7; `bhr_0_1` is the raw buy-and-hold return |
| `car_0_2` | Sum of market-model abnormal returns over the same days; beta from CRSP VW market, trading days −250 to −30 |
| `kre_beta` | Slope of the bank's daily return on KRE's daily return (SPDR S&P Regional Banking ETF), trading days −250 to −30, at least 150 days. Control for the common regional-bank shock in R5 |
| `in_sample` | Matched to FDIC, has event returns, and positive equity (333 entities) |
| `bank_eq_to_mcap` | Bank subsidiaries' total equity (`EQTOT`) / the company's market value on Dec 30, 2022 (CRSP price × shares) |
| `nic_primary_activity` | The company's primary activity code (NAICS) in the FFIEC NIC attributes file |
| `bank_centric` | `main_sample`, without companies whose `bank_eq_to_mcap` is under 0.20 or whose `nic_primary_activity` isn't banking (5221xx, 551111, 551112). The sample for R10 (`specs_tried.md` #20) |
| `main_sample` | `in_sample` without SVB, the bank whose collapse is the event itself (332 entities). The main regressions run on this (`specs_tried.md` #17) |

### Threats to validity
1. **Failed banks and the main sample.** SVB and Signature stop trading on Mar 10 with no CRSP delisting return. We set it to −100% (shareholders of a bank in FDIC receivership are wiped out), which makes their BHAR about −96%. **SVB is left out of the main sample** because its collapse is the event, not a response to it; Signature stays in as a bank that the run spread to (`specs_tried.md` #17, instructor audit A2). The estimate depends on these two banks: the uninsured-share coefficient is −0.149 with SVB (R6), −0.112 without it (R1, main), and −0.065 without Signature too (R3). All three are reported here and on the dashboard. We chose the main sample after seeing the audit's leave-out table, and say so in `specs_tried.md`.
2. **Look-ahead in the data vintage:** the FDIC API serves the current version of Q4 2022 data, which may include amendments filed after March 2023. All 24 fields checked for FRC, SIVB, WAL, and ZION matched the current FFIEC CDR Q4 2022 bulk snapshot exactly. The CDR bulk file is also a current snapshot, so this checks cross-source consistency rather than recovering original filing vintages.
3. **Loss measure:** `EQCCOMPI` is an annual OCI flow, not accumulated AOCI; the diagnostic column is now `oci_2022_to_equity`. See [Morgan’s reconciliation](docs/zions_measurement.md). Losses on securities moved from AFS to HTM sit in equity (AOCI), not in the HTM gap (Zions shows a negative HTM loss). Securities-only measures also ignore losses on loans.
4. **Custody banks:** State Street (101%), BNY Mellon (93%), and Citi (82%) have very high uninsured shares, but most of those deposits are operational accounts for institutional clients, which behave differently from a startup's payroll account. One ratio is slightly above 1 because the FDIC's uninsured estimate and domestic deposits are measured differently.
5. **Outliers in ratios:** `sec_loss_to_equity` has a median of 0.21 but a maximum of 29.1 (First American), and 8 in-sample entities are above 1. R8 and R9 winsorize the ratios at the 1st/99th percentiles (`specs_tried.md` #19): the uninsured-share coefficient doesn't change (−0.113, p = 0.037). Step 4 prints these on every run.
6. **Entities without FDIC data:** 6 of 343 don't match, all non-banks that own a thrift. The 10 real banks our first link rule dropped are now matched through the NIC ownership file (see "Linking banks" above).
7. **Small, illiquid banks** have noisy returns; 2,247 CRSP rows use a bid/ask midpoint instead of a closing price.
8. **Bank-level measures, company-level returns.** Our measures come from the call reports of each entity's *bank subsidiaries*, but the outcome is the stock return of the *whole listed company*. For firms where the bank is a small part of the business (Schwab, Ameriprise, First American, Goldman Sachs, Morgan Stanley, AmEx, Raymond James, Stifel, Synchrony, Discover, Ally, SoFi, LendingClub), the ratio does not describe what the stock is pricing. **R10 checks this** (`specs_tried.md` #20): it drops companies whose banks' equity is under 20% of their market value, or whose primary activity the regulator codes as non-banking (First American, Ameriprise, Schwab, Amex, Raymond James, Goldman Sachs, Morgan Stanley, Ally). The uninsured-share coefficient is −0.130 (p = 0.025) on the remaining 324.
9. **The window includes the rescue.** Day +2 (Mar 13) comes after the Sunday, Mar 12 announcement that all SVB and Signature depositors would be protected and that banks could borrow against their bonds at par (BTFP). That policy targets both of our explanatory variables, so the three-day return measures the panic *net of* the rescue. **R7 checks this** with a window that stops on Fri, Mar 10 (`specs_tried.md` #18): the uninsured-share coefficient falls to −0.053 and isn't significant (p = 0.35). The sorting on uninsured deposits shows up on Monday, Mar 13, after the rescue, so our main result describes Monday's contagion more than the first two days' reaction to SVB.
10. **Standard errors.** All banks share the same three trading days, so their abnormal returns are correlated beyond the market (a regional-bank factor). HC3 standard errors do not correct for that, so our p-values are probably too small. R5 adds each bank's pre-event beta to KRE (a regional-bank ETF) as a control for that common factor; the uninsured-share coefficient barely moves (see `outputs/regressions.md`). This reduces the problem but doesn't remove it.
11. **Pre-tax losses vs. after-tax equity.** HTM losses are pre-tax while `EQTOT` is after-tax, and in `sec_loss_to_equity` the AFS losses have already reduced `EQTOT` through AOCI.

## Project history

How we picked this project (three candidate ideas, Oct 15) and the first proof of concept (Oct 23) are in [`docs/checkpoint0_candidates.md`](docs/checkpoint0_candidates.md) and [`STATUS.md`](STATUS.md).

## Repo structure
```
README.md
STATUS.md            # Checkpoint 1 memo
specs_tried.md       # every specification we run
run_all.py           # rebuilds everything from raw inputs
requirements.txt
code/                # config.py, 00_build_universe ... 09_screen_today (see Pipeline); wrds/pull_crsp.do (the CRSP pull)
requests/            # the PERMCO list we sent for the CRSP pull
data/raw/            # git-ignored; recreated by the download code, except crsp/ (licensed) and nic/ (manual FFIEC downloads)
data/interim/        # git-ignored; row-level CRSP event-day returns
data/processed/
data/provenance_log.csv
outputs/             # every table/figure in the slides and dashboard
audits/              # self-audits, the instructor's audit, and our response
docs/                # Zions note, Checkpoint 0 history, dashboard screenshots
inputs/              # hand-transcribed Zions 10-K figures, with sources
app/                 # dashboard (GitHub Pages)
```
