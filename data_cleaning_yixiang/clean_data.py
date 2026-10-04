"""Reproduce the individual Module 6 submission from untouched source files."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import zipfile
from io import BytesIO
from pathlib import Path
import pandas as pd

AEI_KEY = ['date_start','date_end','geo_id','geo_level','category_name',
           'hierarchy_level','metric_id','node_external_id']
BLS_KEY = ['AREA','AREA_TYPE','NAICS','OWN_CODE','OCC_CODE']
BLS_NUM = ['TOT_EMP','EMP_PRSE','JOBS_1000','LOC_QUOTIENT','PCT_TOTAL',
           'PCT_RPT','H_MEAN','A_MEAN','MEAN_PRSE','H_PCT10','H_PCT25',
           'H_MEDIAN','H_PCT75','H_PCT90','A_PCT10','A_PCT25','A_MEDIAN',
           'A_PCT75','A_PCT90']
SIGNALS = {
    'usa_share_of_messages_by_onet_iwa_month.csv':['month','iwa_cleaned'],
    'usa_share_of_work_related_messages_by_onet_iwa_month.csv':['month','iwa_cleaned'],
    'usa_share_of_messages_by_state_2025_rank.csv':['year','state_code'],
    'usa_share_of_messages_by_topic_state_2025.csv':['year','state_code','topic'],
}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def dump(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def profile(d, key):
    return {'rows':len(d),'columns':list(d.columns),
            'input_types':{c:str(t) for c,t in d.dtypes.items()},
            'blank_counts':{c:int(v) for c,v in d.eq('').sum().items()},
            'exact_duplicate_excess':int(d.duplicated().sum()),
            'logical_key':key,
            'repeated_key_excess':int(d.duplicated(key).sum()),
            'rows_with_repeated_key':int(d.duplicated(key,keep=False).sum())}

def trim(d, audit):
    d=d.copy()
    changes={}
    examples=[]
    for c in d:
        s=d[c].str.strip()
        changed=s.ne(d[c])
        changes[c]=int(changed.sum())
        for i in d.index[changed][:2]:
            examples.append({'column':c,'source_record':int(i)+1,
                             'before':d.at[i,c],'after':s.at[i]})
        d[c]=s
    audit['text_changes']=changes
    audit['text_examples']=examples[:10]
    return d

def numeric(s, markers=('',)):
    parsed=pd.to_numeric(s.mask(s.isin(markers)),errors='coerce')
    unexpected=parsed.isna() & ~s.isin(markers)
    if unexpected.any():
        raise ValueError(f'Unexpected numeric tokens: {s[unexpected].unique()[:10]}')
    return parsed

def save(d, path, key):
    path.parent.mkdir(parents=True,exist_ok=True)
    d.sort_values(key,kind='stable').to_csv(path,index=False,lineterminator='\n')

def run(source, output):
    source,output=Path(source),Path(output)
    clean=output/'cleaned'
    evidence=output/'evidence'
    clean.mkdir(parents=True,exist_ok=True)
    evidence.mkdir(parents=True,exist_ok=True)
    audit={'rule_version':'1.0','sources':{},'merges':{},'outputs':{}}
    manifest={}

    def register(rel):
        p=source/rel
        manifest[rel]={'bytes':p.stat().st_size,'sha256':digest(p)}
        return p

    # All rows in both AEI files are inspected; scoped output retains original fields.
    aei_parts=[]
    for product,filename in [('claude_ai','aei_claude_ai_2026-06-26.csv'),
                             ('1p_api','aei_1p_api_2026-06-26.csv')]:
        rel='2026-06-26/'+filename
        raw=pd.read_csv(register(rel),dtype=str,keep_default_na=False)
        a=profile(raw,AEI_KEY)
        a['repeated_node_id_excess']=int(raw.duplicated('node_external_id').sum())
        d=trim(raw,a)
        assert not d.duplicated(AEI_KEY).any(), 'AEI key collision'
        assert not d[AEI_KEY].eq('').any().any(), 'Missing AEI key'
        values=numeric(d.value)
        assert values.notna().all()
        import numpy as np
        assert np.isfinite(values).all()
        dates={c:pd.to_datetime(d[c],format='%Y-%m-%d',errors='coerce')
               for c in ['date_start','date_end']}
        assert all(v.notna().all() for v in dates.values())
        assert (dates['date_start']<dates['date_end']).all()
        hierarchy=numeric(d.hierarchy_level)
        assert hierarchy.isin([0,1,2,3]).all()
        percent=d.metric_id.eq('pct') | d.metric_id.str.endswith('_pct')
        unusual=(percent & ~values.between(0,100)) | (values<0)
        unusual |= d.metric_id.eq('ai_autonomy_mean') & ~values.between(1,5)
        a['conversion_failures']={'value':0,'date_start':0,'date_end':0,'hierarchy_level':0}
        a['range_flag_count_full']=int(unusual.sum())
        a['periods']=sorted(d.date_start.unique().tolist())
        a['geographies']=d.geo_level.value_counts().to_dict()
        mask=d.category_name.eq('soc_occupation') & d.geo_id.isin(['US-CA','USA','GLOBAL'])
        kept=d.loc[mask].copy()
        kept['source_record']=kept.index+1
        kept['source_file']=rel
        kept['source_id']=product
        kept['value_raw']=kept.value
        kept['node_name_raw']=raw.loc[mask,'node_name']
        kept['value']=values.loc[mask]
        kept['hierarchy_level']=hierarchy.loc[mask].astype(int)
        kept['range_flag']=unusual.loc[mask]
        kept['unit']=kept.metric_id.map(lambda x:'percent' if x=='pct' or x.endswith('_pct')
            else {'ai_autonomy_mean':'scale_1_to_5','human_only_time_mean':'hours',
                  'human_with_ai_time_mean':'minutes','usage_per_capita_index':'index'}.get(x,
                  'years' if x.endswith('education_years_mean') else 'source_defined'))
        a['selected_rows']=len(kept)
        a['excluded_outside_scope']=len(d)-len(kept)
        a['missing_value_after']=int(kept.value.isna().sum())
        audit['sources'][rel]=a
        aei_parts.append(kept)
        print(f'{product}: inspected {len(d):,}; retained {len(kept):,}',flush=True)
    aei=pd.concat(aei_parts,ignore_index=True)
    save(aei,clean/'anthropic_occupations.csv',['source_id']+AEI_KEY)

    # Inspect both full workbooks, retaining only the declared California scope.
    archive=register('oesm25ma.zip')
    bls_parts=[]
    with zipfile.ZipFile(archive) as z:
        for member in ['oesm25ma/BOS_M2025_dl.xlsx','oesm25ma/MSA_M2025_dl.xlsx']:
            raw=pd.read_excel(BytesIO(z.read(member)),dtype=str,keep_default_na=False)
            a=profile(raw,BLS_KEY)
            d=trim(raw,a)
            assert not d.duplicated(BLS_KEY).any(),'BLS key collision'
            a['numeric_markers_full']={c:d.loc[d[c].isin(['','*','**','#']),c].value_counts().to_dict()
                                      for c in BLS_NUM}
            for c in BLS_NUM:
                numeric(d[c],('','*','**','#'))
            a['conversion_failures']={c:0 for c in BLS_NUM}
            mask=d.PRIM_STATE.eq('CA') & d.O_GROUP.eq('detailed') & d.NAICS.eq('000000') & d.OWN_CODE.eq('1235')
            kept=d.loc[mask].copy()
            kept['source_record']=kept.index+1
            kept['source_file']=member
            kept['AREA_TITLE_raw']=raw.loc[mask,'AREA_TITLE']
            a['missing_before']={c:int(kept[c].eq('').sum()) for c in BLS_NUM}
            a['missing_after']={}
            a['raw_markers_selected']={}
            for c in BLS_NUM:
                kept[c+'_raw']=kept[c]
                a['raw_markers_selected'][c]=kept.loc[kept[c].isin(['','*','**','#']),c].value_counts().to_dict()
                kept[c]=numeric(kept[c],('','*','**','#'))
                a['missing_after'][c]=int(kept[c].isna().sum())
            kept['range_flag']=kept[BLS_NUM].lt(0).any(axis=1)
            kept['cross_state_area']=kept.AREA_TITLE.str.contains(r', [A-Z]{2}-[A-Z]{2}',regex=True)
            kept['oews_release']='2025-05'
            a['selected_rows']=len(kept)
            a['excluded_non_CA']=int((~d.PRIM_STATE.eq('CA')).sum())
            a['excluded_CA_other_scope']=int(d.PRIM_STATE.eq('CA').sum())-len(kept)
            a['range_flag_count_selected']=int(kept.range_flag.sum())
            a['employment_total_selected']=float(kept.TOT_EMP.sum(min_count=1))
            a['employment_n_selected']=int(kept.TOT_EMP.notna().sum())
            audit['sources'][member]=a
            bls_parts.append(kept)
            print(f'{member}: inspected {len(d):,}; retained {len(kept):,}',flush=True)
    bls=pd.concat(bls_parts,ignore_index=True)
    assert not bls.duplicated(['AREA','OCC_CODE']).any()
    save(bls,clean/'bls_ca_occupations.csv',['AREA','OCC_CODE'])

    for filename,key in SIGNALS.items():
        rel='data-download-csv/public_release_csv/'+filename
        raw=pd.read_csv(register(rel),dtype=str,keep_default_na=False)
        a=profile(raw,key)
        d=trim(raw,a)
        assert not d.duplicated(key).any()
        assert not d[key].eq('').any().any()
        metric='rank' if 'rank' in d else 'share_of_messages'
        d[metric+'_raw']=d[metric]
        d[metric]=numeric(d[metric])
        assert d[metric].notna().all()
        if metric=='rank':
            assert d[metric].between(1,51).all() and (d[metric]%1==0).all()
        else:
            assert d[metric].between(0,1).all()
            group=['month'] if 'month' in d else ['year','state_code']
            a['share_sums_by_group']=d.groupby(group,dropna=False)[metric].sum().reset_index().to_dict('records')
        if 'month' in d:
            assert pd.to_datetime(d.month,format='%Y-%m-%d',errors='coerce').notna().all()
        d['source_record']=d.index+1
        a['conversion_failures']={metric:0}
        a['selected_rows']=len(d)
        audit['sources'][rel]=a
        save(d,clean/filename,key)

    # A provisional code-prefix join, deliberately not a priority score.
    ca=aei[(aei.source_id=='claude_ai') & (aei.geo_id=='US-CA') &
           (aei.hierarchy_level==0) & (aei.metric_id=='pct') & (aei.date_start=='2026-05-01')].copy()
    assert len(ca)>0
    assert ca.node_external_id.str.fullmatch(r'\d{2}-\d{4}\.\d{2}').all()
    ca['OCC_CODE']=ca.node_external_id.str[:7]
    roll=ca.groupby('OCC_CODE',as_index=False,dropna=False).agg(
        ca_claude_usage_pct=('value','sum'),
        contributing_onet_codes=('node_external_id',lambda s:';'.join(sorted(s))),
        contributing_code_count=('node_external_id','size'))
    assert abs(roll.ca_claude_usage_pct.sum()-ca.value.sum())<1e-9
    joined=bls.merge(roll,on='OCC_CODE',how='left',validate='many_to_one',indicator=True)
    joined=joined.rename(columns={'_merge':'ai_match_status'})
    joined['ai_geography']='US-CA'
    joined['ai_period']='2026-05-01/2026-06-01'
    joined['mapping_status']='provisional_SOC_prefix_not_verified_crosswalk'
    assert len(joined)==len(bls)
    assert joined.TOT_EMP.sum()==bls.TOT_EMP.sum()
    save(roll,clean/'ca_claude_soc_prefix.csv',['OCC_CODE'])
    save(joined,clean/'ca_workforce_context.csv',['AREA','OCC_CODE'])
    unmatched=joined.loc[joined.ai_match_status.eq('left_only'),['OCC_CODE','OCC_TITLE']].drop_duplicates()
    save(unmatched,evidence/'unmatched_bls_occupations.csv',['OCC_CODE'])
    unused=roll.loc[~roll.OCC_CODE.isin(bls.OCC_CODE)]
    save(unused,evidence/'unmatched_anthropic_prefixes.csv',['OCC_CODE'])
    audit['merges']['bls_to_ca_claude']={
        'key':'OCC_CODE','relationship':'many BLS areas to one CA occupation prefix',
        'bls_before':len(bls),'aei_leaf_before':len(ca),'aei_prefix_after':len(roll),
        'joined_after':len(joined),'unmatched_bls_rows':int(joined.ai_match_status.eq('left_only').sum()),
        'unmatched_bls_codes':len(unmatched),'unused_aei_prefixes':len(unused),
        'employment_before':float(bls.TOT_EMP.sum()),'employment_after':float(joined.TOT_EMP.sum()),
        'aei_share_before':float(ca.value.sum()),'aei_share_after':float(roll.ca_claude_usage_pct.sum()),
        'taxonomy_status':'provisional; team must verify official crosswalk before decision use'}
    stats=[]
    for area,g in joined.groupby(['AREA','AREA_TITLE'],dropna=False,sort=True):
        stats.append({'AREA':area[0],'AREA_TITLE':area[1],'rows':len(g),
            'employment_n':int(g.TOT_EMP.notna().sum()),'employment_published_sum':float(g.TOT_EMP.sum(min_count=1)),
            'median_wage_n':int(g.A_MEDIAN.notna().sum()),
            'mean_of_published_occupation_medians':float(g.A_MEDIAN.mean()),
            'ai_matched_rows':int(g.ai_match_status.eq('both').sum())})
    save(pd.DataFrame(stats),evidence/'area_metric_support.csv',['AREA'])
    audit['outputs']['summary']={'bls_rows':len(bls),'areas':int(bls.AREA.nunique()),
        'occupations':int(bls.OCC_CODE.nunique()),'anthropic_rows':len(aei),
        'employment_missing':int(bls.TOT_EMP.isna().sum()),'wage_missing':int(bls.A_MEDIAN.isna().sum()),
        'employment_published_sum':float(bls.TOT_EMP.sum()),
        'employment_n':int(bls.TOT_EMP.notna().sum()),'wage_n':int(bls.A_MEDIAN.notna().sum()),
        'unmatched_ai_rows':int(joined.ca_claude_usage_pct.isna().sum())}

    ordered=joined.sort_values(['AREA','OCC_CODE']).reset_index(drop=True)
    chosen=[]
    rules=[('suppressed_employment',ordered.TOT_EMP.isna()),
           ('topcoded_wage',ordered.A_MEDIAN_raw.eq('#')),
           ('unavailable_wage',ordered.A_MEDIAN_raw.eq('*')),
           ('unmatched_AI',ordered.ai_match_status.eq('left_only')),
           ('multiple_ONET_codes',ordered.contributing_code_count.gt(1))]
    reasons={}
    for label,mask in rules:
        candidates=ordered.index[mask & ~ordered.index.isin(chosen)]
        if len(candidates):
            i=int(candidates[0]); chosen.append(i); reasons[str(i)]=label
    for i in ordered.index:
        if len(chosen)>=50: break
        if i not in chosen: chosen.append(int(i))
    ordered.loc[chosen].to_csv(output/'cleaned_sample.csv',index=False,lineterminator='\n')
    dump(evidence/'sample_selection.json',{'method':'first row for each difficult-case rule, then sorted AREA/OCC_CODE until 50',
        'difficult_case_sorted_indices':reasons,'rows':len(chosen),
        'representative':False,'all_cleaned_columns_included':True})
    dump(evidence/'full_data_checks.json',audit)
    dump(evidence/'source_manifest.json',manifest)
    for rel,entry in manifest.items():
        assert digest(source/rel)==entry['sha256'],'Source changed during run'
    hashes={str(p.relative_to(output)).replace('\\','/'):digest(p)
            for p in sorted(output.rglob('*')) if p.is_file() and
            ('cleaned' in p.parts or p.name=='cleaned_sample.csv')}
    dump(evidence/'output_hashes.json',hashes)
    dump(evidence/'environment.json',{'python':platform.python_version(),'pandas':pd.__version__,
        'platform':platform.platform()})
    print(json.dumps(audit['outputs']['summary'],indent=2),flush=True)
    return audit

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,default=Path(__file__).parent/'outputs')
    args=parser.parse_args()
    run(args.source_root,args.output_dir)
