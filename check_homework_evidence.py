"""Additional Module 6 evidence: original profiles, planned record checks, fresh rerun."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

from clean_source_data import AI_KEY, BLS_KEY, FILES, NUMERIC

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'cleaned'


def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--profiles-only', action='store_true', help='Refresh profiles and record checks without rerunning the pipeline')
    args = parser.parse_args()
    source = args.input_dir
    audit = json.loads((OUT / 'cleaning_audit.json').read_text())
    profiles, missing, cases = [], [], []
    originals = {}
    for name in FILES:
        raw = (pd.read_csv(source / name, dtype='string', keep_default_na=False) if name.endswith('.csv')
               else pd.read_excel(source / name, sheet_name=0, dtype='string', keep_default_na=False))
        originals[name] = raw
        key = AI_KEY if name.endswith('.csv') else (['O*NET-SOC Code'] if name == 'Occupation Data.xlsx'
                                                    else [k.upper() for k in BLS_KEY])
        lone_id = 'node_external_id' if name.endswith('.csv') else ('O*NET-SOC Code' if name == 'Occupation Data.xlsx' else 'OCC_CODE')
        profiles.append({'source': name, 'rows': len(raw), 'exact_duplicates': int(raw.duplicated().sum()),
                         'repeated_full_keys': int(raw.duplicated(key).sum()),
                         'repeated_single_ids_after_first': int(raw.duplicated([lone_id]).sum()),
                         'trimmed_text_cells': sum(int(raw[c].ne(raw[c].str.strip()).sum()) for c in raw)})
        if name.startswith(('BOS', 'MSA')):
            for field in NUMERIC:
                x = raw[field.upper()].str.strip()
                status = audit[name]['numeric_status_counts'][field]
                missing.append({'source': name.split('_')[0], 'field': field,
                                'before_blank': int(x.eq('').sum()),
                                'before_star': int(x.eq('*').sum()), 'before_double_star': int(x.eq('**').sum()),
                                'before_hash': int(x.eq('#').sum()),
                                'after_exact_value_missing': sum(n for k, n in status.items() if k != 'reported')})
            clean = pd.read_parquet(OUT / (Path(name).stem.lower() + '_clean.parquet'))
            for field in ['annual', 'hourly']:
                blanks = int(raw[field.upper()].str.strip().eq('').sum())
                nulls = int(clean[field].isna().sum())
                assert blanks == nulls
                missing.append({'source': name.split('_')[0], 'field': field, 'before_blank': blanks,
                                'before_star': 0, 'before_double_star': 0, 'before_hash': 0,
                                'after_exact_value_missing': nulls})

    # Select originals and write expected outcomes BEFORE inspecting their cleaned records.
    msa = originals['MSA_M2025_dl.xlsx']
    ca = msa[msa.PRIM_STATE.eq('CA') & msa.O_GROUP.eq('detailed')]
    for field, token, status, bound in [('A_MEDIAN', '#', 'top_coded_lower_bound', 239200),
                                      ('TOT_EMP', '**', 'employment_not_available', None),
                                      ('A_MEDIAN', '*', 'wage_not_available', None)]:
        r = ca[ca[field].eq(token)].iloc[0]
        cases.append({'source': 'MSA_M2025_dl.xlsx', 'area': r.AREA, 'soc': r.OCC_CODE,
                      'field': field.lower(), 'original': token,
                      'expected': {'value': None, 'status': status, 'lower_bound': bound}})
    r = originals['BOS_M2025_dl.xlsx'].query("PRIM_STATE == 'CA' and O_GROUP == 'detailed'").iloc[0]
    cases.append({'source': 'BOS_M2025_dl.xlsx', 'area': r.AREA, 'soc': r.OCC_CODE,
                  'field': 'area_code', 'original': r.AREA, 'expected': {'value': r.AREA}})
    a = originals[FILES[0]]
    r = a[a.geo_id.eq('GLOBAL') & a.category_name.eq('soc_occupation') & a.hierarchy_level.eq('0')
          & a.metric_id.eq('use_case_work_pct') & a.date_start.eq('2026-05-01')].iloc[0]
    cases.append({'source': FILES[0], 'key': {k: r[k] for k in AI_KEY}, 'field': 'value',
                  'original': r.value, 'expected': {'value': float(r.value)}})
    for case, reason in zip(cases, ['The workbook defines # as a lower bound, not an exact wage.',
                                    'The workbook defines ** as unavailable employment, not zero.',
                                    'The workbook defines * as an unavailable wage, not zero.',
                                    'Area identifiers must keep leading zeros.',
                                    'Convert the numeric type while preserving the published percentage.']):
        case['reason'] = reason
    (OUT / 'record_check_expectations.json').write_text(json.dumps(cases, indent=2), encoding='utf-8')
    cleaned = pd.read_parquet(OUT / 'occupation_area.parquet')
    ai = pd.read_parquet(OUT / 'aei_claude_ai_clean.parquet')
    for c in cases:
        if 'area' in c:
            row = cleaned[cleaned.area_code.eq(c['area']) & cleaned.soc_code.eq(c['soc'])]
            assert len(row) == 1
            row = row.iloc[0]
            if c['field'] == 'area_code':
                actual = {'value': row.area_code}
            else:
                field = c['field']
                bound = row.get(field + '_lower_bound')
                actual = {'value': None if pd.isna(row[field]) else float(row[field]),
                          'status': row[field + '_status'], 'lower_bound': None if pd.isna(bound) else float(bound)}
        else:
            mask = pd.Series(True, index=ai.index)
            for key, value in c['key'].items():
                if key in ['date_start', 'date_end']:
                    value = pd.Timestamp(value)
                elif key == 'hierarchy_level':
                    value = int(value)
                mask &= ai[key].eq(value)
            assert mask.sum() == 1
            actual = {'value': float(ai.loc[mask, 'value'].iloc[0])}
        c['actual'] = actual
        c['matches'] = actual == c['expected']
        assert c['matches'], c
    pd.DataFrame(profiles).to_csv(OUT / 'homework_source_profiles.csv', index=False)
    pd.DataFrame(missing).to_csv(OUT / 'homework_missing_before_after.csv', index=False)
    (OUT / 'record_check_results.json').write_text(json.dumps(cases, indent=2), encoding='utf-8')
    # Small sample includes difficult wage/employment cases, a leading-zero ID, and ordinary rows.
    difficult = [cleaned[cleaned.area_code.eq(c['area']) & cleaned.soc_code.eq(c['soc'])] for c in cases if 'area' in c]
    sample = pd.concat(difficult + [cleaned.head(20)]).drop_duplicates(['area_code', 'soc_code']).head(20)
    sample.to_csv(OUT / 'homework_sample_20.csv', index=False)
    if args.profiles_only:
        print('Refreshed source profiles and five planned/actual record checks.')
        return
    manifest = json.loads((OUT / 'source_manifest.json').read_text())
    before = {p.name: digest(p) for p in OUT.iterdir() if p.is_file() and not p.name.startswith(('homework_', 'record_check_'))
              and p.name != 'validation_results.json'}
    subprocess.run([sys.executable, str(ROOT / 'clean_source_data.py'), '--input-dir', str(source)], check=True)
    changed = [name for name, value in before.items() if digest(OUT / name) != value]
    assert not changed, changed
    subprocess.run([sys.executable, str(ROOT / 'validate_cleaned_data.py'), '--input-dir', str(source)], check=True)
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-v'], check=True)
    source_same = all(digest(source / m['file']) == m['sha256'] for m in manifest)
    assert source_same
    results = {'matched_output_files': len(before), 'changed_output_files': changed, 'source_hashes_unchanged': source_same,
               'sample_rows': len(sample), 'record_checks_passed': len(cases),
               'ca_employment_sum': float(cleaned.tot_emp.sum()),
               'ca_employment_nonmissing': int(cleaned.tot_emp.count()),
               'ca_exact_median_wage_nonmissing': int(cleaned.a_median.count()),
               'ca_work_use_context_nonmissing': int(cleaned.has_global_work_use_context.sum())}
    (OUT / 'homework_verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
