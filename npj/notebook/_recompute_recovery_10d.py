"""Recompute disruption + recovery metrics from SAVED baselines with a configurable
trough-search window (default 10 days; was 7).

This faithfully reproduces the Stage-C metric logic shared by:
  - npj/notebook/_build_00e.py        (Helene clusters    -> helene_100mi/)
  - notebook/local_metrics.ipynb      (Milton counties    -> milton_100mi/)
  - npj/notebook/_build_00c.py        (Milton clusters    -> milton_clustered_100mi/, appendix)
  - npj/notebook/00_regional_flows_100mi.ipynb cell 9 (regional -> regional_metrics_summary_100mi.csv)

No SARIMAX re-fitting: the trough window only affects the recovery step, so we read the
existing per-unit / per-category baseline CSVs and rewrite the metrics_*.csv files.

Usage:
  python3 _recompute_recovery_10d.py --verify   # regenerate at window=7, compare to current (no overwrite)
  python3 _recompute_recovery_10d.py --window 10 # overwrite metrics with 10-day window
"""
import argparse, os, pathlib, sys
import numpy as np, pandas as pd
from scipy.stats import theilslopes

ROOT = pathlib.Path(__file__).resolve().parents[2]   # .../4_hurricane_category
LL   = ROOT / 'results' / 'local_level'
REG  = ROOT / 'results' / 'npj_100mi' / 'regional_data'

# ---- metric functions (identical to the four producers) -------------------------------
def compute_relative_deviation(df):
    denom = df['y_pred'].replace(0, np.nan) + 1e-12
    return (df['y_true'] - df['y_pred']) / denom * 100

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
        return {'recovery_days': None, 'trough_date': None, 'recovery_date': None, 'slope': None, 'intercept': None}
    trough = search.idxmin(); post = rd.loc[rd.index >= trough]; vals = post.values; mono_end = 1
    for i in range(1, len(vals)):
        if vals[i] >= vals[i-1] - 1e-15: mono_end = i + 1
        else: break
    mono = post.iloc[:mono_end]
    if len(mono) < 2:
        return {'recovery_days': None, 'trough_date': trough, 'recovery_date': None, 'slope': None, 'intercept': None}
    slope, intercept, *_ = theilslopes(mono.values, np.arange(len(mono), dtype=float))
    if slope <= 0:
        return {'recovery_days': None, 'trough_date': trough, 'recovery_date': None, 'slope': float(slope), 'intercept': float(intercept)}
    tau = -intercept / slope
    return {'recovery_days': float((trough - landing).days + tau), 'trough_date': trough,
            'recovery_date': trough + pd.to_timedelta(tau, unit='D'), 'slope': float(slope), 'intercept': float(intercept)}

FLOW_TYPES = ['within', 'inflow', 'outflow']

# ---- local metrics (one row per unit) -------------------------------------------------
def build_local(hrc_dir, landing, window):
    out = {}
    for ft in FLOW_TYPES:
        files = sorted([f for f in os.listdir(hrc_dir) if f.startswith(f'baseline_{ft}_') and f.endswith('.csv')])
        rows = []
        for bf in files:
            uid = bf.replace(f'baseline_{ft}_', '').replace('.csv', '')
            df = pd.read_csv(hrc_dir / bf, index_col=0, parse_dates=True)
            rel = compute_relative_deviation(df); row = {'unit_id': uid}
            dval, ddate = compute_largest_drop(rel, landing); row['largest_drop'], row['drop_date'] = dval, ddate
            ival, idate = compute_outflow_increase(rel, landing); row['largest_increase'], row['increase_date'] = ival, idate
            if ft in ('within', 'inflow'):
                rec = trend_based_recovery(rel, landing, trough_search_days=window)
                row['recovery_days'] = rec['recovery_days']; row['recovery_date'] = rec['recovery_date']
                row['trough_date'] = rec['trough_date']
                row['slope_pct_per_day'] = rec['slope'] * 100 if rec['slope'] else None
            else:
                row['recovery_days'] = None; row['recovery_date'] = None; row['trough_date'] = None; row['slope_pct_per_day'] = None
            row['total_disruption'] = abs(dval) * row['recovery_days'] if dval is not None and row.get('recovery_days') is not None else None
            rows.append(row)
        out[ft] = pd.DataFrame(rows, columns=['unit_id','largest_drop','drop_date','largest_increase','increase_date',
                                              'recovery_days','recovery_date','trough_date','slope_pct_per_day','total_disruption'])
    return out

# ---- regional summary (one row per hurricane x flow x category) ------------------------
GROUP_DISPLAY = {'Travel':'Travel','Work_and_Professional':'Work & Professional','Health':'Health',
                 'Education':'Education','Retail_and_Leisure':'Retail & Leisure',
                 'Urban_Government':'Urban Government','Utilities':'Utilities'}
# order matches 00_regional_flows_100mi.ipynb cell 3 (milton before helene) so rewritten rows keep the same order
REG_LANDING = {'milton': pd.Timestamp('2024-10-09'), 'helene': pd.Timestamp('2024-09-26')}

def build_regional(window):
    rows = []
    for hrc, landing in REG_LANDING.items():
        d = REG / hrc
        for ft in FLOW_TYPES:
            for safe in GROUP_DISPLAY:
                p = d / f'baseline_{ft}_{safe}.csv'
                if not p.exists(): continue
                df = pd.read_csv(p, index_col=0, parse_dates=True)
                rel = compute_relative_deviation(df)
                row = {'hurricane': hrc, 'flow_type': ft, 'category': GROUP_DISPLAY[safe]}
                dv, _ = compute_largest_drop(rel, landing); row['largest_drop'] = dv
                iv, _ = compute_outflow_increase(rel, landing); row['largest_increase'] = iv
                if ft in ('within', 'inflow'):
                    rec = trend_based_recovery(rel, landing, trough_search_days=window)
                    row['recovery_days'] = rec.get('recovery_days')
                    row['slope_pct_per_day'] = (rec['slope'] * 100) if rec.get('slope') else None
                else:
                    row['recovery_days'] = None; row['slope_pct_per_day'] = None
                rows.append(row)
    return pd.DataFrame(rows, columns=['hurricane','flow_type','category','largest_drop','largest_increase','recovery_days','slope_pct_per_day'])

LOCAL_DIRS = {'helene_100mi': pd.Timestamp('2024-09-26'),
              'milton_100mi': pd.Timestamp('2024-10-09'),
              'milton_clustered_100mi': pd.Timestamp('2024-10-09')}

def num_compare(new_df, old_path, cols):
    """numeric closeness check vs an existing file"""
    old = pd.read_csv(old_path)
    msgs = []
    for c in cols:
        if c not in old.columns or c not in new_df.columns: continue
        a = pd.to_numeric(old[c], errors='coerce').to_numpy()
        b = pd.to_numeric(new_df[c], errors='coerce').to_numpy()
        if len(a) != len(b):
            msgs.append(f"{c}: LEN {len(a)}!={len(b)}"); continue
        both_nan = np.isnan(a) & np.isnan(b)
        ok = both_nan | np.isclose(a, b, rtol=1e-9, atol=1e-9, equal_nan=True)
        if not ok.all():
            msgs.append(f"{c}: {(~ok).sum()} mismatches (max abs diff {np.nanmax(np.abs(a-b)):.4g})")
    return msgs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', type=int, default=10)
    ap.add_argument('--verify', action='store_true', help='regenerate at window=7 and compare to current files; no overwrite')
    args = ap.parse_args()

    if args.verify:
        print("=== VERIFY: regenerate at window=7, compare numerically to current files (NO overwrite) ===")
        allok = True
        for d, landing in LOCAL_DIRS.items():
            res = build_local(LL / d, landing, window=7)
            for ft, df in res.items():
                p = LL / d / f'metrics_{ft}.csv'
                if not p.exists(): print(f"  {d}/{ft}: (no existing file)"); continue
                msgs = num_compare(df, p, ['largest_drop','largest_increase','recovery_days','slope_pct_per_day','total_disruption'])
                print(f"  {d}/metrics_{ft}.csv: {'OK' if not msgs else 'DIFF -> '+'; '.join(msgs)}")
                allok &= not msgs
        reg = build_regional(window=7)
        p = REG / 'regional_metrics_summary_100mi.csv'
        msgs = num_compare(reg, p, ['largest_drop','largest_increase','recovery_days','slope_pct_per_day'])
        print(f"  regional_metrics_summary_100mi.csv: {'OK' if not msgs else 'DIFF -> '+'; '.join(msgs)}")
        allok &= not msgs
        print("=== VERIFY", "PASSED" if allok else "FAILED", "===")
        sys.exit(0 if allok else 1)

    print(f"=== REGENERATE metrics with trough_search_days={args.window} (OVERWRITING) ===")
    for d, landing in LOCAL_DIRS.items():
        res = build_local(LL / d, landing, window=args.window)
        for ft, df in res.items():
            p = LL / d / f'metrics_{ft}.csv'
            df.to_csv(p, index=False)
            nv = df['recovery_days'].notna().sum() if 'recovery_days' in df else 0
            print(f"  wrote {p.relative_to(ROOT)}  ({len(df)} units, recovery non-NaN={nv})")
    reg = build_regional(window=args.window)
    p = REG / 'regional_metrics_summary_100mi.csv'
    reg.to_csv(p, index=False)
    print(f"  wrote {p.relative_to(ROOT)}  ({len(reg)} rows)")
    print("=== DONE ===")

if __name__ == '__main__':
    main()
