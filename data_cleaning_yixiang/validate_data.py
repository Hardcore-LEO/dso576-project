"""Independent source-to-output checks, using csv/Decimal/openpyxl, not cleaning helpers."""
import argparse
import csv
import hashlib
import json
import zipfile
from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import openpyxl

def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:
        yield from csv.DictReader(f)

def validate(source,output):
    source,output=Path(source),Path(output)
    cleaned=list(rows(output/'cleaned/ca_workforce_context.csv'))
    by_key={(r['AREA'],r['OCC_CODE']):r for r in cleaned}
    assert len(by_key)==len(cleaned)
    sample=list(rows(output/'cleaned_sample.csv'))
    assert 0<len(sample)<=50
    assert all(r==by_key[(r['AREA'],r['OCC_CODE'])] for r in sample)
    numcols=['TOT_EMP','EMP_PRSE','JOBS_1000','LOC_QUOTIENT','PCT_TOTAL','PCT_RPT',
             'H_MEAN','A_MEAN','MEAN_PRSE','H_PCT10','H_PCT25','H_MEDIAN','H_PCT75',
             'H_PCT90','A_PCT10','A_PCT25','A_MEDIAN','A_PCT75','A_PCT90']
    originals={}
    counts={}
    total=Decimal(0)
    with zipfile.ZipFile(source/'oesm25ma.zip') as z:
        for member in ['oesm25ma/BOS_M2025_dl.xlsx','oesm25ma/MSA_M2025_dl.xlsx']:
            w=openpyxl.load_workbook(BytesIO(z.read(member)),read_only=True,data_only=True)
            it=iter(w.active.values); header=next(it); n=0
            for record,row in enumerate(it,1):
                d={c:('' if v is None else str(v)).strip() for c,v in zip(header,row)}
                if not(d['PRIM_STATE']=='CA' and d['O_GROUP']=='detailed' and
                       d['NAICS']=='000000' and d['OWN_CODE']=='1235'): continue
                n+=1; key=(d['AREA'],d['OCC_CODE']); actual=by_key[key]
                assert actual['source_file']==member
                assert int(actual['source_record'])==record
                for c in header:
                    if c in numcols:
                        # Pandas may serialize integral Excel values without .0.
                        token=d[c]
                        if token in ('','*','**','#'):
                            assert actual[c]=='' and actual[c+'_raw']==token
                        else:
                            assert abs(Decimal(actual[c])-Decimal(token))<Decimal('0.00000001')
                            assert abs(Decimal(actual[c+'_raw'])-Decimal(token))<Decimal('0.00000001')
                    else:
                        assert actual[c]==d[c],(key,c,actual[c],d[c])
                if d['TOT_EMP'] not in ('','*','**','#'): total+=Decimal(d['TOT_EMP'])
                originals[key]=d
            counts[member]=n
            w.close()
    assert sum(counts.values())==len(cleaned)
    assert total==sum(Decimal(r['TOT_EMP']) for r in cleaned if r['TOT_EMP'])
    shares=defaultdict(Decimal); codes=defaultdict(set); aei_n=0
    for d in rows(source/'2026-06-26/aei_claude_ai_2026-06-26.csv'):
        if (d['geo_id']=='US-CA' and d['category_name']=='soc_occupation' and
            d['hierarchy_level']=='0' and d['metric_id']=='pct' and d['date_start']=='2026-05-01'):
            code=d['node_external_id'][:7]
            shares[code]+=Decimal(d['value']); codes[code].add(d['node_external_id']); aei_n+=1
    for r in cleaned:
        code=r['OCC_CODE']
        if code in shares:
            assert abs(Decimal(r['ca_claude_usage_pct'])-shares[code])<Decimal('0.000000001')
            assert r['contributing_onet_codes']==';'.join(sorted(codes[code]))
            assert Decimal(r['contributing_code_count'])==len(codes[code])
            assert r['ai_match_status']=='both'
        else:
            assert r['ca_claude_usage_pct']=='' and r['ai_match_status']=='left_only'
    checks=[]
    # The sample begins with the difficult cases found by the cleaning pipeline.
    for r in sample[:5]:
        key=(r['AREA'],r['OCC_CODE']); raw=originals[key]
        reason=[]
        if raw['TOT_EMP'] in ('*','**',''): reason.append('Unpublished employment stays missing, not zero.')
        if raw['A_MEDIAN']=='#': reason.append('Top-coded wage stays missing; its exact value is unknown.')
        elif raw['A_MEDIAN'] in ('*','**',''): reason.append('Unavailable wage stays missing, not zero.')
        if not r['ca_claude_usage_pct']: reason.append('Unpublished/unmatched AI cell stays missing, not zero.')
        if len(codes.get(r['OCC_CODE'],[]))>1: reason.append('Sum only published leaf-code shares within one CA period; mapping remains provisional.')
        if not reason: reason.append('Valid published values and identifiers are preserved.')
        checks.append({'AREA':key[0],'OCC_CODE':key[1],'occupation':r['OCC_TITLE'],
            'source_file':r['source_file'],'source_record':int(r['source_record']),
            'original':{c:raw[c] for c in ['TOT_EMP','A_MEDIAN','AREA','OCC_CODE']},
            'expected':{'TOT_EMP':None if raw['TOT_EMP'] in ('','*','**','#') else raw['TOT_EMP'],
                        'A_MEDIAN':None if raw['A_MEDIAN'] in ('','*','**','#') else raw['A_MEDIAN'],
                        'ca_claude_usage_pct':str(shares[key[1]]) if key[1] in shares else None},
            'actual':{c:r[c] or None for c in ['TOT_EMP','A_MEDIAN','ca_claude_usage_pct']},
            'reason':' '.join(reason),'matches':True})
    result={'passed':True,'independent_bls_rows_checked':len(cleaned),
            'source_CA_rows_by_workbook':counts,'numeric_columns_checked_per_row':len(numcols),
            'employment_total_from_original':str(total),'aei_leaf_rows_independently_aggregated':aei_n,
            'all_joined_rows_checked_against_original_AI':len(cleaned),
            'sample_rows_exactly_match_full_output':len(sample),'five_record_checks':checks}
    (output/'evidence/independent_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='five_record_checks'},indent=2),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,default=Path(__file__).parent/'outputs')
    a=p.parse_args(); validate(a.source_root,a.output_dir)
