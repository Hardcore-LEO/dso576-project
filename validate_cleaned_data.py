"""Independent output reconciliation; exits nonzero on any failed check."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=Path)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'data' / 'cleaned')
    args = parser.parse_args()
    out = args.output_dir
    checks = []

    def check(name, condition):
        checks.append({'check': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)

    audit = json.loads((out / 'cleaning_audit.json').read_text(encoding='utf-8'))
    bls = pd.concat([pd.read_parquet(out / (stem + '_clean.parquet'))
                     for stem in ['bos_m2025_dl', 'msa_m2025_dl']], ignore_index=True)
    ca = pd.read_parquet(out / 'occupation_area.parquet')
    ai = pd.read_parquet(out / 'aei_claude_ai_clean.parquet')
    onet = pd.read_parquet(out / 'occupations.parquet')
    wide = pd.read_parquet(out / 'occupation_ai_by_scope.parquet')
    check('Complete AEI rows reconcile', len(ai) == audit['aei_claude_ai_2026-06-26.csv']['clean_rows'])
    check('Complete BLS rows reconcile', len(bls) == sum(audit[name]['clean_rows'] for name in
          ['BOS_M2025_dl.xlsx', 'MSA_M2025_dl.xlsx']))
    check('Dictionary rows reconcile', len(onet) == audit['Occupation Data.xlsx']['clean_rows'])
    check('Full BLS key unique', not bls.duplicated(['area', 'area_type', 'naics', 'i_group', 'own_code',
                                                'occ_code', 'o_group']).any())
    check('Full AEI key unique', not ai.duplicated(['date_start', 'date_end', 'geo_id', 'geo_level',
          'category_name', 'hierarchy_level', 'metric_id', 'node_external_id']).any())
    check('CA key unique', not ca.duplicated(['area_code', 'soc_code']).any())
    expected = bls[bls.prim_state.eq('CA') & bls.o_group.eq('detailed')]
    check('No employment multiplication', len(ca) == len(expected) and
          np.isclose(ca.tot_emp.sum(), expected.tot_emp.sum()))
    merged = ca.merge(expected[['area', 'occ_code', 'tot_emp', 'a_median']],
                      left_on=['area_code', 'soc_code'], right_on=['area', 'occ_code'], validate='one_to_one')
    for field in ['tot_emp', 'a_median']:
        check(f'Every {field} survives joins unchanged', np.allclose(
            merged[field + '_x'].to_numpy(dtype=float, na_value=np.nan),
            merged[field + '_y'].to_numpy(dtype=float, na_value=np.nan), equal_nan=True))
    check('No occupation totals included', ca.o_group.eq('detailed').all())
    check('Nonmetro leading zeros survive', ca.loc[ca.area_type.eq('6'), 'area_code'].str.startswith('06').all())
    for prefix, lower in [('a_', 239200), ('h_', 115)]:
        for col in [c for c in bls if c.startswith(prefix) and c.endswith('_status')]:
            raw = col.removesuffix('_status')
            mask = bls[col].eq('top_coded_lower_bound')
            check(f'{raw} top coding preserved', bls.loc[mask, raw].isna().all()
                  and bls.loc[mask, raw + '_lower_bound'].eq(lower).all())
    check('All source AI percentages within bounds', ai.loc[ai.metric_id.str.endswith('pct'), 'value'].between(0, 100).all())
    check('Both original months retained', set(ai.date_start.dt.strftime('%Y-%m-%d')) == {'2026-04-01', '2026-05-01'})
    check('No false local occupation work-use measurements',
          wide.loc[wide.geo_id.isin(['US-CA', 'USA']), 'use_case_work_pct'].isna().all())
    # Independently recompute ranges from long source rows, not from the pipeline's wide table.
    current = ai[ai.date_start.eq(ai.date_start.max()) & ai.geo_id.eq('GLOBAL')
                 & ai.category_name.eq('soc_occupation') & ai.hierarchy_level.eq(0)
                 & ai.metric_id.eq('use_case_work_pct')].copy()
    current['soc_code'] = current.node_external_id.str.slice(0, 7)
    recalc = current.groupby('soc_code').value.agg(['min', 'max', 'count']).reset_index()
    compared = ca.merge(recalc, on='soc_code', how='left', validate='many_to_one')
    for suffix, field in [('min', 'min'), ('max', 'max'), ('n_extensions', 'count')]:
        actual = compared['use_case_work_pct_' + suffix]
        target = compared[field]
        if suffix == 'n_extensions':
            actual, target = actual.fillna(0), target.fillna(0)
        check('Independent work-use ' + suffix, np.allclose(actual.astype(float), target.astype(float), equal_nan=True))
    check('Context missingness flags consistent', ca.has_global_work_use_context.eq(
          ca.use_case_work_pct_min.notna()).all())
    check('No fabricated importance/exposure/priority', not {'importance_value', 'observed_exposure',
                                                           'priority_score'} & set(ca.columns))
    change = pd.read_parquet(out / 'occupation_usage_month_comparison.parquet')
    check('Unpublished month not filled with zero', change.loc[~change.both_months_published,
                                                              'change_percentage_points'].isna().all())
    check('Month changes arithmetic', np.allclose(change.change_percentage_points,
          change.may_usage_share_pct - change.april_usage_share_pct, equal_nan=True))
    for name in ['occupation_area', 'occupations', 'occupation_ai_by_scope']:
        csv = pd.read_csv(out / (name + '.csv'), dtype=str, keep_default_na=False)
        parquet = pd.read_parquet(out / (name + '.parquet'))
        check(name + ' CSV row count', len(csv) == len(parquet))
        for col in ['area_code', 'soc_code', 'onet_soc_code']:
            if col in parquet:
                check(name + ' CSV ' + col, csv[col].tolist() == parquet[col].fillna('').tolist())
    source_checked = False
    if args.input_dir:
        for m in json.loads((out / 'source_manifest.json').read_text(encoding='utf-8')):
            with (args.input_dir / m['file']).open('rb') as f:
                digest = hashlib.file_digest(f, 'sha256').hexdigest()
            check(m['file'] + ' unchanged', digest == m['sha256'])
        source_checked = True
    result = {'status': 'passed', 'passed_checks': len(checks), 'source_files_rehashed': source_checked, 'checks': checks}
    (out / 'validation_results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"PASS: {len(checks)} independent validation checks")


if __name__ == '__main__':
    main()
