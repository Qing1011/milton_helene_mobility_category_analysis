"""Assemble the CLUSTERED (appendix) pooled dataset: Milton 30 clusters + Helene 101 clusters.
This is the cross-storm combine that used to live in 00c Stage D; kept out of the per-storm notebooks (00c/00e).
Reads each storm's clustered metrics + cluster assignments, aggregates ACS per cluster (same rule as the primary),
adds an outflow_degenerate flag, and writes results/local_level/regression/pooled_dataset_100mi_clustered.csv (131).
geo env. APPENDIX robustness only — the PRIMARY uses Milton COUNTIES (build_primary_pooled.py).
"""
import pandas as pd, numpy as np, os
ROOT='/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category'
LR=f'{ROOT}/results/local_level'; NB=f'{ROOT}/notebook'; DATA=f'{ROOT}/data'; REG=f'{LR}/regression'
FLOW=['within','inflow','outflow']
acs=pd.read_csv(f'{NB}/acs_socioeconomic_v2.csv'); acs['GEOID']=acs['GEOID'].astype(int)
nchs=pd.read_csv(f'{DATA}/NCHS Urban-Rural Classification Scheme for Counties.csv', encoding='utf-8-sig')
nchs['GEOID']=nchs['Location'].astype(int); nchs['nchs_code']=nchs['2023 Code'].str.extract(r'(\d)').astype(int)
coastal=pd.read_csv(f'{LR}/coastal_flags.csv'); coastal['GEOID']=coastal['GEOID'].astype(int)

def outflow_flag(hrc_dir, ids):
    bs=pd.read_csv(f'{hrc_dir}/baseline_summary.csv'); bs['unit_id']=bs['unit_id'].astype(str)
    of=bs[bs['flow_type']=='outflow'].set_index('unit_id')['pred_mean']; med=of.median()
    return {u:(int(of.get(u,np.nan)<0.03*med) if pd.notna(of.get(u,np.nan)) else 0) for u in ids}

def load_clustered(clustered_dir, hurricane, cat):
    cdf=pd.read_csv(f'{clustered_dir}/county_cluster_assignments.csv'); cdf['GEOID']=cdf['GEOID'].astype(int)
    extra=[c for c in ['pct_no_vehicle','insurance_coverage_pct','pct_white','white_pop'] if c not in cdf.columns]
    cdf=cdf.merge(acs[['GEOID']+extra],on='GEOID',how='left')
    if 'nchs_code' not in cdf.columns: cdf=cdf.merge(nchs[['GEOID','nchs_code']],on='GEOID',how='left')
    cdf=cdf.merge(coastal[['GEOID','is_coastal','area_sq_mi']],on='GEOID',how='left')
    feat=cdf.groupby('cluster').apply(lambda g: pd.Series({
        'total_population':g['total_population'].sum(),'median_household_income':g['median_household_income'].median(),
        'pct_no_vehicle':g['pct_no_vehicle'].median(),'insurance_coverage_pct':g['insurance_coverage_pct'].median(),
        'pct_white':(g['white_pop'].sum()/g['total_population'].sum()*100 if g['total_population'].sum()>0 else np.nan),
        'nchs_code':g['nchs_code'].mode().iloc[0] if len(g['nchs_code'].mode()) else np.nan,
        'is_coastal':int(g['is_coastal'].any()),'area_sq_mi':g['area_sq_mi'].sum(),
        'dist_to_track_mi':g['dist_to_track_mi'].mean(),'n_counties':len(g),
        'NAME':g.sort_values('total_population',ascending=False)['NAME'].iloc[0]})).reset_index()
    feat['pop_density']=feat['total_population']/feat['area_sq_mi']
    m={ft:pd.read_csv(f'{clustered_dir}/metrics_{ft}.csv') for ft in FLOW}
    for ft in m: m[ft]['unit_id']=m[ft]['unit_id'].astype(int)
    df=(m['within'][['unit_id','largest_drop','recovery_days','total_disruption']]
        .rename(columns={'unit_id':'cluster','largest_drop':'largest_drop_within','recovery_days':'recovery_days_within','total_disruption':'total_disruption_within'}))
    df=df.merge(m['inflow'][['unit_id','largest_drop','recovery_days','total_disruption']]
        .rename(columns={'unit_id':'cluster','largest_drop':'largest_drop_inflow','recovery_days':'recovery_days_inflow','total_disruption':'total_disruption_inflow'}),on='cluster',how='left')
    df=df.merge(m['outflow'][['unit_id','largest_increase']].rename(columns={'unit_id':'cluster','largest_increase':'largest_increase_outflow'}),on='cluster',how='left')
    df=df.merge(feat,on='cluster',how='left')
    df['hurricane']=hurricane; df['hurricane_cat']=cat; df['unit_type']='cluster'; df['unit_id']=df['cluster']
    flag=outflow_flag(clustered_dir, df['unit_id'].astype(str)); df['outflow_degenerate']=df['unit_id'].astype(str).map(flag)
    return df

mil=load_clustered(f'{LR}/milton_clustered_100mi','milton',5)
hel=load_clustered(f'{LR}/helene_100mi','helene',4)
COLS=['unit_id','NAME','hurricane','hurricane_cat','n_counties','total_population','median_household_income',
      'pct_no_vehicle','pct_white','insurance_coverage_pct','nchs_code','is_coastal','pop_density','dist_to_track_mi',
      'largest_drop_within','recovery_days_within','total_disruption_within','largest_drop_inflow','recovery_days_inflow',
      'total_disruption_inflow','largest_increase_outflow','outflow_degenerate']
pooled=pd.concat([mil[COLS],hel[COLS]], ignore_index=True); pooled['is_milton']=(pooled['hurricane']=='milton').astype(int)
out=f'{REG}/pooled_dataset_100mi_clustered.csv'; pooled.to_csv(out, index=False)
print(f'saved {out} ({len(pooled)} rows = {len(mil)} Milton clusters + {len(hel)} Helene clusters) | outflow_degenerate={int(pooled.outflow_degenerate.sum())}')
