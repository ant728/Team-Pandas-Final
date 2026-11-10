"""Serve an allowlisted public preview; never serve the repository or raw data directory."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
dest = root / 'work' / 'preview'
files = ['app/index.html', 'PROPOSAL.md', 'audits/01_self_audit.md',
         'docs/zions_measurement.md', 'docs/images/dashboard_mockup.png',
         'outputs/dashboard_data.json', 'outputs/poc_final_rows.csv',
         'outputs/zions_reconciliation.csv']
for name in files:
    source = root / name
    if source.exists():
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
print('Open http://127.0.0.1:8766/app/index.html ; only allowlisted public assets are served.', flush=True)
ThreadingHTTPServer(('127.0.0.1', 8766), partial(SimpleHTTPRequestHandler, directory=str(dest))).serve_forever()
