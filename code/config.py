"""Shared paths and study settings. Every script imports from here so the choices live in one place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"   # git-ignored: holds row-level CRSP data, which is licensed
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
PROVENANCE_LOG = ROOT / "data" / "provenance_log.csv"
REQUESTS = ROOT / "requests"

# NY Fed CRSP-FRB link: maps each listed bank entity (RSSD ID) to its CRSP PERMCO, with start/end dates.
# Page: https://www.newyorkfed.org/research/banking_research/crsp-frb  (this is the Sep 30, 2024 vintage)
NYFED_LINK_URL = ("https://www.newyorkfed.org/medialibrary/media/research/banking_research/data/"
                  "crsp_20240930v2.csv")

# Call report quarter: the last one public BEFORE the event.
# Q4 2022 call reports were due Jan 30, 2023, well before SVB's Mar 8, 2023 announcement.
CALL_REPORT_DATE = "20221231"

# FDIC BankFind fields (all in $ thousands). Definitions:
# https://api.fdic.gov/banks/docs/risview_properties.yaml
FDIC_FIELDS = [
    "CERT", "NAME", "RSSDHCR", "NAMEHCR", "REPDTE",
    "ASSET",     # total assets
    "DEP",       # total deposits
    "DEPDOM",    # deposits in domestic offices
    "DEPUNINS",  # estimated uninsured deposits, domestic offices (filled for 4,720 of 4,773 banks in Q4 2022)
    "DEPLGAMT",  # amount in deposit accounts over $250,000 (all banks)
    "DEPLGB",    # number of deposit accounts over $250,000 (all banks)
    "EQTOT",     # total equity capital
    "EQCCOMPI",  # accumulated other comprehensive income (after tax), for the Zions question
    "SC",        # total securities (= SCHA + SCAF)
    "SCHA",      # held-to-maturity securities, amortized cost (book value)
    "SCHF",      # held-to-maturity securities, fair value
    "SCAA",      # available-for-sale securities, amortized cost
    "SCAF",      # available-for-sale securities, fair value (book value)
]
INSURANCE_LIMIT_THOUSANDS = 250  # FDIC insurance limit per account, in $ thousands

# CRSP daily data, pulled by Prof. Bowen from WRDS on 2026-11-06 (see README provenance).
# Licensed for Lehigh users only: the files live in data/raw/crsp/ (git-ignored) and are never published.
CRSP_DIR = RAW / "crsp"
CRSP_DAILY = CRSP_DIR / "crsp_daily_2022_2023.csv"
CRSP_MARKET = CRSP_DIR / "crsp_market_vwretd.csv"
CRSP_DELIST = CRSP_DIR / "crsp_delistings.csv"

# Event: SVB announced a $1.8B securities loss and a capital raise after the close on Wed Mar 8, 2023.
# Day 0 is the first trading day after that news.
EVENT_DAY0 = "2023-03-09"
EVENT_WINDOW = (0, 2)            # Mar 9, Mar 10 (SVB closed by regulators), Mar 13 (Signature closed Sunday)
ESTIMATION_WINDOW = (-250, -30)  # trading days relative to day 0, for the market model
MIN_EST_OBS = 150

# SVB and Signature delisted on Mar 10, 2023 (code 584) with no CRSP delisting return.
# Their equity was wiped out in the failures, so we set the missing delisting return to -100%.
# specs_tried.md logs the alternative (dropping them).
MISSING_DLRET_FAILED = -1.0

# yfinance is used only as an independent cross-check of CRSP returns in the hand checks.
CHECK_TICKERS = ["JPM", "WAL", "ZION"]
PRICE_START = "2023-03-01"
PRICE_END = "2023-03-20"
