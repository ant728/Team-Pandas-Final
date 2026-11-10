"""Reconcile sourced Zions disclosures with the official raw FDIC report.

This is an accounting diagnostic, not a second event study or a new regression.
Dollar amounts in the disclosure file are millions; FDIC amounts are thousands.
"""
import pandas as pd

from config import CALL_REPORT_DATE, OUTPUTS, RAW, ROOT


def main():
    disclosures = pd.read_csv(ROOT / 'inputs' / 'zions_disclosures.csv')
    assert disclosures['item'].is_unique
    assert pd.to_datetime(disclosures['public_date']).lt(pd.Timestamp('2023-03-09')).all()
    assert disclosures['report_date'].eq('2022-12-31').all()
    values = disclosures.set_index('item')['value_millions']
    reports = pd.read_csv(RAW / f'fdic_financials_{CALL_REPORT_DATE}.csv')
    zions = reports.loc[reports['CERT'].eq(2270)]
    assert len(zions) == 1, 'Expected one Zions bank report (CERT 2270)'
    bank = zions.iloc[0]
    assert bank['EQTOT'] > 0
    equity_millions = bank['EQTOT'] / 1000

    # Compare independently transcribed rounded disclosures with the raw API.
    fields = {'htm_cost': 'SCHA', 'htm_fair_value': 'SCHF',
              'afs_cost': 'SCAA', 'afs_fair_value': 'SCAF', 'oci_2022_flow_aftertax': 'EQCCOMPI'}
    disclosures['fdic_value_millions'] = disclosures['item'].map(
        {item: bank[field] / 1000 for item, field in fields.items()})
    disclosures['difference_millions'] = disclosures['fdic_value_millions'] - disclosures['value_millions']
    checks = disclosures['item'].isin(fields)
    assert disclosures.loc[checks, 'difference_millions'].abs().le(1).all(), '10-K/FDIC mismatch exceeds rounding'
    assert (values['securities_aoci_aftertax'] + values['derivatives_other_aoci_aftertax']
            + values['pension_aoci_aftertax']) == values['total_aoci_aftertax']

    htm_gap = values['htm_cost'] - values['htm_fair_value']
    afs_gap = values['afs_cost'] - values['afs_fair_value']
    comparison = pd.DataFrame([
        ('HTM gap / equity', htm_gap / equity_millions, 'Rounded 10-K gap / FDIC equity'),
        ('HTM + AFS gaps / equity', (htm_gap + afs_gap) / equity_millions, 'Rounded 10-K gaps / FDIC equity'),
        ('Transfer-adjusted / equity (approximate diagnostic)',
         (htm_gap + afs_gap + values['transfer_loss_pretax_approx']) / equity_millions,
         'Approximate disclosed transfer loss; not exact remaining year-end balance'),
        ('2022 OCI flow / equity', bank['EQCCOMPI'] / bank['EQTOT'],
         'Flow, not accumulated AOCI; not a securities-only loss measure'),
    ], columns=['measure', 'value', 'note'])
    # Expose the flow and denominator in public outputs so the note is traceable.
    additional = pd.DataFrame([
        {'item': 'fdic_equity', 'value_millions': equity_millions, 'source': 'FDIC BankFind financials',
         'location': 'CERT 2270; EQTOT; 20221231', 'note': 'Denominator; millions of dollars'},
        {'item': 'fdic_oci_2022_flow', 'value_millions': bank['EQCCOMPI'] / 1000,
         'source': 'FDIC BankFind financials', 'location': 'CERT 2270; EQCCOMPI; 20221231',
         'note': 'Other comprehensive income flow; not accumulated AOCI'},
    ])
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    pd.concat([disclosures, additional], ignore_index=True).to_csv(OUTPUTS / 'zions_reconciliation.csv', index=False)
    comparison.to_csv(OUTPUTS / 'zions_measure_comparison.csv', index=False)
    print('Zions reconciliation: five rounded disclosure checks and AOCI component check PASS.')
    print(comparison.to_string(index=False))


if __name__ == '__main__':
    main()
