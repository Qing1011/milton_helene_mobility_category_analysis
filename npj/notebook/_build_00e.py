"""Builder for 00e_helene_cluster_recompute.ipynb (npj 100-mi) — Helene cluster recompute.
Helene analog of 00c: aggregate the OD tensor per Helene cluster (101) -> SARIMAX baselines -> metrics.
Faithful port of recompute_flows(Helene path)+local_baseline+local_metrics. Reads the cluster assignment from 00d.
Heavy mobility-tensor pass (487 counties x 31 weeks x ~9.4GB). geo env.
"""
import nbformat as nbf
nb=nbf.v4.new_notebook(); cells=[]
md=lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code=lambda s: cells.append(nbf.v4.new_code_cell(s))

md("""# 00e — Helene cluster recompute (flows → baselines → metrics)  ·  HELENE ONLY

Helene analog of `00c`. Aggregates the OD tensor per **Helene cluster (101)** → SARIMAX baselines → metrics, for the
**PRIMARY** Helene units. Reads the cluster assignment produced by `00d_helene_clustering`. Heavy tensor pass
(487 counties × 31 weeks).

Pipeline (Helene clusters):
1. **Stage A** flows — per-cluster within / inflow / outflow (`compute_local_flows`) → `flow_ts_{flow}.csv`.
2. **Stage B** SARIMAX baselines (Helene train cut **2024-09-19** = 7 d pre-landfall) → `baseline_{flow}_{cluster}.csv`.
3. **Stage C** disruption + recovery metrics → `metrics_{flow}.csv`.
4. **Stage D** Helene outflow-degeneracy diagnostic.

Outputs → `results/local_level/helene_100mi/`.""")

code("""import pandas as pd, numpy as np, h5py, os, sys, time, datetime as dt, warnings
from importlib import reload
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import theilslopes
warnings.filterwarnings('ignore')

HURRICANE_OCT='./../../../hurricane_oct/'; NOTEBOOK_DIR='../../notebook'; RESULTS='../../results'
LOCAL_ROOT=f'{RESULTS}/local_level'; HELENE_DIR=f'{LOCAL_ROOT}/helene_100mi'
os.makedirs(f'{HELENE_DIR}/figures', exist_ok=True)
sys.path.append(HURRICANE_OCT); sys.path.append(os.path.join(HURRICANE_OCT,'mobility_function')); sys.path.insert(0, NOTEBOOK_DIR)
from mobility_function import analysis as ma; ma=reload(ma)
from recovery_function_v2 import (prepare_time_series_with_exog, fit_arimax_model, get_predictions_and_ci)
ARIMA_ORDER, SEASONAL_ORDER=(1,0,0),(0,0,0,0); FLOW_TYPES=['within','inflow','outflow']
# Helene config (identical to local_baseline.ipynb): train ends 7 d pre-landfall.
LANDING=pd.Timestamp('2024-09-26'); TRAIN_END='2024-09-19'; FC_START='2024-09-20'; FC_END='2024-10-31'
print('setup ok | Helene landing', LANDING.date(), '| train_end', TRAIN_END, '| forecast', FC_START, '->', FC_END)""")

code("""# ── Date grid + geoid index ──
def mondays_str(year, start_month=7, end_month=10):
    start=dt.date(year,start_month,28); end=dt.date(year,end_month,31)
    cur=start+dt.timedelta(days=(0-start.weekday())%7); out=[]
    while cur<=end: out.append(cur.strftime('%Y%m%d')); cur+=dt.timedelta(days=7)
    return out
mondays_2023, mondays_2024 = mondays_str(2023), mondays_str(2024); all_mondays=mondays_2023+mondays_2024
dates_2023=pd.date_range(start='2023-07-31',periods=len(mondays_2023)*7,freq='D')
dates_2024=pd.date_range(start='2024-07-29',periods=len(mondays_2024)*7,freq='D')
dates_all=dates_2023.union(dates_2024)
geo_idx=pd.read_csv(f'{NOTEBOOK_DIR}/geoid_idx_names.csv'); geo_idx['GEOID']=geo_idx['GEOID'].astype(int)
print(f'Mondays {len(all_mondays)} | days {len(dates_all)}')""")

code('''def compute_local_flows(M_sum, local_idx, all_A_idx):
    """within (within-cluster pairs), outflow (local->outside A), inflow (outside A->local). From recompute_flows."""
    n_total=M_sum.shape[1]; A_mask=np.zeros(n_total,dtype=bool); A_mask[all_A_idx]=True; outside=~A_mask
    if len(local_idx)==1:
        j=local_idx[0]; within=M_sum[:,j,j]
    else:
        within=M_sum[:,local_idx,:][:,:,local_idx].sum(axis=(1,2))
    outflow=M_sum[:,:,local_idx].sum(axis=2)[:,outside].sum(axis=1)
    inflow=M_sum[:,local_idx,:].sum(axis=1)[:,outside].sum(axis=1)
    return within, outflow, inflow''')

code("""# ── Load Helene cluster assignments (from 00d) ──
cluster_df=pd.read_csv(f'{HELENE_DIR}/county_cluster_assignments.csv'); cluster_df['GEOID']=cluster_df['GEOID'].astype(int)
cluster_df=cluster_df.merge(geo_idx[['GEOID','county_idx']],on='GEOID',how='left')
assert cluster_df['county_idx'].notna().all(), 'some Helene counties missing from geo_idx!'
cluster_df['county_idx']=cluster_df['county_idx'].astype(int)
all_A_idx_helene=cluster_df['county_idx'].values
cluster_indices={c:g['county_idx'].values for c,g in cluster_df.groupby('cluster')}
print(f'Helene: {len(cluster_df)} counties -> {len(cluster_indices)} clusters')""")

md("## Stage A — heavy tensor pass: Helene cluster flows  ⏳ (loads ~9.4 GB OD tensor per week)")

code("""h_within={c:[] for c in cluster_indices}; h_out={c:[] for c in cluster_indices}; h_in={c:[] for c in cluster_indices}
for k,date_str in enumerate(all_mondays):
    t0=time.time()
    M=ma.h5py_to_4d_array(f'{HURRICANE_OCT}data/mobility/M_raw_{date_str}.h5'); M_sum=M.sum(axis=1); del M
    for c,c_idx in cluster_indices.items():
        w,o,i=compute_local_flows(M_sum,c_idx,all_A_idx_helene); h_within[c].append(w); h_out[c].append(o); h_in[c].append(i)
    del M_sum
    print(f'  [{k+1:2d}/{len(all_mondays)}] {date_str}  {time.time()-t0:5.0f}s', flush=True)
for c in cluster_indices:
    h_within[c]=np.concatenate(h_within[c]); h_out[c]=np.concatenate(h_out[c]); h_in[c]=np.concatenate(h_in[c])
print('Stage A done.')""")

code("""for name,ts in [('within',h_within),('outflow',h_out),('inflow',h_in)]:
    dfx=pd.DataFrame({str(c):ts[c] for c in sorted(cluster_indices)}, index=dates_all); dfx.index.name='date'
    dfx.to_csv(f'{HELENE_DIR}/flow_ts_{name}.csv'); print(f'  saved flow_ts_{name}.csv {dfx.shape}')""")

md("## Stage B — SARIMAX cluster baselines")

code("""def fit_baselines(hrc_dir, landing, train_end, fc_start, fc_end, make_plots=True):
    fig_dir=f'{hrc_dir}/figures'; os.makedirs(fig_dir, exist_ok=True); summary=[]
    for ft in FLOW_TYPES:
        flow_df=pd.read_csv(f'{hrc_dir}/flow_ts_{ft}.csv', index_col=0, parse_dates=True); dates=flow_df.index; ok=fail=0
        for uid in flow_df.columns:
            try:
                y_log,y,X=prepare_time_series_with_exog(flow_df[uid].values, dates)
                res,_,_=fit_arimax_model(y_log,X,order=ARIMA_ORDER,seasonal_order=SEASONAL_ORDER,train_2024_end=train_end)
                df_rec,_=get_predictions_and_ci(res,X,y,forecast_start=fc_start,forecast_end=fc_end)
                df_rec.to_csv(f'{hrc_dir}/baseline_{ft}_{uid}.csv')
                if make_plots:
                    fig,ax=plt.subplots(figsize=(13,4))
                    ax.plot(df_rec.index,df_rec['y_true'],'k-',lw=1.3,label='Observed'); ax.plot(df_rec.index,df_rec['y_pred'],'r-',lw=1.3,label='Baseline')
                    ax.fill_between(df_rec.index,df_rec['ci_lower'],df_rec['ci_upper'],color='red',alpha=0.15); ax.axvline(landing,color='blue',ls='--',lw=1.5)
                    ax.set_title(f'Helene cluster {uid} — {ft}',fontweight='bold'); ax.legend(fontsize=8); ax.grid(alpha=0.3); plt.tight_layout()
                    plt.savefig(f'{fig_dir}/baseline_{ft}_{uid}.png',dpi=90,bbox_inches='tight'); plt.close()
                ok+=1; summary.append({'unit_id':uid,'flow_type':ft,'status':'success','pred_mean':float(df_rec['y_pred'].mean()),'true_mean':float(df_rec['y_true'].mean())})
            except Exception as e:
                fail+=1; summary.append({'unit_id':uid,'flow_type':ft,'status':f'failed: {e}'}); print(f'    FAIL {ft} cluster {uid}: {e}')
        print(f'  {ft}: {ok} ok, {fail} failed')
    pd.DataFrame(summary).to_csv(f'{hrc_dir}/baseline_summary.csv', index=False); return pd.DataFrame(summary)
_=fit_baselines(HELENE_DIR, LANDING, TRAIN_END, FC_START, FC_END); print('Stage B done.')""")

md("## Stage C — disruption + recovery metrics")

code('''def compute_relative_deviation(df):
    denom=df['y_pred'].replace(0,np.nan)+1e-12
    return ((df['y_true']-df['y_pred'])/denom*100,(df['ci_lower']-df['y_pred'])/denom*100,(df['ci_upper']-df['y_pred'])/denom*100)
def compute_largest_drop(rel,landing,window_days=6):
    w=rel.loc[(rel.index>=landing)&(rel.index<=landing+pd.Timedelta(days=window_days))]; return (None,None) if w.empty else (float(w.min()),w.idxmin())
def compute_outflow_increase(rel,landing,pre=3,post=6):
    w=rel.loc[(rel.index>=landing-pd.Timedelta(days=pre))&(rel.index<=landing+pd.Timedelta(days=post))]; return (None,None) if w.empty else (float(w.max()),w.idxmax())
def trend_based_recovery(rel,landing,smooth_window=3,trough_search_days=10):
    rd=rel.rolling(window=smooth_window,center=True,min_periods=1).mean()
    search=rd.loc[(rd.index>=landing)&(rd.index<=landing+pd.Timedelta(days=trough_search_days))]
    if search.empty or search.min()>=0: return {'recovery_days':None,'trough_date':None,'recovery_date':None,'slope':None,'intercept':None,'rd_smooth':rd,'mono_segment':None}
    trough=search.idxmin(); post=rd.loc[rd.index>=trough]; vals=post.values; mono_end=1
    for i in range(1,len(vals)):
        if vals[i]>=vals[i-1]-1e-15: mono_end=i+1
        else: break
    mono=post.iloc[:mono_end]
    if len(mono)<2: return {'recovery_days':None,'trough_date':trough,'recovery_date':None,'slope':None,'intercept':None,'rd_smooth':rd,'mono_segment':mono}
    slope,intercept,*_=theilslopes(mono.values,np.arange(len(mono),dtype=float))
    if slope<=0: return {'recovery_days':None,'trough_date':trough,'recovery_date':None,'slope':float(slope),'intercept':float(intercept),'rd_smooth':rd,'mono_segment':mono}
    tau=-intercept/slope
    return {'recovery_days':float((trough-landing).days+tau),'trough_date':trough,'recovery_date':trough+pd.to_timedelta(tau,unit='D'),'slope':float(slope),'intercept':float(intercept),'rd_smooth':rd,'mono_segment':mono}
print('metric functions defined')''')

code("""def build_metrics(hrc_dir, landing, make_plots=True):
    fig_dir=f'{hrc_dir}/figures'
    for ft in FLOW_TYPES:
        files=sorted([f for f in os.listdir(hrc_dir) if f.startswith(f'baseline_{ft}_') and f.endswith('.csv')]); rows=[]
        for bf in files:
            uid=bf.replace(f'baseline_{ft}_','').replace('.csv',''); df=pd.read_csv(f'{hrc_dir}/{bf}',index_col=0,parse_dates=True)
            rel,_,_=compute_relative_deviation(df); row={'unit_id':uid}
            dval,ddate=compute_largest_drop(rel,landing); row['largest_drop'],row['drop_date']=dval,ddate
            ival,idate=compute_outflow_increase(rel,landing); row['largest_increase'],row['increase_date']=ival,idate
            rec=None
            if ft in ('within','inflow'):
                rec=trend_based_recovery(rel,landing); row['recovery_days']=rec['recovery_days']; row['recovery_date']=rec['recovery_date']
                row['trough_date']=rec['trough_date']; row['slope_pct_per_day']=rec['slope']*100 if rec['slope'] else None
            else: row['recovery_days']=None
            row['total_disruption']=abs(dval)*row['recovery_days'] if dval is not None and row.get('recovery_days') is not None else None
            rows.append(row)
            if make_plots:
                fig,ax=plt.subplots(figsize=(13,4)); ax.plot(rel.index,rel.values,'k-',lw=1.3); ax.axhline(0,color='gray',ls='--',lw=1); ax.axvline(landing,color='blue',ls='--',lw=1.5)
                if dval is not None: ax.plot(ddate,dval,'rv',ms=9)
                if ft=='outflow' and ival is not None: ax.plot(idate,ival,'g^',ms=9)
                if rec and rec.get('recovery_date'): ax.axvline(rec['recovery_date'],color='green',ls='--',lw=1.5)
                ax.set_title(f'Helene cluster {uid} — {ft}',fontweight='bold'); ax.set_ylabel('rel. dev (%)'); ax.grid(alpha=0.3); plt.tight_layout()
                plt.savefig(f'{fig_dir}/metrics_{ft}_{uid}.png',dpi=90,bbox_inches='tight'); plt.close()
        pd.DataFrame(rows).to_csv(f'{hrc_dir}/metrics_{ft}.csv', index=False); print(f'  metrics_{ft}.csv: {len(rows)} clusters')
build_metrics(HELENE_DIR, LANDING); print('Stage C done.')""")

md("## Stage D — outflow-degeneracy diagnostic (Helene clusters)")

code("""mo=pd.read_csv(f'{HELENE_DIR}/metrics_outflow.csv'); bs=pd.read_csv(f'{HELENE_DIR}/baseline_summary.csv')
of=bs[bs['flow_type']=='outflow'][['unit_id','pred_mean']].copy(); of['unit_id']=of['unit_id'].astype(str); mo['unit_id']=mo['unit_id'].astype(str)
d=mo.merge(of,on='unit_id',how='left'); med=d['pred_mean'].median(); d['pct_of_median']=d['pred_mean']/med*100
d['tiny_baseline']=d['pred_mean']<0.03*med
flagged=d[d['tiny_baseline']].sort_values('pred_mean')
print(f'=== HELENE (clusters): {len(d)} clusters | outflow baseline median {med:,.0f}/day ===')
print(f'  tiny baseline (<3% median, flag as outflow_degenerate): {int(d.tiny_baseline.sum())}')
if len(flagged): print(flagged[['unit_id','pred_mean','pct_of_median','largest_increase']].round(1).to_string(index=False))
print('\\n00e COMPLETE — Helene cluster metrics written to', HELENE_DIR)
print('Cross-storm clustered pooled dataset: run build_clustered_pooled.py')""")

nb['cells']=cells
nb['metadata']={'kernelspec':{'display_name':'geo','language':'python','name':'python3'},'language_info':{'name':'python'}}
nbf.write(nb,'00e_helene_cluster_recompute.ipynb'); print('wrote 00e_helene_cluster_recompute.ipynb', len(cells),'cells')
