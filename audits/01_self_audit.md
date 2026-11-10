# Checkpoint 2 self-audit — dashboard contribution

**Scope:** Mason Friedman’s dashboard and the six-bank inputs in the
November 10 checkpoint workspace. This records the dashboard checks;
the team’s skeptical review and integrated pipeline sign-off are still open.

| Check | Finding and response |
|---|---|
| Reproducibility | Served `app/` with Python’s local HTTP server and loaded Intro, Method, March 2023 Results, and Who’s Next in a browser. No package install or API request is needed by the dashboard. It reads two named CSVs under `outputs/`. |
| Missing returns | The original output has four usable CARs. The optional CRSP preview has five: Comerica now has a complete event window. SVB is absent from both plots and stays in the balance-sheet table. In the CRSP archive, SVB has no reported March 10 delisting return or usable March 13 return. No return was imputed. |
| Chart definitions | X uses uninsured domestic deposits / domestic deposits. Y uses summed market-model CAR on March 9, 10, and 13. Size uses assets in billions of dollars, and color uses the preliminary HTM + AFS loss / equity ratio. The source selector changes the stated benchmark along with the observations. Clicking a dot or selecting a bank shows the source values. |
| Numeric sorting | The six-bank table defaults to highest uninsured share (SVB, 93.88%). Sorting HTM loss / equity ascending puts Zions (−2.31%) ahead of Comerica (0%). Searching for Zions narrows the results to one row. |
| CRSP preview | The generator matched four issuers using RSSD and confirmed two direct banks by issuer name and unique dated tickers. An independent OLS calculation reproduced the five CARs. The app receives only bank-level outputs. The raw ZIP and daily records stay outside the repository and browser. |
| Interpretation | Who’s Next shows December 2022 reports, without a failure flag or a current-quarter ranking. The four- and five-point scatters describe coverage and associations; they are not a regression or a validation test. |

**For the integrated checkpoint:** After the team refreshes the sample,
recheck that the dashboard labels reflect the adopted return and loss
measures, confirm both CSVs use the same balance-sheet snapshot, and rerun
the app. The full team review still needs the rebuilt small-sample pipeline,
return and regression checks, Zions treatment, the FDIC/FFIEC comparison,
and the dated test plan. Do not treat the optional CRSP preview as the
team’s formal delisting specification.
