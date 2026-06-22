"""Build the PRIMARY local pooled dataset (decision 2026-06-19):
   Helene = 101 clusters (helene_100mi), Milton = 34 COUNTIES (milton_100mi).
   Outflow degeneracy handled by FLAG (outflow_degenerate), not by dropping units.
   -> results/local_level/regression/pooled_dataset_100mi_primary.csv  (135 rows)
The 30-cluster Milton variant (pooled_dataset_100mi_clustered.csv, from 00c) is the appendix robustness set.
Run with the geo env python. No mobility-tensor pass (reads existing metrics_*.csv).
"""
import pandas as pd, numpy as np, os

ROOT = '/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category'
LR   = f'{ROOT}/results/local_level'
NB   = f'{ROOT}/notebook'
DATA = f'{ROOT}/data'
HELENE_DIR = f'{LR}/helene_100mi'            # clusters
MILTON_DIR = f'{LR}/milton_100mi'            # counties (county-level metrics)
MILTON_CLU = f'{LR}/milton_clustered_100mi'  # per-county ACS+dist+nchs lookup (from 00b)
REG_OUT    = f'{LR}/regression'
FLOW = ['within', 'inflow', 'outflow']

acs = pd.read_csv(f'{NB}/acs_socioeconomic_v2.csv'); acs['GEOID'] = acs['GEOID'].astype(int)
nchs = pd.read_csv(f'{DATA}/NCHS Urban-Rural Classification Scheme for Counties.csv', encoding='utf-8-sig')
nchs['GEOID'] = nchs['Location'].astype(int); nchs['nchs_code'] = nchs['2023 Code'].str.extract(r'(\d)').astype(int)
coastal = pd.read_csv(f'{LR}/coastal_flags.csv'); coastal['GEOID'] = coastal['GEOID'].astype(int)
# per-county dist/nchs/name lookup built in 00b (covers all 34 Milton counties)
mcty = pd.read_csv(f'{MILTON_CLU}/county_cluster_assignments.csv'); mcty['GEOID'] = mcty['GEOID'].astype(int)

OUT_COLS = ['unit_id', 'unit_type', 'NAME', 'hurricane', 'hurricane_cat', 'n_counties',
            'total_population', 'median_household_income', 'pct_no_vehicle', 'pct_white',
            'insurance_coverage_pct', 'nchs_code', 'is_coastal', 'pop_density', 'dist_to_track_mi',
            'largest_drop_within', 'recovery_days_within', 'total_disruption_within',
            'largest_drop_inflow', 'recovery_days_inflow', 'total_disruption_inflow',
            'largest_increase_outflow', 'outflow_degenerate']

def outflow_flag(hrc_dir, ids):
    """flag = mean outflow baseline < 3% of this storm's median outflow baseline. ids as str."""
    bs = pd.read_csv(f'{hrc_dir}/baseline_summary.csv'); bs['unit_id'] = bs['unit_id'].astype(str)
    of = bs[bs['flow_type'] == 'outflow'].set_index('unit_id')['pred_mean']
    med = of.median()
    return {u: int(of.get(u, np.nan) < 0.03 * med) if pd.notna(of.get(u, np.nan)) else 0 for u in ids}, med

def load_helene_clusters():
    cdf = pd.read_csv(f'{HELENE_DIR}/county_cluster_assignments.csv'); cdf['GEOID'] = cdf['GEOID'].astype(int)
    extra = [c for c in ['pct_no_vehicle', 'insurance_coverage_pct', 'pct_white', 'white_pop'] if c not in cdf.columns]
    cdf = cdf.merge(acs[['GEOID'] + extra], on='GEOID', how='left')
    if 'nchs_code' not in cdf.columns:
        cdf = cdf.merge(nchs[['GEOID', 'nchs_code']], on='GEOID', how='left')
    cdf = cdf.merge(coastal[['GEOID', 'is_coastal', 'area_sq_mi']], on='GEOID', how='left')
    feat = cdf.groupby('cluster').apply(lambda g: pd.Series({
        'total_population': g['total_population'].sum(),
        'median_household_income': g['median_household_income'].median(),
        'pct_no_vehicle': g['pct_no_vehicle'].median(),
        'insurance_coverage_pct': g['insurance_coverage_pct'].median(),
        'pct_white': (g['white_pop'].sum() / g['total_population'].sum() * 100 if g['total_population'].sum() > 0 else np.nan),
        'nchs_code': g['nchs_code'].mode().iloc[0] if len(g['nchs_code'].mode()) else np.nan,
        'is_coastal': int(g['is_coastal'].any()), 'area_sq_mi': g['area_sq_mi'].sum(),
        'dist_to_track_mi': g['dist_to_track_mi'].mean(), 'n_counties': len(g),
        'NAME': g.sort_values('total_population', ascending=False)['NAME'].iloc[0]})).reset_index()
    feat['pop_density'] = feat['total_population'] / feat['area_sq_mi']
    m = {ft: pd.read_csv(f'{HELENE_DIR}/metrics_{ft}.csv') for ft in FLOW}
    for ft in m: m[ft]['unit_id'] = m[ft]['unit_id'].astype(int)
    df = (m['within'][['unit_id', 'largest_drop', 'recovery_days', 'total_disruption']]
          .rename(columns={'unit_id': 'cluster', 'largest_drop': 'largest_drop_within',
                           'recovery_days': 'recovery_days_within', 'total_disruption': 'total_disruption_within'}))
    df = df.merge(m['inflow'][['unit_id', 'largest_drop', 'recovery_days', 'total_disruption']]
                  .rename(columns={'unit_id': 'cluster', 'largest_drop': 'largest_drop_inflow',
                                   'recovery_days': 'recovery_days_inflow', 'total_disruption': 'total_disruption_inflow'}),
                  on='cluster', how='left')
    df = df.merge(m['outflow'][['unit_id', 'largest_increase']]
                  .rename(columns={'unit_id': 'cluster', 'largest_increase': 'largest_increase_outflow'}), on='cluster', how='left')
    df = df.merge(feat, on='cluster', how='left')
    df['hurricane'] = 'helene'; df['hurricane_cat'] = 4; df['unit_type'] = 'cluster'; df['unit_id'] = df['cluster']
    flag, med = outflow_flag(HELENE_DIR, df['unit_id'].astype(str))
    df['outflow_degenerate'] = df['unit_id'].astype(str).map(flag)
    print(f'Helene: {len(df)} clusters | outflow median {med:,.0f} | flagged {df.outflow_degenerate.sum()}')
    return df[OUT_COLS]

def load_milton_counties():
    m = {ft: pd.read_csv(f'{MILTON_DIR}/metrics_{ft}.csv') for ft in FLOW}
    for ft in m: m[ft]['unit_id'] = m[ft]['unit_id'].astype(int)
    df = (m['within'][['unit_id', 'largest_drop', 'recovery_days', 'total_disruption']]
          .rename(columns={'unit_id': 'GEOID', 'largest_drop': 'largest_drop_within',
                           'recovery_days': 'recovery_days_within', 'total_disruption': 'total_disruption_within'}))
    df = df.merge(m['inflow'][['unit_id', 'largest_drop', 'recovery_days', 'total_disruption']]
                  .rename(columns={'unit_id': 'GEOID', 'largest_drop': 'largest_drop_inflow',
                                   'recovery_days': 'recovery_days_inflow', 'total_disruption': 'total_disruption_inflow'}),
                  on='GEOID', how='left')
    df = df.merge(m['outflow'][['unit_id', 'largest_increase']]
                  .rename(columns={'unit_id': 'GEOID', 'largest_increase': 'largest_increase_outflow'}), on='GEOID', how='left')
    df = df.merge(acs[['GEOID', 'total_population', 'median_household_income', 'pct_no_vehicle',
                       'insurance_coverage_pct', 'pct_white']], on='GEOID', how='left')
    df = df.merge(mcty[['GEOID', 'NAME', 'nchs_code', 'dist_to_track_mi']], on='GEOID', how='left')
    df = df.merge(coastal[['GEOID', 'is_coastal', 'area_sq_mi']], on='GEOID', how='left')
    df['pop_density'] = df['total_population'] / df['area_sq_mi']
    df['n_counties'] = 1
    df['hurricane'] = 'milton'; df['hurricane_cat'] = 5; df['unit_type'] = 'county'; df['unit_id'] = df['GEOID']
    flag, med = outflow_flag(MILTON_DIR, df['unit_id'].astype(str))
    df['outflow_degenerate'] = df['unit_id'].astype(str).map(flag)
    deg = df[df.outflow_degenerate == 1]['NAME'].tolist()
    print(f'Milton: {len(df)} counties | outflow median {med:,.0f} | flagged {df.outflow_degenerate.sum()} {deg}')
    return df[OUT_COLS]

helene = load_helene_clusters()
milton = load_milton_counties()
pooled = pd.concat([milton, helene], ignore_index=True)
pooled['is_milton'] = (pooled['hurricane'] == 'milton').astype(int)
out = f'{REG_OUT}/pooled_dataset_100mi_primary.csv'
pooled.to_csv(out, index=False)
print(f'\nsaved {out}  ({len(pooled)} rows = {len(milton)} Milton counties + {len(helene)} Helene clusters)')
print('within DV nulls:', int(pooled.largest_drop_within.isna().sum()),
      '| inflow DV nulls:', int(pooled.largest_drop_inflow.isna().sum()),
      '| outflow DV nulls:', int(pooled.largest_increase_outflow.isna().sum()),
      '| outflow_degenerate total:', int(pooled.outflow_degenerate.sum()))
