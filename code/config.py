"""Shared paths and study settings. Every script imports from here so the choices live in one place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
PROVENANCE_LOG = ROOT / "data" / "provenance_log.csv"

CROSSWALK = INPUTS / "checkpoint2_crosswalk.csv"
CRSP_DIR = RAW / "crsp_delivery" / "ant728_request"
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
    "CERT", "NAME", "FED_RSSD", "RSSDHCR", "NAMEHCR", "REPDTE",
    "ASSET",     # total assets
    "DEP",       # total deposits
    "DEPDOM",    # deposits in domestic offices
    "DEPUNINS",  # estimated uninsured deposits, domestic offices (RC-O; banks > $1B only)
    "EQTOT",     # total equity capital
    "EQCCOMPI",  # OTHER COMPREHENSIVE INCOME: flow, not accumulated AOCI balance
    "SC",        # total securities (= SCHA + SCAF)
    "SCHA",      # held-to-maturity securities, amortized cost (book value)
    "SCHF",      # held-to-maturity securities, fair value
    "SCAA",      # available-for-sale securities, amortized cost
    "SCAF",      # available-for-sale securities, fair value (book value)
]

# Event: SVB announced a $1.8B securities loss and a capital raise after the close on Wed Mar 8, 2023.
# Day 0 is the first trading day after that news.
EVENT_DAY0 = "2023-03-09"
EVENT_WINDOW = (0, 2)          # Mar 9, Mar 10 (SVB closed by regulators), Mar 13 (Signature closed Sunday)
ESTIMATION_WINDOW = (-250, -30)  # trading days relative to day 0, for the market model
MARKET = "SPY"

PRICE_START = "2022-01-01"
PRICE_END = "2023-04-01"
