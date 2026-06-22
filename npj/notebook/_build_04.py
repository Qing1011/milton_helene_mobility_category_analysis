"""Builder for 04_local_recovery_dist.ipynb — recovery-time histograms (figure5b_recovery_descriptive style).
Overlaid Helene (blue) + Milton (red) histograms of per-unit recovery_days, within + inflow, on the PRIMARY units
(Milton 34 counties + Helene 101 clusters). geo env.
"""
import nbformat as nbf
nb=nbf.v4.new_notebook(); cells=[]
md=lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code=lambda s: cells.append(nbf.v4.new_code_cell(s))

md("""# 04 — Local recovery-time distribution (histograms)

Overlaid histograms of per-unit `recovery_days` (Helene blue, Milton red), **within + inflow only** (outflow is an
evacuation surge — no recovery). Style matches `figure5b_recovery_descriptive` (panel b, col 0): α=0.55, white
edges, dashed per-storm mean lines, μ/sd box. Units = primary (Milton **34 counties** + Helene **101 clusters**).""")

code("""import pathlib, warnings
import numpy as np, pandas as pd
import matplotlib as mpl, matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
    'font.size':8,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
    'legend.fontsize':7,'axes.linewidth':0.6,'axes.spines.top':False,'axes.spines.right':False,
    'savefig.dpi':300,'savefig.bbox':'tight','pdf.fonttype':42,'ps.fonttype':42})
ROOT=pathlib.Path('/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category')
LL=ROOT/'results/local_level'; OUT=ROOT/'results/npj_100mi'; OUT.mkdir(parents=True,exist_ok=True)
# recovery_days read DIRECTLY from the per-storm metrics: Helene clusters from 00d/00e (helene_100mi/),
# Milton counties from milton_100mi/. (No pooled-CSV intermediary.)
HURR_DIR={'helene':'helene_100mi','milton':'milton_100mi'}
_recs=[]
for hk,d in HURR_DIR.items():
    for flow in ['within','inflow']:
        m=pd.read_csv(LL/d/f'metrics_{flow}.csv')[['unit_id','recovery_days']].copy(); m['hurricane']=hk; m['flow']=flow; _recs.append(m)
POOL=(pd.concat(_recs,ignore_index=True)
        .pivot_table(index=['hurricane','unit_id'],columns='flow',values='recovery_days').reset_index()
        .rename(columns={'within':'recovery_days_within','inflow':'recovery_days_inflow'}))
HURR_COLOR={'helene':'#1f77b4','milton':'#d62728'}
SPECS=[('recovery_days_within','Within recovery',np.arange(0,18,1)),
       ('recovery_days_inflow','Inflow recovery',np.arange(0,26,2))]   # 10-day trough window: inflow max ~24d (was ~65 at 7d)
print('units', POOL.hurricane.value_counts().to_dict())""")

code("""def draw_hist(ax, rec_col, row_label, bins):
    # mu/sd folded into the legend labels (no separate stats box -> no overlap at small panel size)
    for hk in ['helene','milton']:
        d=POOL[POOL.hurricane==hk][rec_col].dropna()
        mu,sd=d.mean(),d.std()
        ax.hist(d, bins=bins, alpha=0.55, color=HURR_COLOR[hk], edgecolor='white', linewidth=0.4,
                label=f'{hk.title()}  n={len(d)}, $\\mu$={mu:.1f}d, sd={sd:.1f}')
        ax.axvline(mu, color=HURR_COLOR[hk], lw=1.2, ls='--', alpha=0.9)
        ax.axvspan(mu-sd, mu+sd, ymin=0.0, ymax=0.04, color=HURR_COLOR[hk], alpha=0.35, zorder=0)
    ax.set_xlabel(f'{row_label} (days from landfall)'); ax.set_ylabel('Number of units')
    ax.set_title(f'{row_label}: distribution', loc='left', fontsize=8, pad=2)
    ax.legend(loc='best', frameon=False, fontsize=6.0)
    ax.grid(ls=':', lw=0.4, color='#dddddd', alpha=0.7); ax.set_axisbelow(True)

# combined 1x2 panel (within | inflow)
fig,axes=plt.subplots(1,2,figsize=(7.0,3.2))
for ax,(col,lab,bins) in zip(axes,SPECS): draw_hist(ax,col,lab,bins)
fig.tight_layout()
for ext in ('pdf','png'): fig.savefig(OUT/f'figure4_recovery_distribution.{ext}', dpi=300, bbox_inches='tight')
print('saved figure4_recovery_distribution'); plt.close()

# also one-panel-one-file
for col,lab,bins in SPECS:
    f,ax=plt.subplots(figsize=(3.6,3.0)); draw_hist(ax,col,lab,bins); f.tight_layout()
    key=col.replace('recovery_days_','')
    for ext in ('pdf','png'): f.savefig(OUT/f'figure4_recovery_{key}.{ext}', dpi=300, bbox_inches='tight')
    plt.close()
print('saved per-flow panels')""")

code("""# figure-ready stats CSV
rows=[]
for col,lab,_ in SPECS:
    for hk in ['helene','milton']:
        d=POOL[POOL.hurricane==hk][col].dropna()
        rows.append(dict(flow=col.replace('recovery_days_',''), hurricane=hk, n=len(d),
            mean=d.mean(), sd=d.std(), median=d.median(), p25=d.quantile(.25), p75=d.quantile(.75)))
pd.DataFrame(rows).round(3).to_csv(OUT/'figure4_recovery_stats.csv', index=False)
print('saved figure4_recovery_stats.csv')""")

nb['cells']=cells
nb['metadata']={'kernelspec':{'display_name':'geo','language':'python','name':'python3'},'language_info':{'name':'python'}}
OUT_NB='04_local_recovery_time distribution.ipynb'  # user's filename
nbf.write(nb, OUT_NB); print('wrote', OUT_NB, len(cells),'cells')
