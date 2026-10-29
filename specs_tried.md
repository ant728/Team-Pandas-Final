# Specifications tried

Every specification we run goes here, including the ones we drop. Count so far: **4 variants** on a 6-bank proof-of-concept sample (4 with returns). No hypothesis tests have been run yet, so nothing here is a result.

| # | Date | What | Sample | Outcome | Kept? |
|---|---|---|---|---|---|
| 1 | 2026-10-29 | CAR[0,+2], market model on SPY, estimation window [−250, −30], day 0 = Mar 9, 2023 | JPM, WAL, ZION, FRC | WAL −76%, FRC −89%, ZION −36%, JPM −2% | Baseline for now |
| 2 | 2026-10-29 | Same window, market-adjusted (stock − SPY, no beta) | same | Within 1.3 pp of #1 for all four | Robustness column |
| 3 | 2026-10-29 | Buy-and-hold return, Mar 8 close → Mar 13 close (raw, not abnormal) | same | WAL −64%, FRC −73%, ZION −36%, JPM −5% | **Likely switch to BHAR.** Summing daily returns overstates crashes this large (WAL: −76% summed vs −64% compounded) |
| 4 | 2026-10-29 | Two loss measures: HTM loss / equity vs. (HTM + AFS loss) / equity | all 6 | They rank banks very differently: Comerica is 0 on the first, 0.62 on the second; Zions is negative on the first | Undecided. See STATUS.md |

## Choices fixed before looking at returns
- Call report quarter: Q4 2022 (due Jan 30, 2023, public before the event).
- Day 0: Mar 9, 2023 (SVB's announcement came after the close on Mar 8).
- Uninsured share denominator: domestic deposits (the uninsured estimate only covers domestic offices).
