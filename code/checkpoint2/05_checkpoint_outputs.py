"""Export the dashboard inputs and descriptive diagnostics; no network requests here."""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from config import INPUTS, OUTPUTS


def main():
    final = pd.read_csv(OUTPUTS / 'checkpoint2_dataset.csv')
    assert final.ticker.is_unique
    assert final.uninsured_dep_share.dropna().between(0, 1).all()
    disclosures = pd.read_csv(INPUTS / 'zions_disclosures.csv')
    assert (pd.to_datetime(disclosures.public_date) < pd.Timestamp('2023-03-09')).all()
    d = disclosures.set_index('item').value_millions
    assert d.securities_aoci_aftertax + d.derivatives_other_aoci_aftertax + d.pension_aoci_aftertax == d.total_aoci_aftertax
    z = final.set_index('ticker').loc['ZION']
    assert abs(z.htm_unrealized_loss_bn * 1000 - (d.htm_cost - d.htm_fair_value)) < 1
    assert abs(z.afs_unrealized_loss_bn * 1000 - (d.afs_cost - d.afs_fair_value)) < 1
    # Derive exact equity from the existing processed dollar aggregates, not rounded output ratios.
    from config import PROCESSED
    equity_m = pd.read_csv(PROCESSED / 'bank_measures.csv').set_index('ticker').at['ZION', 'EQTOT'] / 1000
    diagnostic = pd.DataFrame([
        ('HTM gap / equity', (d.htm_cost-d.htm_fair_value)/equity_m),
        ('HTM + AFS gaps / equity', (d.htm_cost-d.htm_fair_value+d.afs_cost-d.afs_fair_value)/equity_m),
        ('Transfer-adjusted / equity (approximate diagnostic)',
         (d.htm_cost-d.htm_fair_value+d.afs_cost-d.afs_fair_value+d.transfer_loss_pretax_approx)/equity_m),
    ], columns=['measure', 'value'])
    diagnostic.to_csv(OUTPUTS / 'zions_measure_comparison.csv', index=False)
    disclosures.to_csv(OUTPUTS / 'zions_reconciliation.csv', index=False)
    complete = final.dropna(subset=['bhar_mktadj', 'uninsured_dep_share', 'sec_loss_to_equity'])
    fit = {'n': len(complete), 'status': 'insufficient observations', 'outcome': 'bhar_mktadj', 'predictors': ['uninsured_dep_share', 'sec_loss_to_equity'], 'inference': 'No p-values: selected proof-of-concept sample, missing failed banks.'}
    if len(complete) >= 4:
        X = np.column_stack([np.ones(len(complete)), complete.uninsured_dep_share, complete.sec_loss_to_equity])
        assert np.linalg.matrix_rank(X) == 3
        coef = np.linalg.lstsq(X, complete.bhar_mktadj, rcond=None)[0]
        fit.update(status='descriptive OLS only', residual_df=int(len(complete)-3),
                   coefficients=dict(zip(['intercept','uninsured_dep_share','sec_loss_to_equity'], map(float,coef))))
    (OUTPUTS / 'regression_diagnostic.json').write_text(json.dumps(fit, indent=2), encoding='utf-8')
    def records(frame):
        return json.loads(frame.to_json(orient='records'))
    payload = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'sample': records(final),
               'report_date': '2022-12-31', 'event': '2023-03-09 to 2023-03-13',
               'zions': records(diagnostic), 'regression': fit,
               'live_screen_available': False, 'crsp_available': True}
    (OUTPUTS / 'dashboard_data.json').write_text(json.dumps(payload, indent=2, allow_nan=False), encoding='utf-8')
    print(f'Dashboard: {len(final)} banks; {len(complete)} observed event returns. Zions reconciliation checks pass.')


if __name__ == '__main__':
    main()
