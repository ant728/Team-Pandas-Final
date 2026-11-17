"""Step 2: prices from yfinance, for two separate jobs.

1. KRE, the regional-bank ETF (REQUIRED). Step 3 estimates each bank's beta to KRE, the control for the
   common shock in spec R5 (instructor audit A3, specs_tried.md #14). Our CRSP pull doesn't include KRE.
   Output: data/raw/kre_daily.csv, one row per date. If it can't be downloaded after a few tries, the run stops.

2. A few banks' prices, ONLY to cross-check CRSP returns in the hand checks. CRSP is the source for every
   bank return we report; if yfinance agrees on the event-window return for a few surviving banks, that's
   evidence our CRSP handling is right. Output: data/raw/prices_check.csv, one row per symbol x date.
   yfinance is unofficial and sometimes fails or rate-limits. Because these are only cross-checks, a failure
   does not stop run_all.py: the symbol is skipped with a warning, and 06_hand_checks.py marks it SKIPPED.
"""
import time

import pandas as pd
import yfinance as yf

from config import CHECK_TICKERS, KRE_END, KRE_PRICES, KRE_START, KRE_TICKER, PRICE_END, PRICE_START, RAW
from provenance import log_download


def download_kre(tries=3):
    for attempt in range(1, tries + 1):
        try:
            h = yf.Ticker(KRE_TICKER).history(start=KRE_START, end=KRE_END, auto_adjust=True)
            if not h.empty:
                break
            print(f"yfinance returned nothing for {KRE_TICKER} (try {attempt} of {tries})")
        except Exception as e:  # network errors, rate limits
            print(f"yfinance failed for {KRE_TICKER} (try {attempt} of {tries}): {e}")
        time.sleep(5 * attempt)
    else:
        raise RuntimeError(f"Could not download {KRE_TICKER} from yfinance; step 3 needs it for kre_beta (spec R5). "
                           "Rerun later.")
    kre = h[["Close"]].reset_index()
    kre["Date"] = kre["Date"].dt.tz_localize(None).dt.normalize()
    kre.columns = ["date", "close"]
    assert kre["date"].is_unique
    RAW.mkdir(parents=True, exist_ok=True)
    kre.to_csv(KRE_PRICES, index=False)
    log_download(KRE_PRICES, f"yfinance Ticker('{KRE_TICKER}').history(auto_adjust=True)",
                 vintage=f"yfinance {yf.__version__}", note=f"regional-bank index for kre_beta; {KRE_START} to {KRE_END}")
    print(f"{KRE_TICKER}: {len(kre)} days")


def main():
    download_kre()

    frames = []
    for sym in CHECK_TICKERS:
        try:
            h = yf.Ticker(sym).history(start=PRICE_START, end=PRICE_END, auto_adjust=True)
        except Exception as e:  # network errors, rate limits, yfinance API changes
            print(f"WARNING: yfinance failed for {sym} ({e}); its cross-check will be SKIPPED")
            continue
        if h.empty:
            print(f"WARNING: yfinance returned nothing for {sym}; its cross-check will be SKIPPED")
            continue
        df = h[["Close"]].reset_index()
        df["Date"] = df["Date"].dt.tz_localize(None).dt.normalize()
        df.columns = ["date", "close"]
        df["symbol"] = sym
        frames.append(df)
        print(f"{sym}: {len(df)} days")

    if not frames:
        print("WARNING: no yfinance prices downloaded; all yfinance cross-checks will be SKIPPED")
        (RAW / "prices_check.csv").unlink(missing_ok=True)  # never cross-check against an old download
        return

    out = pd.concat(frames, ignore_index=True)[["symbol", "date", "close"]]
    assert not out.duplicated(["symbol", "date"]).any()
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "prices_check.csv"
    out.to_csv(path, index=False)
    log_download(path, "yfinance Ticker.history(auto_adjust=True)",
                 vintage=f"yfinance {yf.__version__}", note=f"cross-check only; {PRICE_START} to {PRICE_END}")


if __name__ == "__main__":
    main()
