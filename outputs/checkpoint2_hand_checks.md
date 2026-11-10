# Hand checks

Generated from local raw inputs by `04_hand_checks.py`. Scenario checks validate arithmetic, not recovery assumptions.

| Check | Pipeline | Independent | Tolerance | Result | Evidence |
|---|---:|---:|---:|---|---|
| SVB uninsured domestic share | 0.9388 | 0.9400 | 0.01 | PASS | Fed SVB review: approximately 94%; https://www.federalreserve.gov/publications/2023-April-SVB-Key-Takeaways.htm |
| SVB HTM loss ($B) | 15.1590 | 15.1000 | 0.3 | PASS | Original project hand check against SVB 2022 10-K; subsidiary aggregation differs from parent |
| JPM asset aggregation ($B) | 3202.0049 | 3202.0049 | 0.001 | PASS | Plain csv loop over raw FDIC subsidiary records |
| WAL compounded return | -0.6350 | -0.6350 | 0.0001 | PASS | Independent CRSP scalar product over exactly three trading dates |
| WAL market-adjusted BHAR | -0.5966 | -0.5966 | 0.0001 | PASS | Independent stock gross return minus CRSP market gross return |
| SIVB zero-recovery scenario | -0.9616 | -0.9616 | 0.0001 | PASS | Assumption only: terminal stock value zero; not an observed CRSP return |
| SBNY zero-recovery scenario | -0.9616 | -0.9616 | 0.0001 | PASS | Assumption only: terminal stock value zero; not an observed CRSP return |
| Comerica return coverage | 1.0000 | 1.0000 | 0 | PASS | CRSP restores later-acquired bank coverage |
