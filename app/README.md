# Checkpoint 2 dashboard

View the [live dashboard](https://ant728.github.io/Team-Pandas-Final/app/).
The [HW8 page guide and screenshots](../docs/mason_hw8.md) document what to show in the proposal.

From the repository root, run:

```sh
python3 app/serve.py
```

Open <http://127.0.0.1:8765/app/>. No package install is needed to view the
committed results. The server binds to your own machine and serves only
the dashboard assets and the published CSV. Press Ctrl+C to stop it.

- **Intro** explains the question and shows the total and analysis sample counts.
- **Method** explains the December 2022 Call Reports and the March 2023 event.
- **March 2023 Results** plots only entities marked `in_sample` with both
  uninsured deposit share and buy-and-hold abnormal return (BHAR).
  Hover or select a point to see the original values. The bank selector also
  lets you inspect entities that are not on the plot.
- **Who's Next** is a sortable, searchable view of the historical balance
  sheets. Use the sample filter to see excluded entities and their reasons.
  It is not a current ranking or a validated failure prediction.

## Data contract

The dashboard reads only [`outputs/final_dataset.csv`](../outputs/final_dataset.csv),
produced by `code/04_build_dataset.py`. Each row is one listed entity.
The underlying bank measures are from December 2022, as defined in the pipeline.

| Field | Used for |
|---|---|
| `rssd_id` | Unique entity key for the table, chart, and selector |
| `ticker`, `name` | Display labels; the entity name is used when the ticker is blank |
| `uninsured_dep_share` | X-axis and historical screen |
| `bhar_0_2` | Y-axis: bank buy-and-hold return minus the CRSP value-weighted market buy-and-hold return over March 9, 10, and 13 |
| `bhr_0_2` | Bank's buy-and-hold return before subtracting the market, shown in the inspector |
| `total_assets_bn` | Dot size and table column, in billions of dollars |
| `sec_loss_to_equity`, `htm_loss_to_equity` | Securities loss / equity sets the dot color; the table also shows the HTM-only measure |
| `in_sample` | Official sample flag from the pipeline |
| `has_fdic`, `has_returns`, `positive_equity` | Explain exclusions in the inspector and historical table |
| `dlret_imputed` | Outlines points for which the pipeline assumed a total loss at delisting |

The app preserves missing values and displays them as dashes. Color
saturates at the plotted sample's 95th percentile of securities losses
relative to equity, so extreme ratios do not wash out the rest of the
chart. The original ratios still appear in the table and tooltips.

To rebuild the results, follow the [main README](../README.md#how-to-run)
and run `python run_all.py` with the licensed inputs under the ignored
`data/raw/crsp/` directory. The server never serves those inputs or any
files under `data/interim/`. The dashboard does not recompute returns.
