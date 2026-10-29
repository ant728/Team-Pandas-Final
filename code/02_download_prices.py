"""Step 2: pull daily adjusted closes from yfinance for the sample banks and the market (SPY).

Output: data/raw/prices.csv in long form, one row per symbol x date.
Symbols yfinance can't find (delisted banks) are logged in data/raw/prices_missing.csv
instead of being dropped silently.
"""
import pandas as pd
import yfinance as yf

from config import CROSSWALK, MARKET, PRICE_END, PRICE_START, RAW
from provenance import log_download


def main():
    xw = pd.read_csv(CROSSWALK)
    symbols = list(xw["yf_symbol"]) + [MARKET]

    frames, missing = [], []
    for sym in symbols:
        h = yf.Ticker(sym).history(start=PRICE_START, end=PRICE_END, auto_adjust=True)
        if h.empty:
            missing.append(sym)
            print(f"{sym}: NO DATA")
            continue
        df = h[["Close"]].reset_index()
        df["Date"] = df["Date"].dt.tz_localize(None).dt.normalize()
        df.columns = ["date", "close"]
        df["symbol"] = sym
        frames.append(df)
        print(f"{sym}: {len(df)} days, {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}")

    out = pd.concat(frames, ignore_index=True)[["symbol", "date", "close"]]
    assert not out.duplicated(["symbol", "date"]).any()

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "prices.csv"
    out.to_csv(path, index=False)
    log_download(path, "yfinance Ticker.history(auto_adjust=True)",
                 vintage=f"yfinance {yf.__version__}", note=f"{PRICE_START} to {PRICE_END}")

    miss_path = RAW / "prices_missing.csv"
    pd.DataFrame({"yf_symbol": missing}).to_csv(miss_path, index=False)
    print(f"Saved {len(out)} rows to {path}; missing: {missing or 'none'}")


if __name__ == "__main__":
    main()
