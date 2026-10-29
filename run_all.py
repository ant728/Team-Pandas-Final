"""Rebuild everything from the raw sources: python run_all.py"""
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent / "code"
STEPS = [
    "01_download_fdic.py",
    "02_download_prices.py",
    "03_build_dataset.py",
    "04_hand_checks.py",
]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    subprocess.run([sys.executable, str(CODE / step)], cwd=CODE, check=True)
print("\nDone. See outputs/.")
