# Checkpoint 2 dashboard

From the repository root, run:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open <http://127.0.0.1:8765/app/>. Use the server rather than opening
`index.html` directly so the browser can load the CSV. Press Ctrl+C to stop
the server. No JavaScript packages or external services are required.

- **Intro** explains the question and shows data coverage.
- **Method** describes the pre-event balance-sheet measures and CAR.
- **March 2023 Results** shows the four complete yfinance event CARs in the
  original six-bank sample. Select a bank or its point to inspect its values.
- **Who's Next** shows all six banks' December 2022 reports, with search and
  numeric sorting. It is a historical screen demonstration, not a current
  ranking or a validation result.

## Optional local CRSP preview

With authorized access to the professor's CRSP ZIP, run the following from
the root, replacing the archive path as needed:

```sh
python3 -B code/05_crsp_dashboard_preview.py "/path/to/ant728_request.zip"
```

This reads the ZIP without extracting it and writes
`outputs/poc_crsp_rows.csv`. Reload the dashboard to switch between the
original SPY-based CAR and the CRSP value-weighted market-model CAR. The
CRSP preview recovers Comerica; SVB's CAR stays blank because its event
window is incomplete. Neither preview imputes SVB's delisting return.

The ZIP stays local. Only per-bank aggregates and public balance-sheet
measures reach the dashboard. The generated CRSP preview is ignored by Git.
Do not place the ZIP or raw daily records under the web server root.

## Data contract

The browser reads only `outputs/poc_final_rows.csv` and, when present,
`outputs/poc_crsp_rows.csv`. Each file has one row per ticker for December
31, 2022. The optional preview must use the same balance-sheet snapshot as
the original.

| Field | Used for |
|---|---|
| `ticker`, `entity_name`, `call_report_date` | Entity label, date, and unique key |
| `uninsured_dep_share` | Scatter x-axis and screen, stored as a fraction |
| `car_0_2`, `car_note` | Scatter y-axis and missing-return explanation |
| `total_assets_bn` | Scatter size and table column, in billions of dollars |
| `sec_loss_to_equity` | Scatter color and screen, preliminary HTM + AFS measure |
| `htm_loss_to_equity` | Comparison column for the HTM-only measure |

Missing numeric values stay blank. When the pipeline moves to a
buy-and-hold return or revises the loss measure, update the field, label,
and Method definition together. The CRSP generator is an optional
coverage preview; it does not modify or replace `run_all.py`.
