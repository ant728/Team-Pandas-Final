"""Independent public-figure, aggregation and CRSP event-return checks."""
import csv
import math
import pandas as pd
from config import CALL_REPORT_DATE, CRSP_DIR, OUTPUTS, RAW, CROSSWALK

final = pd.read_csv(OUTPUTS / 'poc_final_rows.csv').set_index('ticker')
checks = []
def check(name, actual, expected, tol, source):
    ok = math.isfinite(actual) and abs(actual-expected) <= tol
    checks.append((name, actual, expected, tol, 'PASS' if ok else 'FAIL', source))

check('SVB uninsured domestic share', final.at['SIVB','uninsured_dep_share'], .94, .01,
      'Fed SVB review: approximately 94%; https://www.federalreserve.gov/publications/2023-April-SVB-Key-Takeaways.htm')
check('SVB HTM loss ($B)', final.at['SIVB','htm_unrealized_loss_bn'], 15.1, .3,
      'Original project hand check against SVB 2022 10-K; subsidiary aggregation differs from parent')
with open(RAW / f'fdic_financials_{CALL_REPORT_DATE}.csv', newline='') as f:
    jpm = sum(float(r['ASSET']) for r in csv.DictReader(f) if r['ticker']=='JPM') / 1e6
check('JPM asset aggregation ($B)', final.at['JPM','total_assets_bn'], jpm, .001, 'Plain csv loop over raw FDIC subsidiary records')

xw = pd.read_csv(CROSSWALK).set_index('ticker')
daily = pd.read_csv(CRSP_DIR / 'crsp_daily_2022_2023.csv')
market = pd.read_csv(CRSP_DIR / 'crsp_market_vwretd.csv')
dates = ['2023-03-09','2023-03-10','2023-03-13']
# Independent scalar multiplication rather than the vectorized pipeline implementation.
bank_product = market_product = 1.0
for date in dates:
    r = daily[(daily.permco==xw.at['WAL','permco']) & (daily.date==date)].iloc[0]
    gross = 1+float(r.ret)
    if pd.notna(r.dlret) and r.dlstdt==date:
        gross *= 1+float(r.dlret)
    bank_product *= gross
    market_product *= 1+float(market.loc[market.date==date,'vwretd'].iloc[0])
check('WAL compounded return', final.at['WAL','buy_hold_return'], bank_product-1, .0001, 'Independent CRSP scalar product over exactly three trading dates')
check('WAL market-adjusted BHAR', final.at['WAL','bhar_mktadj'], bank_product-market_product, .0001, 'Independent stock gross return minus CRSP market gross return')
assert final.index.is_unique and len(final)==len(xw)
for ticker in ['SIVB','SBNY']:
    assert pd.isna(final.at[ticker,'bhar_mktadj']), 'Unknown failed-bank return must stay unknown'
    check(ticker+' zero-recovery scenario', final.at[ticker,'bhar_failure_zero_recovery_scenario'], -market_product, .0001,
          'Assumption only: terminal stock value zero; not an observed CRSP return')
check('Comerica return coverage', float(pd.notna(final.at['CMA','bhar_mktadj'])), 1, 0, 'CRSP restores later-acquired bank coverage')

lines = ['# Hand checks','', 'Generated from local raw inputs by `04_hand_checks.py`. Scenario checks validate arithmetic, not recovery assumptions.','',
'| Check | Pipeline | Independent | Tolerance | Result | Evidence |','|---|---:|---:|---:|---|---|']
for name,a,b,tol,res,src in checks:
    lines.append(f'| {name} | {a:.4f} | {b:.4f} | {tol:g} | {res} | {src} |')
(OUTPUTS/'hand_checks.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
assert all(r[4]=='PASS' for r in checks), 'Independent check failed'
