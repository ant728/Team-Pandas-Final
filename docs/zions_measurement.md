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

`inputs/zions_disclosures.csv` records manually transcribed public figures, units, public date, and exact locations. `05_checkpoint_outputs.py` checks component arithmetic and rounded cost/fair-value agreement with FDIC, then writes `outputs/zions_reconciliation.csv` and `outputs/zions_measure_comparison.csv`. These are sourced inputs, never invented observations. Verify the transcription against the linked report when reviewing the PR.

**Correction to the handoff:** FDIC labels `EQCCOMPI` as OTHER COMPREHENSIVE INCOME, not accumulated AOCI. Its Zions value is -$3,032.035 million, matching the annual OCI flow (rounded -$3,032 million), rather than the closing -$3,112 million balance. Do not use that field as accumulated losses. See the [FDIC dictionary](https://api.fdic.gov/banks/docs/risview_properties.yaml).

This is not the team's separate 3–5-bank FFIEC bulk-file comparison. A tax benefit on an annual OCI flow is not the tax adjustment for an accumulated balance. The approximate diagnostic is not used in the regression or a cross-bank adjusted ranking. The rounded transfer disclosure needs a precise remaining-balance check before full-sample application.
