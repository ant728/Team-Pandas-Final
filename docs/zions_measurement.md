# Zions: where the transferred loss sits

Owner: Morgan Waddell. Checkpoint 2, November 14, 2026.

The loss did not vanish: an AFS-to-HTM transfer resets the carrying basis while the earlier loss remains in AOCI and is amortized. Call-report Schedule RC item 26.b (B530) holds aggregate AOCI, net of tax; the securities footnote is needed to isolate transfers.

| 2022 year-end disclosure | $ million | Source location |
|---|---:|---|
| HTM amortized cost / fair value | 11,126 / 11,239 | 10-K Note 5, p95 |
| AFS amortized cost / fair value | 13,538 / 11,915 | Note 5, p95 |
| Transfer-related pretax loss, approximate | 2,400 | Note 5, p95, footnote 1 |
| Securities AOCI, after tax | -2,800 | Note 14 |
| Derivatives/other AOCI; pension AOCI | -311; -1 | Note 14 |
| Total AOCI, after tax | -3,112 | Note 14 |

**Choice:** measure total securities exposure as `(HTM gap + AFS gap + remaining pretax transferred loss) / equity`. It includes losses already reflected in equity; it is not an additional equity write-down. The Zions illustration uses the rounded transfer disclosure, not a verified unamortized year-end balance. Do not add total AOCI or gross it up with an assumed tax rate. Cross-bank transfer balances remain to be collected; the existing dashboard baseline is explicitly provisional.

Sources: [Zions 2022 10-K, filed February 23, 2023](https://www.sec.gov/Archives/edgar/data/109380/000010938023000074/zions-20221231.htm); [FFIEC instructions, Schedule RC item 26.b](https://www.ffiec.gov/sites/default/files/data/reporting-forms/ffiec031-ffiec041-call-report-preparation-intructions.pdf). Definitions are reference guidance; historical measurements use pre-event disclosures.

## Reproduction and limits

`inputs/zions_disclosures.csv` records manually transcribed public figures, units, public date, and exact locations. `code/07_zions_reconciliation.py` reads the official raw FDIC report, checks component arithmetic and rounded cost/fair-value agreement, then writes `outputs/zions_reconciliation.csv` and `outputs/zions_measure_comparison.csv`. These are sourced inputs, never invented observations. Verify the transcription against the linked report when reviewing the PR.

**Correction to the handoff:** FDIC labels `EQCCOMPI` as OTHER COMPREHENSIVE INCOME, not accumulated AOCI. Its Zions value is -$3,032.035 million, matching the annual OCI flow (rounded -$3,032 million), rather than the closing -$3,112 million balance. Do not use that field as accumulated losses. See the [FDIC dictionary](https://api.fdic.gov/banks/docs/risview_properties.yaml).

This is not the team's separate 3–5-bank FFIEC bulk-file comparison. A tax benefit on an annual OCI flow is not the tax adjustment for an accumulated balance. The approximate diagnostic is not used in the regression or a cross-bank adjusted ranking. The rounded transfer disclosure needs a precise remaining-balance check before full-sample application.

The official `python run_all.py` runs this diagnostic after the team’s hand checks. Its two tables do not change `bhar_0_2`, the zero-recovery policy in specification #5, or the regression sample. The official dataset column `oci_2022_to_equity` replaces the misleading `aoci_to_equity` name without changing its values.


## How to explain Step 07

1. Read the small disclosure CSV and the official FDIC download. CERT 2270 selects Zions, so no ticker matching or new sample is needed.
2. Convert FDIC amounts from thousands to millions before comparing them with the rounded annual-report figures. Differences within one million dollars are allowed for rounding; larger differences stop the pipeline.
3. Add the securities, derivatives/other and pension AOCI components and verify that they equal total AOCI. Separately compare the annual OCI flow with EQCCOMPI; a flow is not an accumulated balance.
4. Calculate the HTM-only ratio, the combined HTM/AFS ratio and an approximate transfer-aware ratio, all using the same official FDIC equity denominator. The transfer disclosure is approximate, so the final ratio is labeled a diagnostic.
5. Write the two public output tables. This step does not modify the final dataset, the failed-bank policy or any regression.
