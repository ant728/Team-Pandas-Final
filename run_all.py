"""Rebuild everything from the raw sources: python run_all.py"""
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent / "code"
CRSP = CODE.parent / 'data/raw/crsp_delivery/ant728_request/crsp_daily_2022_2023.csv'
STEPS = [
    "00_build_universe.py",
    "01_download_fdic.py",
    "02_download_prices.py",
    "03_build_dataset.py",
    "04_hand_checks.py",
    "05_checkpoint_outputs.py",
]

for step in STEPS:
    if step == '02_download_prices.py' and CRSP.exists():
        print('Using local licensed CRSP delivery; skipping yfinance download.', flush=True)
        continue
    print(f"\n=== {step} ===", flush=True)
    subprocess.run([sys.executable, str(CODE / step)], cwd=CODE, check=True)
print("\nDone. See outputs/.")
