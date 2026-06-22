"""Extract 2024 Helene/Milton county wind exposure from the global TC dataset.
Run with BASE miniconda python (has pyreadr). geo/geo_env lack pyreadr.
  /Users/qing/miniconda3/bin/python extract_wind_2024.py
Willoughby parametric wind (vmax_sust m/s). ADM2_id == shapeID (3231 US counties) -> GEOID.
Output: results/exposure/wind_2024_by_county.csv  (storm, GEOID, vmax_sust, vmax_gust, sust_dur, storm_dist_km)
"""
import pyreadr, pandas as pd, numpy as np, os
ROOT='/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category'
RDS=f'{ROOT}/global_tc_data-main/03_processed-data/global_hurr_dat/global_storm_winds_2024.rds'
FIPS=f'{ROOT}/global_tc_data-main/04_sensitivity/4c_map_shapeID_to_fips/shapeID_fips.csv'
OUT=f'{ROOT}/results/exposure/wind_2024_by_county.csv'; os.makedirs(os.path.dirname(OUT), exist_ok=True)

w=list(pyreadr.read_r(RDS).values())[0]
w=w[w['storm_id'].isin(['Helene-2024','Milton-2024'])].copy()
w['storm']=w['storm_id'].str.split('-').str[0].str.lower()   # helene / milton
fips=pd.read_csv(FIPS)[['shapeID','GEOID']].dropna()
fips['GEOID']=fips['GEOID'].astype(int)
w=w.merge(fips, left_on='ADM2_id', right_on='shapeID', how='inner')   # keep US counties only
print(f'after FIPS join: {len(w)} rows | counties {w.GEOID.nunique()} | storms {sorted(w.storm.unique())}')

# one row per (storm, county): peak wind (max vmax_sust), longest duration, nearest approach
agg=(w.groupby(['storm','GEOID'])
       .agg(vmax_sust=('vmax_sust','max'), vmax_gust=('vmax_gust','max'),
            sust_dur=('sust_dur','max'), storm_dist_km=('storm_dist','min'))
       .reset_index())
agg.to_csv(OUT, index=False)
print(f'saved {OUT}  ({len(agg)} storm-county rows)')
for s in ['helene','milton']:
    sub=agg[agg.storm==s]
    print(f'  {s}: {len(sub)} counties | vmax_sust mean {sub.vmax_sust.mean():.1f} max {sub.vmax_sust.max():.1f} m/s')
