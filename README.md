# FIN 331 Final Project: [Team Name]

**Team:** [Name 1], [Name 2], [Name 3], [Name 4]

**Status:** Checkpoint 0, candidate ideas (Thu Oct 15, 2026)

We're considering three ideas, all from `00_PROJECT_SEEDS`:

| # | Idea | Seed | Main tools from class |
|---|---|---|---|
| A | Post-earnings drift in 2026: is there still money on the table? | #2 | Event study (HW6), factor alphas |
| B | Bank fragility: SVB, and who's next | #6 | Event study, cross-sectional regression, call reports |
| C | The spot bitcoin ETF approval: who won? | #14 | Event study with long pre-event windows |

For each idea below we "read it backwards" (Lecture 16, Question 3a): the question, one row of the final dataset, the raw inputs, a chart sketch, and the first thing an auditor would attack. Under each idea, **Quick data check** records what we actually pulled on Oct 15. All rows in the tables are **fake**. They're there to show the shape of the data.

---

## Idea A: Post-earnings drift (Seed 2)

### 1. The question
After a company beats or misses earnings by a lot, does its stock keep moving in the same direction for weeks, and is that move big enough to profit from after trading costs?

### 2. One row of the final dataset
**One row = one firm × one earnings announcement.** Key: (`ticker`, `ann_date`), unique.

| ticker | ann_date | ann_time | day0 | eps_est | eps_actual | surprise_pct | surprise_q | mktcap_pre ($B) | car_m1_p1 | car_p2_p60 |
|---|---|---|---|---|---|---|---|---|---|---|
| AAPL | 2025-07-31 | AMC | 2025-08-01 | 1.43 | 1.57 | 9.8 | 5 | 3,150 | 0.021 | 0.034 |
| TGT | 2025-05-21 | BMO | 2025-05-21 | 1.65 | 1.30 | -21.2 | 1 | 46 | -0.052 | -0.061 |
| KO | 2025-04-29 | BMO | 2025-04-29 | 0.71 | 0.73 | 2.8 | 3 | 305 | 0.004 | -0.008 |

- `ann_time`: BMO = before market open, AMC = after market close. `day0` is the first trading day the news could be traded on (the next day for AMC).
- `surprise_q`: surprise quintile, built **only from announcements before that date** (no look-ahead in the cutoffs).
- `car_p2_p60`: market- or factor-adjusted return from day +2 to day +60 (the drift we'd trade).

From this table we build a second one: **one row = portfolio × day** (long top quintile, short bottom quintile, formed on day +2), for the long-short returns and factor alphas.

### 3. Raw inputs, and do we know we can get them?

| Input | Source | Do we know we can get it? |
|---|---|---|
| Earnings dates, EPS estimate, actual, surprise % | `yf.Ticker(t).get_earnings_dates(limit=…)` | **Yes**, pulled for AAPL (see below) |
| Daily stock returns | `yfinance` | **Yes** |
| Fama-French daily factors | Ken French's data library (zip) | **Yes**, URL returns 200 |
| Historical S&P 500 membership (to avoid survivorship) | Wikipedia's "changes" table, or a GitHub dataset of historical constituents | **Not yet checked.** This is our biggest data question |
| Market cap before the announcement | price × shares outstanding | **Partly.** yfinance gives *today's* shares; historical shares need XBRL `companyfacts` |
| Analyst coverage (number of analysts) | yfinance `info` | **Only today's value.** Using it for past years would be look-ahead. Might drop it. |

### 4. Chart / dashboard sketch
Main chart: average cumulative abnormal return by surprise quintile, from day −5 to day +60. Sliders for holding period and round-trip trading cost; a box shows the long-short return after costs.

```
 CAR
  +4% |                              ____________ Q5 (big beats)
      |                    _________/
  +2% |          _________/
      |    _____/        ......................... Q3
   0% |___/..............
      |   \_____
  -2% |         \_________
      |                   \__________________ Q1 (big misses)
  -4% |
      +----+----+----+----+----+----+----+----+--
         -5   0   +5  +10       +30          +60   event day
      [holding period: 2 ──●────── 60]  [cost: 0 ─●── 50 bps]
      Long-short after costs: 1.1% (t = 2.3)
```

### 5. The first thing an auditor would attack
**Survivorship.** If we take *today's* S&P 500 list and go back to 2020, we only include firms that survived and grew into the index. Those are winners, which biases the drift. Fix: use point-in-time index membership. Close behind: the day-0 rule for after-close announcements, overlapping 60-day windows inflating t-stats (use calendar-time portfolios), and whether the drift survives costs.

### Quick data check (Oct 15)
- `get_earnings_dates(limit=30)` for AAPL returned 50 rows back to **July 2014**, with EPS estimate, reported EPS, surprise %, and a **timestamp** (16:00 ET = after close). So the day-0 rule can be built from the data, not guessed.
- Still to check: does the history go back that far for smaller firms? Does yfinance rate-limit us at 500 tickers? Is there a free point-in-time S&P 500 membership list?

---

## Idea B: Bank fragility, SVB and who's next (Seed 6)

### 1. The question
When Silicon Valley Bank failed in March 2023, did banks that depended more on uninsured deposits and had larger hidden losses on their bond portfolios fall more, and which banks look like that today?

### 2. One row of the final dataset
**One row = one listed bank (holding company)**, measured with the call report for the quarter **before** the event (Dec 31, 2022). Key: `rssd_id`, unique.

| rssd_id | ticker | bank_name | total_assets ($B) | uninsured_dep_share | unrealized_loss_to_equity | htm_share_of_securities | car_mar9_mar13 |
|---|---|---|---|---|---|---|---|
| 1234567 | WAL | Western Alliance | 67.7 | 0.55 | 0.18 | 0.12 | -0.58 |
| 2345678 | JPM | JPMorgan Chase | 3,666 | 0.48 | 0.14 | 0.55 | 0.01 |
| 3456789 | ABCB | Ameris Bancorp | 25.1 | 0.30 | 0.09 | 0.20 | -0.12 |

- `uninsured_dep_share` = estimated uninsured deposits / total deposits (call report Schedule RC-O, item RCON5597, reported by banks over $1B; to verify).
- `unrealized_loss_to_equity` = (amortized cost − fair value) of held-to-maturity + available-for-sale securities / equity (Schedule RC-B; to verify).
- The dashboard's "who's next" screen is the same row, rebuilt with the **latest** call report and no CAR.

### 3. Raw inputs, and do we know we can get them?

| Input | Source | Do we know we can get it? |
|---|---|---|
| Call reports (balance sheet, deposits, securities) | FFIEC CDR bulk download | **Page is reachable** (HTTP 200). Haven't downloaded a quarter yet |
| Bank ID → stock link | NY Fed CRSP–FRB link | **Page is reachable**, but it maps RSSD → CRSP **PERMCO**, not ticker. Need a PERMCO → ticker step (WRDS, if Lehigh has it) or a hand match for ~100 banks |
| Holding company ↔ subsidiary bank structure | FFIEC NIC (National Information Center) | **Not yet checked.** Call reports are filed by the *bank*, but the *holding company* is what trades |
| Daily returns | `yfinance` | **Partly.** Works for survivors; **fails for the failed banks** (see below) |
| Market factor | SPY / Ken French | **Yes** |

### 4. Chart / dashboard sketch
Page 1: scatter of each bank's CAR around March 9–13, 2023 against its uninsured deposit share, dot size = assets, color = unrealized losses. Page 2: "fragility screen", a sortable table of today's listed banks on the same two measures, with the 2023 fitted line showing their predicted drop.

```
 CAR (Mar 9-13, 2023)
   0% |  o  o   O    o
      |    o  o    o   o
 -20% |        o  o  O    o
      |              o   O  o           (dot size = assets,
 -40% |                    o   o         red = big unrealized losses)
      |                         ●
 -60% |                            ●  WAL
      +----+----+----+----+----+----+----+--
         10%  20%  30%  40%  50%  60%  70%   uninsured deposit share
```

### 5. The first thing an auditor would attack
**Survivorship from the delisted banks.** The banks hit hardest (SVB, Signature, First Republic, PacWest) are exactly the ones that vanished from yfinance. If they quietly drop out, the regression understates the effect. We'd need another source for their returns, or disclose it clearly. Close behind: using the call report from **before** the event (Q4 2022, not Q1 2023), the quality of the bank → holding company → ticker link, and noisy returns for small, thinly traded banks.

### Quick data check (Oct 15)
- yfinance has data for survivors: from the Mar 8 to Mar 13, 2023 close, KRE (regional bank ETF) fell about 23% and Western Alliance (WAL) about 64%.
- **SIVBQ (SVB), SBNY (Signature), and PACW (PacWest) returned no prices for March 2023.** FRCB (First Republic) did. This confirms the survivorship problem is real, not hypothetical.
- Still to check: download one quarter of call reports and find the uninsured-deposit and securities fields; see how many listed holding companies the NY Fed link covers.

---

## Idea C: The spot bitcoin ETF approval (Seed 14)

### 1. The question
When the SEC approved spot bitcoin ETFs in January 2024, which stocks gained (bitcoin miners, Coinbase, MicroStrategy, or the fund companies launching the ETFs), and had the market already priced it in weeks earlier?

### 2. One row of the final dataset
**One row = one firm (or BTC) × one event day.** Key: (`ticker`, `date`), unique within an event.

| event | ticker | group | date | rel_day | ret | mkt_ret | ar | car_from_m20 |
|---|---|---|---|---|---|---|---|---|
| btc_etf | COIN | exchange | 2024-01-11 | 0 | -0.067 | 0.000 | -0.068 | 0.18 |
| btc_etf | MARA | miner | 2024-01-11 | 0 | -0.126 | 0.000 | -0.127 | 0.05 |
| btc_etf | BLK | etf_sponsor | 2024-01-11 | 0 | 0.004 | 0.000 | 0.003 | 0.02 |

- Approval came **after the close on Jan 10, 2024**, so stock day 0 is Jan 11.
- `group`: miner, exchange, BTC treasury (MSTR), ETF sponsor, control.
- A second event in the same table: the ETH ETF approvals (May 2024). Also flagged: the fake approval tweet from the SEC's hacked X account on Jan 9.

### 3. Raw inputs, and do we know we can get them?

| Input | Source | Do we know we can get it? |
|---|---|---|
| Stock prices (COIN, MSTR, MARA, RIOT, CLSK, BLK, IVZ, BEN, …) | `yfinance` | **Yes**, pulled (see below) |
| Bitcoin price | `yfinance` `BTC-USD` | **Yes**, but it trades 7 days a week, so it has to be aligned to trading days |
| Approval date and time | SEC press release / statement | **Yes**, page reachable |
| Fake-tweet timing (Jan 9) | SEC statement, news coverage | **Likely**, not yet pulled |
| ETF sponsors | Many are private (Fidelity, Grayscale, ARK, VanEck), so only some are tradable (BLK, IVZ, BEN, WT) | **Yes**, but this limits the sponsor group |

### 4. Chart / dashboard sketch
Main chart: cumulative abnormal return by group from 60 trading days before to 20 after the approval, with vertical lines for the key dates (BlackRock's filing in June 2023, the Grayscale court win in Aug 2023, the fake tweet, approval). A toggle switches to the ETH approval.

```
 CAR
 +80% |                                  /\     miners
      |                          ______/   \___
 +40% |                 ________/              \___ COIN
      |        ________/                 ......:..... MSTR
   0% |_______/____________________________|______ sponsors
      |                                    |   \
 -20% |                                    |    BTC
      +-----+-----+-----+-----+-----+-----+-----+--
          -60   -45   -30   -15    -5    0    +10   trading days
                                   tweet^ ^approval
      [event: (●) BTC ETF  ( ) ETH ETF]
```

### 5. The first thing an auditor would attack
**Anticipation.** The approval was widely expected for weeks, so a short window around Jan 10 will show "sell the news" rather than the value of the approval. Our results depend heavily on when we start the window, and we need to log every window we try in `specs_tried.md`. Close behind: aligning 24/7 bitcoin returns with trading-day stock returns, the fake tweet the day before as a confound, and a tiny sample (about 15 stocks, one main event), so the statistics will be weak.

### Quick data check (Oct 15)
- yfinance returned clean prices for BTC-USD, COIN, MSTR, MARA, RIOT, and SPY around the event.
- Raw returns from the Jan 10 close to the Jan 12 close: BTC about −8%, COIN about −14%, MARA about −26%, while SPY was flat. That's consistent with a "sell the news" reaction and shows why the pre-event window matters.

---

## Comparing the three

| | A: Earnings drift | B: Bank fragility | C: Bitcoin ETF |
|---|---|---|---|
| Sample size | Large (thousands of announcements) | Medium (~100–300 banks, one event) | Small (~15 stocks, 1–2 events) |
| Data risk | Low–medium (point-in-time S&P list) | **High** (ID links, delisted banks, call report fields) | Low |
| Biggest audit risk | Survivorship, overlapping windows | Survivorship of failed banks, timing of the call report | Anticipation, tiny N |
| Dashboard "wow" | Tradable-strategy slider | Live "who's next" screen | Event timeline |
| Who'd pay | Quant PM | Regulators, bank investors | Crypto-exposed equity investor |

**Our pick:** _[team to decide]_. **The data question we need answered first:** _[team to fill in]_.

---

## Proof of concept (Lecture 16, Question 4)
_For our favorite idea: one real row of the final dataset, from the actual source. What did we get, how long would the full dataset take, and what broke?_

[team to fill in]

## Repo structure (planned)
```
README.md
STATUS.md            # Checkpoint 1 memo (due Fri Oct 23)
specs_tried.md       # every specification we run
run_all.py           # rebuilds everything from raw inputs
code/                # 01_download, 02_clean, 03_build_dataset, 04_analysis
data/raw/            # git-ignored; recreated by the download code
data/processed/
outputs/             # every table/figure in the slides and dashboard
audits/              # self-audits (01_self_audit.md, …)
app/                 # dashboard
```

## Threats to validity
_Will be filled in once we pick an idea. The "first thing an auditor would attack" for each idea above is our starting list._
