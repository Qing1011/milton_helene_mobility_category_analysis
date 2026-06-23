"""SENSITIVITY (20k baseline-volume cutoff) — figures only: masked flow map + recovery distributions.
Cutoff rule: for each flow, a unit is KEPT iff its baseline-window mean volume (true_mean in
baseline_summary.csv) >= 20,000 visits/day. Applied PER FLOW (a unit can pass within but fail inflow).
Outputs -> results/npj_100mi/sensitivity_20kcut/. Run in geo_env (geopandas). Does NOT touch primary results.
"""
import pathlib, warnings
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from shapely.geometry import LineString
warnings.filterwarnings('ignore')

ROOT = pathlib.Path('/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category')
HO   = pathlib.Path('/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/hurricane_oct')
LL   = ROOT/'results/local_level'
OUT  = ROOT/'results/npj_100mi/sensitivity_20kcut'; OUT.mkdir(parents=True, exist_ok=True)
COUNTY_SHP = HO/'data/county_geo/tl_2023_us_county/tl_2023_us_county.shp'
TRACK_SHP  = {'Helene': HO/'data/storm_track/helene_storm_track.shp',
              'Milton': HO/'data/storm_track/milton_storm_track.shp'}
VOL_FLOOR = 20000.0
HURR = {'Helene': dict(dir='helene_100mi', level='cluster', landfall='2024-09-26'),
        'Milton': dict(dir='milton_100mi', level='county',  landfall='2024-10-09')}
FLOWS = [('outflow','largest_increase','Outflow: largest increase (%)'),
         ('within','largest_drop','Within: largest drop (%)'),
         ('inflow','largest_drop','Inflow: largest drop (%)')]
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
    'font.size':7,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':300})

# ── per-(storm,unit,flow) keep mask from baseline volume ──────────────────────
_v=[]
for hk,cfg in HURR.items():
    bs=pd.read_csv(LL/cfg['dir']/'baseline_summary.csv'); bs['storm']=hk
    _v.append(bs[['storm','unit_id','flow_type','true_mean']])
VOL=pd.concat(_v, ignore_index=True); VOL['unit_id']=VOL['unit_id'].astype(str)
VOL['keep']=(VOL['true_mean']>=VOL_FLOOR).astype(int)
def keep_set(storm, flow):
    s=VOL[(VOL.storm==storm)&(VOL.flow_type==flow)]
    return set(s.loc[s.keep==1,'unit_id'])
print('=== 20k-cutoff survival (kept/total) ===')
for hk in HURR:
    line=' '.join(f'{f}={len(keep_set(hk,f))}' for f,_,_ in FLOWS)
    print(f'  {hk:7s} total={VOL[(VOL.storm==hk)&(VOL.flow_type=="within")].shape[0]:3d}  {line}')

# ══ PART 1: masked flow map ═══════════════════════════════════════════════════
counties=gpd.read_file(COUNTY_SHP)[['GEOID','STATEFP','geometry']].copy()
counties['GEOID']=counties['GEOID'].astype(int); counties=counties.to_crs(epsg=5070)
states=counties.dissolve(by='STATEFP')[['geometry']]
def load_track(p):
    t=gpd.read_file(p); line=LineString(t.geometry.tolist()) if (t.geom_type=='Point').all() else t.unary_union
    return gpd.GeoDataFrame(geometry=[line], crs=t.crs).to_crs(epsg=5070)
tracks={h:load_track(p) for h,p in TRACK_SHP.items()}

def build_layer(hur, flow, col):
    cfg=HURR[hur]; ks=keep_set(hur, flow)
    m=pd.read_csv(LL/cfg['dir']/f'metrics_{flow}.csv')[['unit_id', col]].copy()
    m.columns=['unit_id','value']; m['unit_id']=m['unit_id'].astype(str)
    m.loc[~m['unit_id'].isin(ks),'value']=np.nan          # MASK low-volume units
    if cfg['level']=='county':
        m['GEOID']=m['unit_id'].astype(int)
        return counties.merge(m[['GEOID','value']], on='GEOID', how='right')
    ca=pd.read_csv(LL/cfg['dir']/'county_cluster_assignments.csv')[['GEOID','cluster']]
    ca['GEOID']=ca['GEOID'].astype(int); m['cluster']=m['unit_id'].astype(int)
    d=ca.merge(m[['cluster','value']], on='cluster', how='left')
    return counties.merge(d[['GEOID','cluster','value']], on='GEOID', how='right')

layers={};
for h in HURR:
    for flow,col,_ in FLOWS:
        layers[(h,flow)]=build_layer(h,flow,col)
norms={}
for flow,col,_ in FLOWS:
    vals=pd.concat([layers[(h,flow)]['value'] for h in HURR]).dropna()
    vlim=float(np.nanpercentile(np.abs(vals),98))
    norms[flow]=TwoSlopeNorm(vmin=-vlim,vcenter=0.0,vmax=vlim)
    print(f'{flow:8s} kept-value color cap +/-{vlim:.0f}% (true max |val|={float(np.nanmax(np.abs(vals))):.0f}%)')
CMAP='RdBu'

fig, axes=plt.subplots(2,3,figsize=(7.2,5.4),constrained_layout=True); panel=iter('abcdef')
for r,h in enumerate(HURR):
    is_cluster=HURR[h]['level']=='cluster'
    edge_c,edge_w=('#cfcfcf',0.1) if is_cluster else ('#666',0.15)
    for c,(flow,col,_) in enumerate(FLOWS):
        ax=axes[r,c]; g=layers[(h,flow)]
        minx,miny,maxx,maxy=g.total_bounds; pad=0.05*max(maxx-minx,maxy-miny)
        x0,y0,x1,y1=minx-pad,miny-pad,maxx+pad,maxy+pad
        counties.cx[x0:x1,y0:y1].plot(ax=ax,facecolor='#f2f2f2',edgecolor='white',linewidth=0.25)
        states.cx[x0:x1,y0:y1].boundary.plot(ax=ax,color='#9a9a9a',linewidth=0.4)
        g.plot(ax=ax,column='value',cmap=CMAP,norm=norms[flow],edgecolor=edge_c,linewidth=edge_w,
               missing_kwds={'color':'#dddddd','edgecolor':'#999','linewidth':0.15,'hatch':'///'})
        if is_cluster: g.dissolve(by='cluster').boundary.plot(ax=ax,color='#222',linewidth=0.45)
        tracks[h].plot(ax=ax,color='black',linewidth=1.1)
        ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.set_axis_off()
        ax.text(0.03,0.97,next(panel),transform=ax.transAxes,va='top',ha='left',fontweight='bold',fontsize=10)
        if r==0: ax.set_title(flow.capitalize(),fontweight='bold',fontsize=9,pad=3)
        if c==0: ax.text(-0.05,0.5,f"{h}\n({HURR[h]['landfall']})",transform=ax.transAxes,
                         rotation=90,va='center',ha='center',fontweight='bold',fontsize=9)
for c,(flow,col,label) in enumerate(FLOWS):
    sm=mpl.cm.ScalarMappable(norm=norms[flow],cmap=CMAP); sm.set_array([])
    cb=fig.colorbar(sm,ax=axes[:,c],location='bottom',shrink=0.85,aspect=26,pad=0.01)
    cb.set_label(label,fontsize=7.5); cb.ax.tick_params(labelsize=6.5)
fig.suptitle('Flow maps — 20k baseline-volume cutoff (hatched grey = below cutoff, masked)',
             fontsize=9, fontweight='bold')
for ext in ('png','pdf'): fig.savefig(OUT/f'figure5_flow_maps_20kcut.{ext}', dpi=400, bbox_inches='tight')
print('saved -> figure5_flow_maps_20kcut'); plt.close(fig)

# ══ PART 2: recovery distributions (masked) ═══════════════════════════════════
HURR_COLOR={'helene':'#1f77b4','milton':'#d62728'}
_recs=[]
for hk,cfg in HURR.items():
    for flow in ['within','inflow']:
        m=pd.read_csv(LL/cfg['dir']/f'metrics_{flow}.csv')[['unit_id','recovery_days']].copy()
        m['unit_id']=m['unit_id'].astype(str); ks=keep_set(hk, flow)
        m=m[m['unit_id'].isin(ks)]                                  # MASK low-volume units
        m['hurricane']=hk.lower(); m['flow']=flow; _recs.append(m)
REC=(pd.concat(_recs,ignore_index=True)
       .pivot_table(index=['hurricane','unit_id'],columns='flow',values='recovery_days').reset_index()
       .rename(columns={'within':'recovery_days_within','inflow':'recovery_days_inflow'}))
SPECS=[('recovery_days_within','Within recovery',np.arange(0,18,1)),
       ('recovery_days_inflow','Inflow recovery',np.arange(0,26,2))]
def draw_hist(ax, rec_col, row_label, bins):
    for hk in ['helene','milton']:
        d=REC[REC.hurricane==hk][rec_col].dropna(); mu,sd=d.mean(),d.std()
        ax.hist(d,bins=bins,alpha=0.55,color=HURR_COLOR[hk],edgecolor='white',linewidth=0.4,
                label=f'{hk.title()}  n={len(d)}, $\\mu$={mu:.1f}d, sd={sd:.1f}')
        ax.axvline(mu,color=HURR_COLOR[hk],lw=1.2,ls='--',alpha=0.9)
    ax.set_xlabel(f'{row_label} (days from landfall)'); ax.set_ylabel('Number of units')
    ax.set_title(f'{row_label}: distribution (20k cutoff)',loc='left',fontsize=8,pad=2)
    ax.legend(loc='best',frameon=False,fontsize=6.0); ax.grid(ls=':',lw=0.4,color='#ddd',alpha=0.7); ax.set_axisbelow(True)
fig,axes=plt.subplots(1,2,figsize=(7.0,3.2))
for ax,(col,lab,bins) in zip(axes,SPECS): draw_hist(ax,col,lab,bins)
fig.tight_layout()
for ext in ('pdf','png'): fig.savefig(OUT/f'figure4_recovery_distribution_20kcut.{ext}', dpi=300, bbox_inches='tight')
print('saved -> figure4_recovery_distribution_20kcut'); plt.close()

rows=[]
for col,lab,_ in SPECS:
    for hk in ['helene','milton']:
        d=REC[REC.hurricane==hk][col].dropna()
        rows.append(dict(flow=col.replace('recovery_days_',''),hurricane=hk,n=len(d),
            mean=d.mean(),sd=d.std(),median=d.median(),p25=d.quantile(.25),p75=d.quantile(.75)))
pd.DataFrame(rows).round(3).to_csv(OUT/'figure4_recovery_stats_20kcut.csv', index=False)
# persist the mask itself for the regression step + provenance
VOL.to_csv(OUT/'volume_keep_mask_20k.csv', index=False)
print('saved -> figure4_recovery_stats_20kcut.csv, volume_keep_mask_20k.csv')
print('FIGS COMPLETE ->', OUT)
