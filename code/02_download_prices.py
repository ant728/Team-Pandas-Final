"""Step 2: pull a few banks' prices from yfinance, ONLY to cross-check CRSP returns in the hand checks.

CRSP is the source for every return we report. yfinance is free and independent, so if the two
agree on the event-window return for a few surviving banks, that's evidence our CRSP handling is right.

Output: data/raw/prices_check.csv, one row per symbol x date.

yfinance is unofficial and sometimes fails or rate-limits. Because this step is only a cross-check, a failure
here does not stop run_all.py: the symbol is skipped with a warning, and 06_hand_checks.py marks its
cross-check SKIPPED instead of passing it.
"""
import pandas as pd
import yfinance as yf

from config import CHECK_TICKERS, PRICE_END, PRICE_START, RAW
from provenance import log_download


def main():
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
