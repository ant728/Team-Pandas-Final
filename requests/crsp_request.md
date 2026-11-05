# CRSP data request

Emailed to Prof. Bowen on Nov 5, 2026, after he offered in issue #4 to pull CRSP data for us. The attached PERMCO list is [`crsp_permcos.csv`](crsp_permcos.csv), built by `code/00_build_universe.py`. When the data arrives it goes in `data/raw/` (git-ignored: CRSP is licensed).

---

**Subject:** Team Pandas: CRSP data request for our bank fragility project

Hi Professor Bowen,

Thank you for the feedback on our status memo, and for offering to pull CRSP data for us. Here is exactly what we need.

Which firms: the 343 PERMCOs in the attached file (crsp_permcos.csv). That's every entity in the NY Fed CRSP-FRB link (Sep 2024 vintage) whose link was active on Dec 31, 2022, the date of the call reports we use. It includes the banks that later failed or merged, so they stay in our sample: SVB (9588), Signature (44999), First Republic (53609), PacWest (37718), and Comerica (1261). Our script code/00_build_universe.py rebuilds the list.

Dates: Jan 1, 2022 to Dec 31, 2023. That covers our market-model estimation window (about 250 trading days before Mar 9, 2023), the event itself, and the rest of 2023 for the out-of-sample "who's next" test you suggested.

Variables (daily stock file, all share classes for each PERMCO):
- PERMNO, PERMCO, date
- RET, RETX, PRC, SHROUT, VOL
- Delisting return and code (DLRET, DLSTCD, DLSTDT), or the CIZ-format daily return that already includes delisting
- From the names file: TICKER, COMNAM, SHRCD, EXCHCD, so we can keep common shares and show tickers on the dashboard
- The CRSP value-weighted market return (VWRETD) for the same dates

A CSV or parquet file in whatever form is easiest for you is great. We'll keep the CRSP data out of our public repo and document where it came from in the README.

On your other points: we'll stick to one event for now, compare a few banks against the FFIEC bulk files, and write up where Zions' missing loss shows up in the call report. Our early lead is accumulated other comprehensive income, which is reported after tax. We'll also build the out-of-sample test of whether a screen using only Dec 2022 data would have flagged First Republic and PacWest.

Thank you,
Andrew Temo
On behalf of Team Pandas (Andrew Temo, Mason Friedman, Morgan Waddell, Ryan Carr)
