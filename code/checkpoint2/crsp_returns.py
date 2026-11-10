"""Aggregate licensed CRSP daily returns without publishing daily observations."""
import numpy as np
import pandas as pd
from config import CRSP_DIR, EVENT_DAY0, EVENT_WINDOW, ESTIMATION_WINDOW, RAW
from provenance import log_download


def event_study_crsp(xw):
    path = CRSP_DIR / 'crsp_daily_2022_2023.csv'
    daily = pd.read_csv(path, parse_dates=['date', 'dlstdt'])
    market = pd.read_csv(CRSP_DIR / 'crsp_market_vwretd.csv', parse_dates=['date']).set_index('date').sort_index()
    assert not daily.duplicated(['permno', 'date']).any()
    assert market.index.is_unique
    assert daily.groupby('permco').permno.nunique().max() == 1, 'Select share classes explicitly if this changes'
    assert daily.shrcd.eq(11).all()
    assert xw.permco.is_unique
    cal = market.index
    p0 = cal.get_loc(pd.Timestamp(EVENT_DAY0))
    est_dates = cal[p0+ESTIMATION_WINDOW[0]:p0+ESTIMATION_WINDOW[1]+1]
    evt_dates = cal[p0+EVENT_WINDOW[0]:p0+EVENT_WINDOW[1]+1]
    benchmark = float((1+market.loc[evt_dates, 'vwretd']).prod()-1)
    rows, daily_private = [], []
    for bank in xw.itertuples():
        stock = daily[daily.permco.eq(bank.permco)].set_index('date').sort_index()
        stock['total_ret'] = pd.to_numeric(stock.ret, errors='coerce')
        dl = pd.to_numeric(stock.dlret, errors='coerce')
        on_delist = stock.index.to_series().eq(stock.dlstdt) & stock.dlstcd.ne(100) & stock.dlstcd.notna()
        observed_dl = on_delist & dl.notna()
        stock.loc[observed_dl, 'total_ret'] = (1+stock.loc[observed_dl, 'total_ret'])*(1+dl[observed_dl])-1
        evt = stock.reindex(evt_dates)
        bad_dl = on_delist.reindex(evt_dates, fill_value=False) & evt.dlret.isna()
        rec = {'ticker':bank.ticker, 'car_note':'', 'return_source':'CRSP RET + observed DLRET; CRSP VWRETD benchmark',
               'market_buy_hold_return':benchmark, 'bhar_failure_zero_recovery_scenario':np.nan,
               'buy_hold_return':np.nan, 'bhar_mktadj':np.nan, 'car_0_2':np.nan, 'car_0_2_mktadj':np.nan,
               'beta':np.nan, 'alpha':np.nan, 'est_obs':0}
        if bad_dl.any():
            rec['car_note'] = 'Missing CRSP delisting return; incomplete event window. Zero recovery shown only as scenario.'
            # A -100% total investment loss is a scenario, not a CRSP-observed return.
            rec['bhar_failure_zero_recovery_scenario'] = -1-benchmark
        elif evt.total_ret.isna().any():
            rec['car_note'] = 'Missing daily event return; no imputation'
        else:
            rec['buy_hold_return'] = float((1+evt.total_ret).prod()-1)
            rec['bhar_mktadj'] = rec['buy_hold_return']-benchmark
            rec['car_0_2_mktadj'] = float((evt.total_ret-market.loc[evt_dates,'vwretd']).sum())
        est = stock.reindex(est_dates)[['total_ret']].join(market[['vwretd']]).dropna()
        rec['est_obs'] = len(est)
        if len(est) >= 150:
            beta, alpha = np.polyfit(est.vwretd, est.total_ret, 1)
            rec.update(beta=float(beta), alpha=float(alpha))
            if pd.notna(rec['buy_hold_return']):
                rec['car_0_2'] = float((evt.total_ret-alpha-beta*market.loc[evt_dates,'vwretd']).sum())
        rows.append(rec)
    # Record receipt/source without claiming a fresh WRDS download.
    log_download(path, 'User-supplied CRSP/WRDS delivery, pulled 2026-11-06 by provider',
                 vintage='legacy CRSP dsf/dsenames/dsedelist/dsi', note='Local licensed input; never publish daily rows')
    return pd.DataFrame(rows), pd.DataFrame(columns=['licensed_daily_rows_not_exported'])
