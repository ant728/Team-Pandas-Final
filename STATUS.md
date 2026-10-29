# Status memo: Checkpoint 1 (pick + proof of concept)

**What we picked, and why.** We picked Seed 6: *When Silicon Valley Bank failed in March 2023, did banks that relied more on uninsured deposits and had larger hidden losses on their bonds fall more, and which listed banks look like that today?* It beat post-earnings drift (Seed 2) and the bitcoin ETF approval (Seed 14) because the question matters to a clear buyer (regulators and bank investors). The same measures also power a forward-looking "who's next" screen, which is more useful than a backward-looking chart. It was the riskiest idea on data, so we tested the data first.

**Our proof of concept.** `python run_all.py` builds real rows for 6 banks (JPM, WAL, ZION, First Republic, SVB, Comerica) in [`outputs/poc_final_rows.csv`](outputs/poc_final_rows.csv). Call report fields come from the FDIC BankFind API (Q4 2022, the last quarter public before the event, rolled up to the holding company using the ownership on that date). Returns come from yfinance, with a market-model CAR over Mar 9–13, 2023. All five hand checks in [`outputs/hand_checks.md`](outputs/hand_checks.md) pass. Two of them match published SVB numbers: uninsured deposits are 93.9% of domestic deposits (the Fed's review says about 94%), and the HTM unrealized loss is $15.2B (the 10-K says $15.1B). What broke or worried us:
- **SVB and Comerica have no prices in yfinance.** SVB failed. Comerica's ticker disappeared after its 2026 merger. So the banks that fell hardest drop out, and survivors who were later acquired drop out too.
- **The ticker link is hand-made** for now (`inputs/bank_crosswalk.csv`). The NY Fed link maps to CRSP PERMCOs, not tickers.
- **Our loss measure is fragile.** "HTM loss / equity" is 0 for Comerica, because it held only AFS securities, and negative for Zions. Zions moved securities from AFS to HTM at already-marked-down values, so the loss sits in equity, not in the HTM gap.
- **Summed CARs overstate crashes this large.** WAL's CAR is −76%, but its actual drop was −64%. We'll probably use buy-and-hold returns.
- The FDIC API serves today's version of the 2022 data (vintage Aug 2026), which could include amendments filed after March 2023.

**Our questions for you.**
1. Can we use WRDS/CRSP through Lehigh? It would give us returns for delisted banks (SVB, Signature, PacWest, Comerica) and a tested RSSD → PERMCO → ticker link. If not, is there a free source you'd trust?
2. Is a securities-only loss measure enough, or should we follow Jiang, Matvos, Piskorski & Seru and mark the whole loan book to market? And how should we treat AFS → HTM transfers?
3. Is the FDIC API vintage acceptable, or should we use the FFIEC bulk files as originally filed?
4. Scope: one event (Mar 9–13), or also Signature (Mar 12) and First Republic (May 1) as separate events?
