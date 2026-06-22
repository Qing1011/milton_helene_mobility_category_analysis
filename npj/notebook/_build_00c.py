"""Builder for 00c_milton_cluster_recompute.ipynb (npj 100-mi package).

Emits a notebook that mirrors, at CLUSTER level for Milton:
  recompute_flows (Helene cluster path) -> local_baseline -> local_metrics -> local_regression
Helene 100mi cluster metrics already exist and are reused; only Milton is recomputed here.
Run:  jupyter nbconvert --to notebook --execute --inplace 00c_milton_cluster_recompute.ipynb
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
def md(s):  cells.append(nbf.v4.new_markdown_cell(s))
def code(s): cells.append(nbf.v4.new_code_cell(s))

md("""# 00c — Milton cluster recompute (flows → baselines → metrics)  ·  MILTON ONLY

Computes **Milton** at cluster level (30 clusters, rule B1) for the **appendix robustness** set. (Helene is the
analog `00e_helene_cluster_recompute`; primary Milton analysis is county-level.) This is a heavy mobility-tensor pass.

Pipeline (Milton clusters only):
1. **Stage A** flows — load the category-summed OD tensor per week, aggregate within / inflow / outflow per cluster
   (`compute_local_flows`) → `flow_ts_{flow}.csv`.
2. **Stage B** SARIMAX baselines per cluster × flow (`recovery_function_v2`, Milton train cut **2024-08-31** to
   avoid Helene contaminating Florida's September) → `baseline_{flow}_{cluster}.csv`.
3. **Stage C** disruption + recovery metrics → `metrics_{flow}.csv` (same schema as `helene_100mi/`).
4. **Stage D** Milton outflow-degeneracy diagnostic.

Outputs → `results/local_level/milton_clustered_100mi/`. The cross-storm clustered pooled dataset is assembled
separately by `build_clustered_pooled.py` (combines this + Helene clusters from 00d/00e).""")

code("""import pandas as pd, numpy as np, h5py, os, sys, time, datetime as dt, warnings
from importlib import reload
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import theilslopes
warnings.filterwarnings('ignore')

# This notebook lives in npj/notebook/ -> one level deeper than the original notebook/.
HURRICANE_OCT = './../../../hurricane_oct/'   # sibling repo: mobility H5 + mobility_function
NOTEBOOK_DIR  = '../../notebook'              # geoid map, ACS, recovery_function_v2
RESULTS       = '../../results'
DATA          = '../../data'
LOCAL_ROOT    = f'{RESULTS}/local_level'
MILTON_DIR    = f'{LOCAL_ROOT}/milton_clustered_100mi'   # cluster assignments already here (from 00b)
REG_OUT       = f'{LOCAL_ROOT}/regression'
os.makedirs(f'{MILTON_DIR}/figures', exist_ok=True)
os.makedirs(REG_OUT, exist_ok=True)

sys.path.append(HURRICANE_OCT)
sys.path.append(os.path.join(HURRICANE_OCT, 'mobility_function'))
sys.path.insert(0, NOTEBOOK_DIR)
from mobility_function import analysis as ma; ma = reload(ma)
from recovery_function_v2 import (prepare_time_series_with_exog, fit_arimax_model, get_predictions_and_ci)

ARIMA_ORDER, SEASONAL_ORDER = (1, 0, 0), (0, 0, 0, 0)
FLOW_TYPES = ['within', 'inflow', 'outflow']
# Milton config (identical to local_baseline.ipynb): train ends 2024-08-31 because Helene (Sep 26) contaminated
# Florida's September mobility, which would bias Milton's counterfactual.
LANDING   = pd.Timestamp('2024-10-09')
TRAIN_END = '2024-08-31'
FC_START, FC_END = '2024-10-03', '2024-10-31'
print('setup ok | Milton landing', LANDING.date(), '| train_end', TRAIN_END, '| forecast', FC_START, '->', FC_END)""")

code("""# ── Date grid (identical to 00 / recompute_flows) ──
def mondays_str(year, start_month=7, end_month=10):
    start = dt.date(year, start_month, 28); end = dt.date(year, end_month, 31)
    cur = start + dt.timedelta(days=(0 - start.weekday()) % 7); out = []
    while cur <= end:
        out.append(cur.strftime('%Y%m%d')); cur += dt.timedelta(days=7)
    return out

mondays_2023, mondays_2024 = mondays_str(2023), mondays_str(2024)
all_mondays = mondays_2023 + mondays_2024
dates_2023 = pd.date_range(start='2023-07-31', periods=len(mondays_2023)*7, freq='D')
dates_2024 = pd.date_range(start='2024-07-29', periods=len(mondays_2024)*7, freq='D')
dates_all  = dates_2023.union(dates_2024)

geo_idx = pd.read_csv(f'{NOTEBOOK_DIR}/geoid_idx_names.csv'); geo_idx['GEOID'] = geo_idx['GEOID'].astype(int)
print(f'Mondays {len(all_mondays)} | days {len(dates_all)} | tensor counties {geo_idx["county_idx"].max()+1}')""")

code('''def compute_local_flows(M_sum, local_idx, all_A_idx):
    """within (self-loop / within-cluster pairs), outflow (local->outside A), inflow (outside A->local).
    Identical to recompute_flows.ipynb."""
    n_total = M_sum.shape[1]
    A_mask = np.zeros(n_total, dtype=bool); A_mask[all_A_idx] = True
    outside_A_mask = ~A_mask
    if len(local_idx) == 1:
        j = local_idx[0]; within = M_sum[:, j, j]
    else:
        within = M_sum[:, local_idx, :][:, :, local_idx].sum(axis=(1, 2))
    outflow = M_sum[:, :, local_idx].sum(axis=2)[:, outside_A_mask].sum(axis=1)
    inflow  = M_sum[:, local_idx, :].sum(axis=1)[:, outside_A_mask].sum(axis=1)
    return within, outflow, inflow''')

code("""# ── Load Milton cluster assignments (from 00b) ──
cluster_df = pd.read_csv(f'{MILTON_DIR}/county_cluster_assignments.csv')
cluster_df['GEOID'] = cluster_df['GEOID'].astype(int)
cluster_df = cluster_df.merge(geo_idx[['GEOID', 'county_idx']], on='GEOID', how='left')
assert cluster_df['county_idx'].notna().all(), 'some Milton counties missing from geo_idx!'
cluster_df['county_idx'] = cluster_df['county_idx'].astype(int)

all_A_idx_milton = cluster_df['county_idx'].values            # whole Milton 100-mi region A
cluster_indices  = {c: g['county_idx'].values for c, g in cluster_df.groupby('cluster')}
n_clusters = len(cluster_indices)
n_singleton = sum(1 for v in cluster_indices.values() if len(v) == 1)
print(f'Milton: {len(cluster_df)} counties -> {n_clusters} clusters ({n_singleton} singletons, '
      f'{n_clusters - n_singleton} merged)')""")

md("## Stage A — heavy tensor pass: Milton cluster flows  ⏳ (loads ~9.4 GB OD tensor per week)")

code("""# ── Aggregate the OD tensor into within / inflow / outflow per Milton cluster ──
m_within = {c: [] for c in cluster_indices}
m_out    = {c: [] for c in cluster_indices}
m_in     = {c: [] for c in cluster_indices}

for k, date_str in enumerate(all_mondays):
    t0 = time.time()
    M = ma.h5py_to_4d_array(f'{HURRICANE_OCT}data/mobility/M_raw_{date_str}.h5')  # (7, 17, 3144, 3144)
    M_sum = M.sum(axis=1); del M                                                   # (7, dest, origin)
    for c, c_idx in cluster_indices.items():
        w, o, i = compute_local_flows(M_sum, c_idx, all_A_idx_milton)
        m_within[c].append(w); m_out[c].append(o); m_in[c].append(i)
    del M_sum
    print(f'  [{k+1:2d}/{len(all_mondays)}] {date_str}  {time.time()-t0:5.0f}s', flush=True)

for c in cluster_indices:
    m_within[c] = np.concatenate(m_within[c])
    m_out[c]    = np.concatenate(m_out[c])
    m_in[c]     = np.concatenate(m_in[c])
print('Stage A done.')""")

code("""# ── Export Milton cluster flow time series + cluster naming ──
for name, ts in [('within', m_within), ('outflow', m_out), ('inflow', m_in)]:
    dfx = pd.DataFrame({str(c): ts[c] for c in sorted(cluster_indices)}, index=dates_all)
    dfx.index.name = 'date'
    dfx.to_csv(f'{MILTON_DIR}/flow_ts_{name}.csv')
    print(f'  saved flow_ts_{name}.csv  {dfx.shape}')

# representative cluster name = largest-population member county (for labelling only)
rep_name = (cluster_df.sort_values('total_population', ascending=False)
            .groupby('cluster').first()['NAME'])
csize = cluster_df.groupby('cluster')['GEOID'].count()
cluster_name = {c: (rep_name[c] if csize[c] == 1 else f'{rep_name[c]} +{csize[c]-1}') for c in cluster_indices}
pd.Series(cluster_name, name='cluster_name').rename_axis('cluster').to_csv(f'{MILTON_DIR}/cluster_names.csv')

# quick sanity: any non-positive baseline-mean outflow (degeneracy flag) ?
print('\\nMean flow per cluster (first few + smallest-outflow):')
sm = pd.DataFrame({'within':[m_within[c].mean() for c in sorted(cluster_indices)],
                   'inflow':[m_in[c].mean() for c in sorted(cluster_indices)],
                   'outflow':[m_out[c].mean() for c in sorted(cluster_indices)]},
                  index=sorted(cluster_indices))
print(sm.sort_values('outflow').head(6).round(0).to_string())""")

md("## Stage B — SARIMAX cluster baselines")

code("""def fit_baselines(hrc_dir, landing, train_end, fc_start, fc_end, make_plots=True):
    fig_dir = f'{hrc_dir}/figures'; os.makedirs(fig_dir, exist_ok=True)
    summary = []
    for ft in FLOW_TYPES:
        flow_df = pd.read_csv(f'{hrc_dir}/flow_ts_{ft}.csv', index_col=0, parse_dates=True)
        dates = flow_df.index
        ok = fail = 0
        for uid in flow_df.columns:
            try:
                y_log, y, X = prepare_time_series_with_exog(flow_df[uid].values, dates)
                res, _, _ = fit_arimax_model(y_log, X, order=ARIMA_ORDER,
                                             seasonal_order=SEASONAL_ORDER, train_2024_end=train_end)
                df_rec, _ = get_predictions_and_ci(res, X, y, forecast_start=fc_start, forecast_end=fc_end)
                df_rec.to_csv(f'{hrc_dir}/baseline_{ft}_{uid}.csv')
                if make_plots:
                    fig, ax = plt.subplots(figsize=(13, 4))
                    ax.plot(df_rec.index, df_rec['y_true'], 'k-', lw=1.3, label='Observed')
                    ax.plot(df_rec.index, df_rec['y_pred'], 'r-', lw=1.3, label='Baseline')
                    ax.fill_between(df_rec.index, df_rec['ci_lower'], df_rec['ci_upper'], color='red', alpha=0.15)
                    ax.axvline(landing, color='blue', ls='--', lw=1.5)
                    ax.set_title(f'Milton cluster {uid} — {ft}', fontweight='bold'); ax.legend(fontsize=8)
                    ax.grid(alpha=0.3); plt.tight_layout()
                    plt.savefig(f'{fig_dir}/baseline_{ft}_{uid}.png', dpi=90, bbox_inches='tight'); plt.close()
                ok += 1
                summary.append({'unit_id': uid, 'flow_type': ft, 'status': 'success',
                                'pred_mean': float(df_rec['y_pred'].mean()),
                                'true_mean': float(df_rec['y_true'].mean())})
            except Exception as e:
                fail += 1; summary.append({'unit_id': uid, 'flow_type': ft, 'status': f'failed: {e}'})
                print(f'    FAIL {ft} cluster {uid}: {e}')
        print(f'  {ft}: {ok} ok, {fail} failed')
    pd.DataFrame(summary).to_csv(f'{hrc_dir}/baseline_summary.csv', index=False)
    return pd.DataFrame(summary)

_ = fit_baselines(MILTON_DIR, LANDING, TRAIN_END, FC_START, FC_END)
print('Stage B done.')""")

md("## Stage C — disruption + recovery metrics")

code('''# ── Metric functions (identical to local_metrics.ipynb / regional_metrics.ipynb) ──
def compute_relative_deviation(df):
    denom = df['y_pred'].replace(0, np.nan) + 1e-12
    return ((df['y_true'] - df['y_pred']) / denom * 100,
            (df['ci_lower'] - df['y_pred']) / denom * 100,
            (df['ci_upper'] - df['y_pred']) / denom * 100)

def compute_largest_drop(rel, landing, window_days=6):
    w = rel.loc[(rel.index >= landing) & (rel.index <= landing + pd.Timedelta(days=window_days))]
    return (None, None) if w.empty else (float(w.min()), w.idxmin())

def compute_outflow_increase(rel, landing, pre=3, post=6):
    w = rel.loc[(rel.index >= landing - pd.Timedelta(days=pre)) & (rel.index <= landing + pd.Timedelta(days=post))]
    return (None, None) if w.empty else (float(w.max()), w.idxmax())

def trend_based_recovery(rel, landing, smooth_window=3, trough_search_days=10):
    rd = rel.rolling(window=smooth_window, center=True, min_periods=1).mean()
    search = rd.loc[(rd.index >= landing) & (rd.index <= landing + pd.Timedelta(days=trough_search_days))]
    if search.empty or search.min() >= 0:
        return {'recovery_days': None, 'trough_date': None, 'recovery_date': None, 'slope': None,
                'intercept': None, 'rd_smooth': rd, 'mono_segment': None}
    trough = search.idxmin(); post = rd.loc[rd.index >= trough]; vals = post.values; mono_end = 1
    for i in range(1, len(vals)):
        if vals[i] >= vals[i-1] - 1e-15: mono_end = i + 1
        else: break
    mono = post.iloc[:mono_end]
    if len(mono) < 2:
        return {'recovery_days': None, 'trough_date': trough, 'recovery_date': None, 'slope': None,
                'intercept': None, 'rd_smooth': rd, 'mono_segment': mono}
    slope, intercept, *_ = theilslopes(mono.values, np.arange(len(mono), dtype=float))
    if slope <= 0:
        return {'recovery_days': None, 'trough_date': trough, 'recovery_date': None, 'slope': float(slope),
                'intercept': float(intercept), 'rd_smooth': rd, 'mono_segment': mono}
    tau = -intercept / slope
    return {'recovery_days': float((trough - landing).days + tau), 'trough_date': trough,
            'recovery_date': trough + pd.to_timedelta(tau, unit='D'), 'slope': float(slope),
            'intercept': float(intercept), 'rd_smooth': rd, 'mono_segment': mono}
print('metric functions defined')''')

code("""# ── Build metrics_{flow}.csv for Milton clusters ──
def build_metrics(hrc_dir, landing, make_plots=True):
    fig_dir = f'{hrc_dir}/figures'
    for ft in FLOW_TYPES:
        files = sorted([f for f in os.listdir(hrc_dir)
                        if f.startswith(f'baseline_{ft}_') and f.endswith('.csv')])
        rows = []
        for bf in files:
            uid = bf.replace(f'baseline_{ft}_', '').replace('.csv', '')
            df = pd.read_csv(f'{hrc_dir}/{bf}', index_col=0, parse_dates=True)
            rel, rel_lo, rel_hi = compute_relative_deviation(df)
            row = {'unit_id': uid}
            dval, ddate = compute_largest_drop(rel, landing)
            row['largest_drop'], row['drop_date'] = dval, ddate
            ival, idate = compute_outflow_increase(rel, landing)
            row['largest_increase'], row['increase_date'] = ival, idate
            rec = None
            if ft in ('within', 'inflow'):
                rec = trend_based_recovery(rel, landing)
                row['recovery_days'] = rec['recovery_days']; row['recovery_date'] = rec['recovery_date']
                row['trough_date'] = rec['trough_date']
                row['slope_pct_per_day'] = rec['slope'] * 100 if rec['slope'] else None
            else:
                row['recovery_days'] = None
            row['total_disruption'] = (abs(dval) * row['recovery_days']
                                       if dval is not None and row.get('recovery_days') is not None else None)
            rows.append(row)
            if make_plots:
                fig, ax = plt.subplots(figsize=(13, 4))
                ax.plot(rel.index, rel.values, 'k-', lw=1.3); ax.axhline(0, color='gray', ls='--', lw=1)
                ax.axvline(landing, color='blue', ls='--', lw=1.5)
                if dval is not None: ax.plot(ddate, dval, 'rv', ms=9)
                if ft == 'outflow' and ival is not None: ax.plot(idate, ival, 'g^', ms=9)
                if rec and rec.get('recovery_date'):
                    ax.axvline(rec['recovery_date'], color='green', ls='--', lw=1.5)
                ax.set_title(f'Milton cluster {uid} — {ft}', fontweight='bold')
                ax.set_ylabel('rel. dev (%)'); ax.grid(alpha=0.3); plt.tight_layout()
                plt.savefig(f'{fig_dir}/metrics_{ft}_{uid}.png', dpi=90, bbox_inches='tight'); plt.close()
        pd.DataFrame(rows).to_csv(f'{hrc_dir}/metrics_{ft}.csv', index=False)
        print(f'  metrics_{ft}.csv: {len(rows)} clusters')

build_metrics(MILTON_DIR, LANDING)
print('Stage C done.')""")

md("""## Stage D — outflow-degeneracy diagnostic (Milton clusters)

The outflow %-metric degenerates where region-leaving baseline flow is tiny (interior/rural units): a mean outflow
baseline < 3% of the storm median makes Δ/baseline explode. Reported here for the Milton clusters. (Cross-storm
pooled-dataset assembly lives in `build_clustered_pooled.py`, NOT in this per-storm notebook.)""")

code("""def outflow_degeneracy(hrc_dir, label):
    mo = pd.read_csv(f'{hrc_dir}/metrics_outflow.csv')
    bs = pd.read_csv(f'{hrc_dir}/baseline_summary.csv')
    of = bs[bs['flow_type'] == 'outflow'][['unit_id', 'pred_mean']].copy()
    of['unit_id'] = of['unit_id'].astype(str); mo['unit_id'] = mo['unit_id'].astype(str)
    d = mo.merge(of, on='unit_id', how='left')
    med = d['pred_mean'].median()
    d['pct_of_median'] = d['pred_mean'] / med * 100
    d['tiny_baseline'] = d['pred_mean'] < 0.03 * med
    flagged = d[d['tiny_baseline']].sort_values('pred_mean')
    print(f'=== {label}: {len(d)} clusters | outflow baseline median {med:,.0f}/day ===')
    print(f'  tiny baseline (<3% median, flag as outflow_degenerate): {int(d.tiny_baseline.sum())}')
    if len(flagged):
        print(flagged[['unit_id', 'pred_mean', 'pct_of_median', 'largest_increase']].round(1).to_string(index=False))
    return d

deg_milton = outflow_degeneracy(MILTON_DIR, 'MILTON (clusters)')""")

code("""print('='*64)
print('00c COMPLETE — Milton cluster metrics written')
print('='*64)
for ft in FLOW_TYPES:
    print(f'  {MILTON_DIR}/metrics_{ft}.csv')
print('\\nCross-storm clustered pooled dataset: run build_clustered_pooled.py')
print('(Helene clusters come from 00d/00e; Milton clusters from this notebook.)')""")

nb["cells"] = cells
nb["metadata"] = {"kernelspec": {"display_name": "geo", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}}

out = "00c_milton_cluster_recompute.ipynb"
nbf.write(nb, out)
print("wrote", out, "with", len(cells), "cells")
