# FDIC API vs. FFIEC CDR comparison

Q4 2022 (report date 2022-12-31), current FFIEC CDR bulk snapshot downloaded 2026-11-10.
Amounts are $ thousands. For consolidated reporters the comparison uses RCFD values where available, otherwise RCON; uninsured deposits use RCON5597.
FFIEC banks are matched to the FDIC API entity using the FDIC certificate numbers in the input crosswalk.

Across 4 listed entities (4 bank filings), all 24 Q4 2022 field comparisons matched exactly.

| Entity | Field | FDIC API | FFIEC CDR | Difference | Result | CERT(s) |
|---|---|---:|---:|---:|---|---|
| FRC | ASSET | 212,638,872 | 212,638,872 | 0 | PASS | 59017 |
| FRC | DEPUNINS | 119,470,758 | 119,470,758 | 0 | PASS | 59017 |
| FRC | SCHA | 28,358,907 | 28,358,907 | 0 | PASS | 59017 |
| FRC | SCHF | 23,587,503 | 23,587,503 | 0 | PASS | 59017 |
| FRC | SCAA | 3,816,695 | 3,816,695 | 0 | PASS | 59017 |
| FRC | SCAF | 3,346,697 | 3,346,697 | 0 | PASS | 59017 |
| SIVB | ASSET | 209,026,000 | 209,026,000 | 0 | PASS | 24735 |
| SIVB | DEPUNINS | 151,592,000 | 151,592,000 | 0 | PASS | 24735 |
| SIVB | SCHA | 91,327,000 | 91,327,000 | 0 | PASS | 24735 |
| SIVB | SCHF | 76,168,000 | 76,168,000 | 0 | PASS | 24735 |
| SIVB | SCAA | 28,502,000 | 28,502,000 | 0 | PASS | 24735 |
| SIVB | SCAF | 25,976,000 | 25,976,000 | 0 | PASS | 24735 |
| WAL | ASSET | 67,683,841 | 67,683,841 | 0 | PASS | 57512 |
| WAL | DEPUNINS | 29,672,465 | 29,672,465 | 0 | PASS | 57512 |
| WAL | SCHA | 1,288,862 | 1,288,862 | 0 | PASS | 57512 |
| WAL | SCHF | 1,112,137 | 1,112,137 | 0 | PASS | 57512 |
| WAL | SCAA | 7,972,852 | 7,972,852 | 0 | PASS | 57512 |
| WAL | SCAF | 7,092,360 | 7,092,360 | 0 | PASS | 57512 |
| ZION | ASSET | 89,544,919 | 89,544,919 | 0 | PASS | 2270 |
| ZION | DEPUNINS | 35,891,556 | 35,891,556 | 0 | PASS | 2270 |
| ZION | SCHA | 11,125,459 | 11,125,459 | 0 | PASS | 2270 |
| ZION | SCHF | 11,238,585 | 11,238,585 | 0 | PASS | 2270 |
| ZION | SCAA | 13,538,167 | 13,538,167 | 0 | PASS | 2270 |
| ZION | SCAF | 11,914,977 | 11,914,977 | 0 | PASS | 2270 |

Field mapping: `ASSET` = RCFD2170/RCON2170; `DEPUNINS` = RCON5597; `SCHA` = RCFD1754/RCON1754; `SCHF` = RCFD1771/RCON1771; `SCAA` = RCFD1772/RCON1772; `SCAF` = RCFD1773/RCON1773.
