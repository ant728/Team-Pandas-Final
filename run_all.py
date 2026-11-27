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
    "07_zions_reconciliation.py",
    "08_fragility_screen.py",
    "09_screen_today.py",
    "10_placebo_windows.py",
    "06_hand_checks.py",   # runs last so it can recheck every step's output, including steps 8-10
]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    subprocess.run([sys.executable, str(CODE / step)], cwd=CODE, check=True)
print("\nDone. See outputs/.")
