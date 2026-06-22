"""Builder for 00d_helene_clustering.ipynb (npj 100-mi) — Helene local clustering.
Faithful port of notebook/helene_spatial_clustering.ipynb (DISTANCE_CUTOFF=100), repointed to absolute paths.
487 counties -> 101 NCHS-homogeneous, spatially-contiguous clusters (merge-all: agglomerative-ward within each
NCHS code toward ~20-county clusters, or connected components if more disconnected pieces than k).
Writes helene_100mi/county_cluster_assignments.csv (the PRIMARY Helene units) + appendix maps.
geo env. The Helene analog of 00b (Milton clustering).
"""
import nbformat as nbf
nb=nbf.v4.new_notebook(); cells=[]
md=lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code=lambda s: cells.append(nbf.v4.new_code_cell(s))

md("""# 00d - Helene local clustering (merge-all within NCHS, 100-mi)

Helene's 100-mi region is **487 counties, 59% rural** (median pop ~25k) → per-county mobility baselines are
unstable, so counties are merged into **NCHS-homogeneous, spatially-contiguous clusters**. Within each NCHS code:
agglomerative (Ward) clustering on centroids with a Queen-contiguity constraint toward ~20-county clusters, OR
connected components where a code has more disconnected pieces than target clusters. → **101 clusters**.
(Faithful port of `notebook/helene_spatial_clustering.ipynb`; the Helene analog of `00b_milton_clustering`.)

Outputs:
- `results/local_level/helene_100mi/county_cluster_assignments.csv` (GEOID->cluster) — PRIMARY Helene units
- `results/helene_clustering_100mi/cluster_summary_nchs_geo.csv`
- `results/npj_100mi/figureB_nchs_helene.{pdf,png}` (appendix rural-urban code map)
- `results/npj_100mi/figureC_clusters_helene.{pdf,png}` (appendix cluster-illustration map)""")

code("""import os, warnings
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib as mpl, matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.sparse import lil_matrix
from scipy.sparse.csgraph import connected_components
from libpysal.weights import Queen
from shapely.geometry import LineString
warnings.filterwarnings('ignore')
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
    'font.size':7,'pdf.fonttype':42,'ps.fonttype':42})

ROOT='/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category'
HO='/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/hurricane_oct'
COUNTY_LIST=f'{ROOT}/results/local_level/helene_100mi/counties_geoid_cut_100.txt'
ACS=f'{ROOT}/notebook/acs_socioeconomic_v2.csv'
NCHS_CSV=f'{ROOT}/data/NCHS Urban-Rural Classification Scheme for Counties.csv'
COUNTY_SHP=f'{HO}/data/county_geo/tl_2023_us_county/tl_2023_us_county.shp'
TRACK_SHP=f'{HO}/data/storm_track/helene_storm_track.shp'
DROP_CSV=f'{ROOT}/results/helene/largest_drop_within.csv'  # optional, carried in assignment (not used for clustering)
OUT_LOCAL=f'{ROOT}/results/local_level/helene_100mi'
OUT_CLUSTERING=f'{ROOT}/results/helene_clustering_100mi'
OUT_NPJ=f'{ROOT}/results/npj_100mi'
for d in (OUT_LOCAL, f'{OUT_CLUSTERING}/figures', OUT_NPJ): os.makedirs(d, exist_ok=True)
NCHS_LABELS={1:'Large central metro',2:'Large fringe metro',3:'Medium metro',4:'Small metro',5:'Micropolitan',6:'Noncore (rural)'}
TARGET_CLUSTER_SIZE=20; MIN_CLUSTER_SIZE=1
print('setup ok')""")

code("""# ── Load counties + ACS + (optional) drop + geometry + track; distance-to-track ──
helene_geoids=[int(x.strip()) for x in open(COUNTY_LIST) if x.strip()]
acs_df=pd.read_csv(ACS); acs_df['GEOID']=acs_df['GEOID'].astype(int)
try:
    drop_df=pd.read_csv(DROP_CSV); drop_df['GEOID']=drop_df['GEOID'].astype(int)
except FileNotFoundError:
    drop_df=pd.DataFrame(columns=['GEOID','largest_drop'])
counties_gdf=gpd.read_file(COUNTY_SHP); counties_gdf['GEOID']=counties_gdf['GEOID'].astype(int)
gdf=counties_gdf[counties_gdf['GEOID'].isin(helene_geoids)].copy()
gdf=gdf.merge(acs_df[['GEOID','total_population','median_household_income','pct_no_vehicle','insurance_coverage_pct']],on='GEOID',how='left')
gdf=gdf.merge(drop_df[['GEOID','largest_drop']],on='GEOID',how='left') if 'largest_drop' in drop_df.columns else gdf.assign(largest_drop=np.nan)
gdf=gdf.to_crs(epsg=5070)
trk=gpd.read_file(TRACK_SHP).to_crs(epsg=5070)
track_line=LineString(trk.geometry.tolist()) if (trk.geometry.geom_type.iloc[0]=='Point') else trk.unary_union
gdf['centroid']=gdf.geometry.centroid
gdf['dist_to_track_mi']=gdf['centroid'].apply(lambda pt: track_line.distance(pt))/1000.0/1.60934
n_before=len(gdf)
gdf=gdf.dropna(subset=['median_household_income']).reset_index(drop=True)
print(f'counties: {n_before} -> {len(gdf)} with income')""")

code("""# ── Queen contiguity (+ connect islands to nearest centroid) ──
w_queen=Queen.from_dataframe(gdf)
islands=[i for i,v in w_queen.neighbors.items() if len(v)==0]
print(f'Queen: n={w_queen.n}, mean nbrs={w_queen.mean_neighbors:.1f}, islands={len(islands)}')
# NCHS
nchs=pd.read_csv(NCHS_CSV, encoding='utf-8-sig')
nchs['GEOID']=nchs['Location'].astype(int); nchs['nchs_code']=nchs['2023 Code'].str.extract(r'(\\d)').astype(int)
nchs['nchs_label']=nchs['2023 Code']
gdf=gdf.merge(nchs[['GEOID','nchs_code','nchs_label']],on='GEOID',how='left')
print('missing NCHS:', gdf['nchs_code'].isna().sum())
print(gdf['nchs_label'].value_counts().sort_index().to_string())""")

code("""# ── Stratified spatial clustering within each NCHS code (verbatim method) ──
cluster_id=0; gdf['cluster']=-1; cluster_meta=[]
for nchs_code in sorted(gdf['nchs_code'].unique()):
    subset=gdf[gdf['nchs_code']==nchs_code].copy(); n=len(subset); nm=NCHS_LABELS.get(nchs_code,f'Code {nchs_code}')
    if n<=MIN_CLUSTER_SIZE:
        gdf.loc[subset.index,'cluster']=cluster_id
        cluster_meta.append({'cluster':cluster_id,'nchs_code':nchs_code,'nchs_label':nm,'n_counties':n}); cluster_id+=1; continue
    k=max(1,round(n/TARGET_CLUSTER_SIZE))
    if k==1:
        gdf.loc[subset.index,'cluster']=cluster_id
        cluster_meta.append({'cluster':cluster_id,'nchs_code':nchs_code,'nchs_label':nm,'n_counties':n}); cluster_id+=1; continue
    idx_map={o:j for j,o in enumerate(subset.index)}; sub_conn=lil_matrix((n,n),dtype=int)
    for i in subset.index:
        if i in w_queen.neighbors:
            for j in w_queen.neighbors[i]:
                if j in idx_map: sub_conn[idx_map[i],idx_map[j]]=1; sub_conn[idx_map[j],idx_map[i]]=1
    sub_conn=sub_conn.tocsr()
    ncomp,comp_labels=connected_components(sub_conn,directed=False)
    if ncomp>k:
        for comp in range(ncomp):
            cm=comp_labels==comp; gdf.loc[subset.index[cm],'cluster']=cluster_id
            cluster_meta.append({'cluster':cluster_id,'nchs_code':nchs_code,'nchs_label':nm,'n_counties':int(cm.sum())}); cluster_id+=1
        continue
    sub_cent=np.array([(pt.x,pt.y) for pt in subset.geometry.centroid]); sub_z=StandardScaler().fit_transform(sub_cent)
    try:
        lab=AgglomerativeClustering(n_clusters=k,connectivity=sub_conn,linkage='ward').fit_predict(sub_z)
    except Exception:
        lab=AgglomerativeClustering(n_clusters=k,linkage='ward').fit_predict(sub_z)
    for sk in range(k):
        m=lab==sk; gdf.loc[subset.index[m],'cluster']=cluster_id
        cluster_meta.append({'cluster':cluster_id,'nchs_code':nchs_code,'nchs_label':nm,'n_counties':int(m.sum())}); cluster_id+=1
total_clusters=cluster_id
assert (gdf['cluster']>=0).all(), 'unassigned!'
assert (gdf.groupby('cluster')['nchs_code'].nunique()==1).all(), 'mixed-NCHS cluster!'
print(f'Helene: {len(gdf)} counties -> {total_clusters} clusters; NCHS-homogeneous OK')""")

code("""# ── Cluster summary + export assignment (schema matches existing helene_100mi) ──
for col in ['white_pop','pop_25plus','bachelors_plus_count']:
    if col not in gdf.columns: gdf=gdf.merge(acs_df[['GEOID',col]],on='GEOID',how='left')
summ=gdf.groupby('cluster').agg(n_counties=('GEOID','count'),total_pop=('total_population','sum'),
    total_white=('white_pop','sum'),total_pop25=('pop_25plus','sum'),total_bachelors=('bachelors_plus_count','sum'),
    median_income=('median_household_income','median'),mean_dist_to_track=('dist_to_track_mi','mean'),
    median_pct_no_vehicle=('pct_no_vehicle','median'),median_insurance=('insurance_coverage_pct','median'),
    nchs_code=('nchs_code','first'),median_drop=('largest_drop','median')).round(1)
summ['cluster_pct_white']=(summ['total_white']/summ['total_pop']*100).round(1)
summ['cluster_pct_bachelors']=(summ['total_bachelors']/summ['total_pop25']*100).round(1)
summ['nchs_label']=summ['nchs_code'].map(NCHS_LABELS)
summ.sort_values(['nchs_code','cluster']).to_csv(f'{OUT_CLUSTERING}/cluster_summary_nchs_geo.csv')

export=gdf[['GEOID','NAME','cluster','nchs_code','nchs_label','median_household_income','total_population',
            'dist_to_track_mi','largest_drop']].copy().sort_values(['cluster','GEOID']).reset_index(drop=True)
export.to_csv(f'{OUT_CLUSTERING}/county_cluster_assignments.csv', index=False)
export.to_csv(f'{OUT_LOCAL}/county_cluster_assignments.csv', index=False)
with open(f'{OUT_LOCAL}/counties_geoid_cut_100.txt','w') as f: f.write('\\n'.join(str(g) for g in helene_geoids))
print(f'{total_clusters} clusters, {len(export)} counties -> {OUT_LOCAL}/county_cluster_assignments.csv')
print(export.groupby('nchs_code')['cluster'].nunique().rename('n_clusters').to_string())""")

code("""# ── Appendix maps: NCHS-by-county (figureB) + cluster-outline (figureC) ──
cmap=plt.cm.get_cmap('RdYlGn_r',6); trk_gdf=gpd.GeoDataFrame(geometry=[track_line],crs='EPSG:5070')
# (B) NCHS per-county
figA,axA=plt.subplots(figsize=(4.6,5.0))
gdf.plot(column='nchs_code',cmap=cmap,vmin=1,vmax=6,edgecolor='white',linewidth=0.15,ax=axA,
         legend=True,legend_kwds={'label':'NCHS code (1=large metro, 6=rural)','shrink':0.6})
trk_gdf.plot(ax=axA,color='black',linewidth=1.0)
_b=gdf.total_bounds; _p=0.05*max(_b[2]-_b[0],_b[3]-_b[1]); axA.set_xlim(_b[0]-_p,_b[2]+_p); axA.set_ylim(_b[1]-_p,_b[3]+_p)
axA.set_title('Helene — rural-urban (NCHS) code by county (100 mi)',fontsize=8,loc='left'); axA.set_axis_off()
for ext in ('pdf','png'): figA.savefig(f'{OUT_NPJ}/figureB_nchs_helene.{ext}',dpi=300,bbox_inches='tight')
plt.close(figA)
# (C) cluster-outline: counties thin, cluster boundaries thick (no per-cluster labels — 101 too dense)
num=gdf.select_dtypes(include=[np.number]).columns.tolist()
diss=gdf[[c for c in num if c!='cluster']+['cluster','geometry']].dissolve(by='cluster',aggfunc='median')
figC,axC=plt.subplots(figsize=(4.6,5.0))
gdf.plot(column='nchs_code',cmap=cmap,vmin=1,vmax=6,edgecolor='white',linewidth=0.12,ax=axC,
         legend=True,legend_kwds={'label':'NCHS code (1=metro, 6=rural)','shrink':0.6})
diss.boundary.plot(ax=axC,color='black',linewidth=0.7)
trk_gdf.plot(ax=axC,color='red',linewidth=1.0)
axC.set_xlim(_b[0]-_p,_b[2]+_p); axC.set_ylim(_b[1]-_p,_b[3]+_p)
axC.set_title(f'Helene — {total_clusters} clusters (counties outlined by cluster, 100 mi)',fontsize=8,loc='left'); axC.set_axis_off()
for ext in ('pdf','png'): figC.savefig(f'{OUT_NPJ}/figureC_clusters_helene.{ext}',dpi=300,bbox_inches='tight')
plt.close(figC)
print('saved figureB_nchs_helene + figureC_clusters_helene')""")

nb['cells']=cells
nb['metadata']={'kernelspec':{'display_name':'geo','language':'python','name':'python3'},'language_info':{'name':'python'}}
nbf.write(nb,'00d_helene_clustering.ipynb'); print('wrote 00d_helene_clustering.ipynb', len(cells),'cells')
