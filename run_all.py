"""Rebuild everything from the raw sources: python run_all.py"""
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent / "code"
STEPS = [
    "00_build_universe.py",
    "01_download_fdic.py",
    "02_download_prices.py",
    "03_crsp_returns.py",
    "04_build_dataset.py",
    "05_regressions.py",
    "06_hand_checks.py",
]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    subprocess.run([sys.executable, str(CODE / step)], cwd=CODE, check=True)
print("\nDone. See outputs/.")
