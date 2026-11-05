Thanks, this is really helpful. Here's exactly what we need from CRSP.

**Which firms:** the 343 PERMCOs in [`requests/crsp_permcos.csv`](requests/crsp_permcos.csv). That's every entity in the NY Fed CRSP–FRB link (Sep 2024 vintage) whose link was active on Dec 31, 2022, our call report date. It includes the banks that later failed or merged (SVB 9588, Signature 44999, First Republic 53609, PacWest 37718, Comerica 1261), so they stay in the sample. `code/00_build_universe.py` rebuilds the list.

**Dates:** Jan 1, 2022 – Dec 31, 2023. That covers our market-model estimation window (about 250 trading days before Mar 9, 2023), the event, and the rest of 2023 for the out-of-sample "who's next" test you suggested (PacWest's link ends Nov 30, 2023).

**Variables (daily stock file, all share classes for each PERMCO):**
- PERMNO, PERMCO, date
- RET, RETX, PRC, SHROUT, VOL
- Delisting return and code (DLRET, DLSTCD, DLSTDT), or the CIZ-format daily return that already includes delisting
- From the names file: TICKER, COMNAM, SHRCD, EXCHCD (so we can keep common shares, and get tickers for the dashboard)
- Market: CRSP value-weighted return (VWRETD) for the same dates

A CSV or parquet in whatever form is easiest for you works. We'll keep it out of the public repo (git-ignored) and document where it came from in the README.

On your other points: we'll stick to one event, compare a few banks against the FFIEC bulk files, and write up where Zions' missing loss shows up. (Early lead: it seems to sit in accumulated OCI, which is reported after tax.)
