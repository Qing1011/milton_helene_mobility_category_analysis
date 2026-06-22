"""Augment the PRIMARY pooled dataset with physical-exposure covariates (precip + wind).
geo env. -> results/local_level/regression/pooled_dataset_100mi_primary_exposure.csv

precip_total_{3,7}day : reused from pooled_dataset_100mi_with_precip.csv (same 135 primary units),
                        joined on (hurricane, total_population).
wind_vmax_sust (m/s)  : from results/exposure/wind_2024_by_county.csv (Willoughby 2024).
                        Milton county = its own value; Helene cluster = population-weighted mean over members.
"""
import pandas as pd, numpy as np
ROOT='/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category'
LR=f'{ROOT}/results/local_level'; REG=f'{LR}/regression'
prim=pd.read_csv(f'{REG}/pooled_dataset_100mi_primary.csv')

# ── precip: join from existing per-unit precip file ──
pp=pd.read_csv(f'{REG}/pooled_dataset_100mi_with_precip.csv')[
    ['hurricane','total_population','precip_total_3day','precip_total_7day']].copy()
# total_population is a unique fingerprint per unit within a storm
assert not pp.duplicated(['hurricane','total_population']).any(), 'precip key not unique'
prim=prim.merge(pp, on=['hurricane','total_population'], how='left')
miss=prim['precip_total_7day'].isna().sum()
print(f'precip merged | missing {miss}/{len(prim)}')

# ── wind: aggregate vmax_sust to each primary unit ──
wind=pd.read_csv(f'{LR}/../exposure/wind_2024_by_county.csv')  # storm, GEOID, vmax_sust,...
wind['GEOID']=wind['GEOID'].astype(int)
wH=wind[wind.storm=='helene'].set_index('GEOID')['vmax_sust']
wM=wind[wind.storm=='milton'].set_index('GEOID')['vmax_sust']

# Milton counties: unit_id == GEOID
mil=prim[prim.hurricane=='milton'].copy()
mil['wind_vmax_sust']=mil['unit_id'].astype(int).map(wM)

# Helene clusters: pop-weighted mean over member counties
ca=pd.read_csv(f'{LR}/helene_100mi/county_cluster_assignments.csv'); ca['GEOID']=ca['GEOID'].astype(int)
ca['w']=ca['GEOID'].map(wH)
def pw(g):
    p=g['total_population']; w=g['w']; m=w.notna()&p.notna()
    return np.average(w[m], weights=p[m]) if m.any() and p[m].sum()>0 else np.nan
cl_wind=ca.groupby('cluster').apply(pw).rename('wind_vmax_sust')
hel=prim[prim.hurricane=='helene'].copy()
hel['wind_vmax_sust']=hel['unit_id'].astype(int).map(cl_wind)

out=pd.concat([mil,hel], ignore_index=True)
print(f'wind merged | missing {out["wind_vmax_sust"].isna().sum()}/{len(out)}')
for s in ['milton','helene']:
    sub=out[out.hurricane==s]
    print(f'  {s}: wind_vmax_sust mean {sub.wind_vmax_sust.mean():.1f}  range [{sub.wind_vmax_sust.min():.1f},{sub.wind_vmax_sust.max():.1f}] | '
          f'precip_7day mean {sub.precip_total_7day.mean():.0f}')

dest=f'{REG}/pooled_dataset_100mi_primary_exposure.csv'
out.to_csv(dest, index=False)
print(f'\nsaved {dest}  ({len(out)} rows, +precip_total_3day/7day, +wind_vmax_sust)')
