"""Builder for 06b_spatial_drivers.ipynb — Moran's I + LISA (BOTH storms) + GWR (Helene only).
Revisions: (1) drop outflow_degenerate units from the OUTFLOW DV; (2) clip storm track to the study-area bbox
(no full inland/oceanic tail); (3) LISA cluster maps for BOTH storms so Milton is visible (Milton GWR is not
identifiable). DV choropleths are NOT produced here — the flow-DV maps are Figure 5 (05_local_flow_maps); the
standalone 06b dvmaps were redundant and dropped. geo env (esda/libpysal/mgwr/geopandas).
"""
import nbformat as nbf
nb=nbf.v4.new_notebook(); cells=[]
md=lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code=lambda s: cells.append(nbf.v4.new_code_cell(s))

md("""# 06b — Spatial drivers: Moran's I + LISA (both storms) → GWR (Helene only)

Units = Helene **101 clusters** + Milton **34 counties**. **Outflow DV drops `outflow_degenerate` units** (Clinch/Glades).
Track is **clipped to the study-area extent**. Both storms get LISA cluster maps; GWR runs for
**Helene only** (Milton GWR not identifiable at n=34). **DV choropleths are NOT produced here** — the flow-DV maps
are Figure 5 (`05_local_flow_maps`). Outputs → `results/npj_100mi/spatial/`.""")

code("""import os, warnings
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, ListedColormap
from shapely.geometry import LineString, box
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from libpysal.weights import Queen, KNN
from esda.moran import Moran, Moran_Local
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
warnings.filterwarnings('ignore')
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
    'font.size':8,'savefig.dpi':300,'savefig.bbox':'tight','pdf.fonttype':42,'ps.fonttype':42})
ROOT='/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category'
HO='/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/hurricane_oct'
REG=f'{ROOT}/results/local_level/regression'
OUT=f'{ROOT}/results/npj_100mi/spatial'; os.makedirs(f'{OUT}/figures', exist_ok=True)
COUNTY_SHP=f'{HO}/data/county_geo/tl_2023_us_county/tl_2023_us_county.shp'
POOL=pd.read_csv(f'{REG}/pooled_dataset_100mi_primary_exposure.csv')

DV_TO_COL={'Largest drop (within)':'largest_drop_within','Largest drop (inflow)':'largest_drop_inflow',
           'Outflow surge':'largest_increase_outflow'}
OUTFLOW_COL='largest_increase_outflow'
FULL_FEATURES=['median_household_income','pct_no_vehicle','pct_white','nchs_code','total_population',
               'pop_density','dist_to_track_mi','insurance_coverage_pct','precip_total_7day','wind_vmax_sust','is_coastal']
GWR_FEATURES=['median_household_income','pct_white','insurance_coverage_pct','dist_to_track_mi']
HURR_LAB={'helene':'Helene','milton':'Milton'}
def dv_subset(gdf, dv_col):
    '''drop degenerate units for the outflow DV only'''
    return gdf[gdf['outflow_degenerate']==0] if dv_col==OUTFLOW_COL else gdf
print('rows', len(POOL))""")

code("""# ── Geometry per storm (EPSG:5070) + track CLIPPED to study-area bbox ──
counties=gpd.read_file(COUNTY_SHP); counties['GEOID']=counties['GEOID'].astype(int)
def helene_gdf():
    sub=POOL[POOL.hurricane=='helene'].copy(); sub['cluster']=sub['unit_id'].astype(int)
    ca=pd.read_csv(f'{ROOT}/results/local_level/helene_100mi/county_cluster_assignments.csv'); ca['GEOID']=ca['GEOID'].astype(int)
    g=counties[counties.GEOID.isin(ca.GEOID)].merge(ca[['GEOID','cluster']],on='GEOID').to_crs(5070)
    g=g.dissolve(by='cluster')[['geometry']].reset_index().merge(sub,on='cluster',how='left')
    c=g.geometry.centroid; g['cx'],g['cy']=c.x,c.y; return g
def milton_gdf():
    sub=POOL[POOL.hurricane=='milton'].copy(); sub['GEOID']=sub['unit_id'].astype(int)
    g=counties[counties.GEOID.isin(sub.GEOID)].to_crs(5070).merge(sub,on='GEOID',how='right')
    c=g.geometry.centroid; g['cx'],g['cy']=c.x,c.y; return g
GDF={'helene':helene_gdf(),'milton':milton_gdf()}
def track_clip(hk, gdf, buf=25000):
    t=gpd.read_file(f'{HO}/data/storm_track/{hk}_storm_track.shp').to_crs(5070)
    line=LineString(t.geometry.tolist()) if (t.geom_type=='Point').all() else t.unary_union
    minx,miny,maxx,maxy=gdf.total_bounds
    clipped=line.intersection(box(minx-buf,miny-buf,maxx+buf,maxy+buf))
    return gpd.GeoDataFrame(geometry=[clipped], crs='EPSG:5070')
TRACK={hk:track_clip(hk,GDF[hk]) for hk in GDF}
for hk in GDF: print(f'{hk}: {len(GDF[hk])} units | track clipped len {TRACK[hk].geometry.length.iloc[0]/1609:.0f} mi')""")

code("""# ── Moran's I: each DV (raw) + OLS residual; Queen + KNN(4); per storm; outflow drops degenerate ──
rows=[]
for hk,g0 in GDF.items():
    for dv_lab,dv in DV_TO_COL.items():
        g=dv_subset(g0, dv).dropna(subset=FULL_FEATURES+[dv]).reset_index(drop=True)
        wq=Queen.from_dataframe(g); wk=KNN.from_dataframe(g,k=4)
        Xz=StandardScaler().fit_transform(g[FULL_FEATURES]); X=sm.add_constant(Xz)
        y=g[dv].values; resid=sm.OLS(y,X).fit().resid
        for wlab,w in [('Queen',wq),('KNN4',wk)]:
            for tgt,vals in [('raw',y),('ols_resid',resid)]:
                try:
                    mi=Moran(vals,w,permutations=999)
                    rows.append(dict(storm=hk,dv=dv_lab,target=tgt,weight=wlab,
                        moran_I=round(float(mi.I),4),p_sim=round(float(mi.p_sim),4),n=len(g)))
                except Exception:
                    rows.append(dict(storm=hk,dv=dv_lab,target=tgt,weight=wlab,moran_I=np.nan,p_sim=np.nan,n=len(g)))
moran=pd.DataFrame(rows); moran.to_csv(f'{OUT}/morans_i_100mi.csv',index=False)
print('saved morans_i_100mi.csv'); print(moran[moran.p_sim<0.10].to_string(index=False))""")

code("""# ── LISA (local Moran) cluster maps where global Moran's I (raw, KNN4) is significant ──
# (DV choropleths intentionally NOT produced here — the flow-DV maps are Figure 5 / 05_local_flow_maps.)
def dvkey(dv): return dv.split('(')[-1].strip(') ').replace(' ','_') if '(' in dv else dv.replace(' ','_')
sig=moran[(moran.target=='raw')&(moran.weight=='KNN4')&(moran.p_sim<0.05)][['storm','dv']].drop_duplicates()
LISA_COL={1:'#d7191c',2:'#abd9e9',3:'#2c7bb6',4:'#fdae61',0:'#dddddd'}  # 1HH 2LH 3LL 4HL 0 ns
LISA_LAB={1:'High-High',2:'Low-High',3:'Low-Low',4:'High-Low',0:'n.s.'}
for _,r in sig.iterrows():
    hk,dv_lab=r['storm'],r['dv']; dv=DV_TO_COL[dv_lab]
    g=dv_subset(GDF[hk],dv).dropna(subset=[dv]).reset_index(drop=True)
    w=KNN.from_dataframe(g,k=4); w.transform='r'
    lm=Moran_Local(g[dv].values,w,permutations=999,seed=42)
    q=np.where(lm.p_sim<0.05, lm.q, 0)
    g=g.copy(); g['lisa']=q
    import matplotlib.patches as mpatches
    fig,ax=plt.subplots(figsize=(6.2,5.4)); handles=[]
    for code,c in LISA_COL.items():
        sub=g[g.lisa==code]
        if len(sub):
            sub.plot(ax=ax,color=c,edgecolor='black',linewidth=0.2)
            handles.append(mpatches.Patch(facecolor=c,edgecolor='black',label=f'{LISA_LAB[code]} ({len(sub)})'))
    TRACK[hk].plot(ax=ax,color='black',linewidth=1.6)
    ax.legend(handles=handles,loc='lower left',fontsize=6,frameon=True,title='LISA quadrant'); ax.set_axis_off()
    ax.set_title(f'{HURR_LAB[hk]} — {dv_lab}: LISA clusters (KNN k=4, p<0.05)',fontsize=9,fontweight='bold')
    plt.tight_layout()
    for ext in ('pdf','png'): fig.savefig(f'{OUT}/figures/figure6b_lisa_{hk}_{dvkey(dv)}.{ext}',dpi=300,bbox_inches='tight')
    plt.close()
print('saved LISA maps for', len(sig), 'significant storm x DV combos:', list(zip(sig.storm,sig.dv)))""")

code("""# ── GWR — Helene only (adaptive bisquare, AICc); outflow drops degenerate ──
def ols_aicc(m,n):
    k=m.df_model+1; return m.aic+(2*k*(k+1))/max(n-k-1,1)
gwr_models={}; diag=[]
for dv_lab,dv in DV_TO_COL.items():
    g=dv_subset(GDF['helene'],dv).dropna(subset=GWR_FEATURES+[dv]).reset_index(drop=True)
    coords=list(zip(g['cx'].values,g['cy'].values)); Xz=StandardScaler().fit_transform(g[GWR_FEATURES])
    y=g[[dv]].values; n=len(g); olsm=sm.OLS(y,sm.add_constant(Xz)).fit()
    bw_min=max(len(GWR_FEATURES)+1+3,8); bw_max=n-1
    sel=Sel_BW(coords,y,Xz,fixed=False,kernel='bisquare')
    bw=sel.search(criterion='AICc',bw_min=bw_min,bw_max=bw_max)
    try:
        m=GWR(coords,y,Xz,bw,fixed=False,kernel='bisquare').fit()
        nsta=m.spatial_variability(sel,n_iters=200)
        gwr_models[dv]={'m':m,'g':g,'bw':bw}
        diag.append(dict(storm='helene',dv=dv_lab,n=n,bw=int(bw),OLS_AICc=round(ols_aicc(olsm,n),2),
            GWR_AICc=round(m.aicc,2),OLS_R2=round(olsm.rsquared,3),GWR_R2=round(float(m.R2),3),
            GWR_adjR2=round(float(m.adj_R2),3),ENP=round(float(m.ENP),1),
            localR2_min=round(float(m.localR2.min()),3),localR2_max=round(float(m.localR2.max()),3),
            nonstationary_vars=';'.join(f for f,p in zip(GWR_FEATURES,nsta[1:]) if p<0.10)))
        print(f'  {dv_lab}: n={n} bw={bw} GWR_AICc={m.aicc:.1f} (OLS {ols_aicc(olsm,n):.1f}) R2={m.R2:.2f} localR2[{m.localR2.min():.2f},{m.localR2.max():.2f}]')
    except Exception as e:
        diag.append(dict(storm='helene',dv=dv_lab,n=n,bw=int(bw),note=f'GWR failed: {e}')); print('  FAIL',dv_lab,e)
pd.DataFrame(diag).to_csv(f'{OUT}/gwr_diagnostics_100mi.csv',index=False); print('saved gwr_diagnostics_100mi.csv')""")

code("""# ── Export Helene GWR local coefficients + maps (clipped track) ──
out=[]
for dv_lab,dv in DV_TO_COL.items():
    if dv not in gwr_models: continue
    m=gwr_models[dv]['m']; g=gwr_models[dv]['g']
    for i in range(len(g)):
        rec=dict(storm='helene',dv=dv_lab,cluster=int(g['cluster'].iloc[i]),local_R2=float(m.localR2[i]))
        for k,fn in enumerate(['intercept']+GWR_FEATURES):
            rec[f'beta_{fn}']=float(m.params[i,k]); rec[f'tval_{fn}']=float(m.tvalues[i,k])
        out.append(rec)
pd.DataFrame(out).to_csv(f'{OUT}/gwr_local_coefs_helene_100mi.csv',index=False)
for dv_lab,dv in DV_TO_COL.items():
    if dv not in gwr_models: continue
    m=gwr_models[dv]['m']; gp=gwr_models[dv]['g'].copy(); gp['local_R2']=m.localR2.flatten()
    fig,ax=plt.subplots(figsize=(6.4,5.4))
    gp.plot(column='local_R2',cmap='viridis',legend=True,edgecolor='black',linewidth=0.2,ax=ax,
            legend_kwds={'label':'Local R²','shrink':0.6})
    TRACK['helene'].plot(ax=ax,color='red',linewidth=1.6)
    ax.set_title(f'Helene GWR local R² — {dv_lab} (N={len(gp)})',fontsize=9,fontweight='bold'); ax.set_axis_off()
    plt.tight_layout()
    for ext in ('pdf','png'): fig.savefig(f'{OUT}/figures/figure6b_gwr_localR2_{dv.split("(")[-1].strip(") ").replace(" ","_")}.{ext}',dpi=300,bbox_inches='tight')
    plt.close()
    fig,axes=plt.subplots(1,len(GWR_FEATURES),figsize=(3.2*len(GWR_FEATURES),3.4))
    for j,fn in enumerate(GWR_FEATURES):
        ax=axes[j]; gp[f'b_{fn}']=m.params[:,j+1]; v=max(np.abs(gp[f'b_{fn}']).max(),1e-6)
        gp.plot(column=f'b_{fn}',cmap='RdBu_r',vmin=-v,vmax=v,legend=True,edgecolor='black',linewidth=0.2,ax=ax,legend_kwds={'shrink':0.55})
        TRACK['helene'].plot(ax=ax,color='black',linewidth=1.0); ax.set_title(f'β {fn}',fontsize=7,fontweight='bold'); ax.set_axis_off()
    fig.suptitle(f'Helene GWR local β — {dv_lab}',fontsize=9,fontweight='bold'); plt.tight_layout()
    for ext in ('pdf','png'): fig.savefig(f'{OUT}/figures/figure6b_gwr_beta_{dv.split("(")[-1].strip(") ").replace(" ","_")}.{ext}',dpi=300,bbox_inches='tight')
    plt.close()
print('saved GWR local coefs + maps')""")

code("""# ── Milton GWR non-identifiability probe (n=34) ──
g=GDF['milton'].dropna(subset=GWR_FEATURES+['largest_drop_within']).reset_index(drop=True)
coords=list(zip(g['cx'].values,g['cy'].values)); Xm=StandardScaler().fit_transform(g[GWR_FEATURES]); y=g[['largest_drop_within']].values; nm=len(g)
try:
    sel=Sel_BW(coords,y,Xm,fixed=False,kernel='bisquare'); bw=sel.search(criterion='AICc',bw_min=max(len(GWR_FEATURES)+4,8),bw_max=nm-1)
    mm=GWR(coords,y,Xm,bw,fixed=False,kernel='bisquare').fit(); frac=bw/nm
    note=dict(storm='milton',n=nm,bw=int(bw),bw_frac_of_n=round(frac,2),ENP=round(float(mm.ENP),1),
              verdict=('near-global (GWR not identifiable)' if frac>=0.9 else 'local'))
    print(f'Milton GWR probe: N={nm}, bw={bw} ({frac:.0%} of n), ENP={mm.ENP:.1f} -> {note["verdict"]}')
except Exception as e:
    note=dict(storm='milton',n=nm,note=f'not identifiable: {e}'); print('Milton GWR not identifiable:',e)
pd.DataFrame([note]).to_csv(f'{OUT}/milton_gwr_probe_100mi.csv',index=False)
print('06b COMPLETE -> results/npj_100mi/spatial/')""")

nb['cells']=cells
nb['metadata']={'kernelspec':{'display_name':'geo','language':'python','name':'python3'},'language_info':{'name':'python'}}
nbf.write(nb,'06b_spatial_drivers.ipynb'); print('wrote 06b_spatial_drivers.ipynb', len(cells),'cells')
