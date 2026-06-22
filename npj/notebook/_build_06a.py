"""Builder for 06a_global_drivers.ipynb — per-storm OLS + Bayesian driver regression (npj 100-mi).
Reuses the model design of notebook/figure5_supp_bayesian_independent.ipynb, repointed to the
100-mi PRIMARY+EXPOSURE dataset (Helene 101 clusters + Milton 34 counties), 11 predictors
(10 ACS/geo + wind_vmax_sust + precip_total_7day), 3 flow DVs, separate per storm, Bayesian primary.
Runs in geo_env (pymc/bambi/arviz). nbconvert --execute.
"""
import nbformat as nbf
nb=nbf.v4.new_notebook(); cells=[]
md=lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code=lambda s: cells.append(nbf.v4.new_code_cell(s))

md("""# 06a — Global drivers (per-storm OLS → Bayesian), 100-mi cluster/county primary

Separate **per-storm** regression (NOT pooled), **Bayesian primary / OLS supplementary**, on
`pooled_dataset_100mi_primary_exposure.csv` (Helene **101 clusters** + Milton **34 counties**).
**3 flow DVs**: within drop, inflow drop, outflow surge. **11 z-scored predictors** incl. physical exposure
(`wind_vmax_sust`, `precip_total_7day`). Weakly-informative priors (Gelman 2.5·sd_y). Compute-once: posterior +
OLS tables written to `results/npj_100mi/drivers/`; forest panels are one-file-each (PDF+PNG).
**Bayesian R²** (Gelman et al. 2019 posterior R²; median + 95% CrI) → `bayes_r2_100mi.csv`, annotated on every Bayesian forest panel.
Env: **geo_env** (pymc/bambi/arviz).""")

code("""import pathlib, warnings
import numpy as np, pandas as pd
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import bambi as bmb, arviz as az
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings('ignore')
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
    'font.size':8,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
    'legend.fontsize':7,'axes.linewidth':0.6,'axes.spines.top':False,'axes.spines.right':False,
    'savefig.dpi':300,'savefig.bbox':'tight','pdf.fonttype':42,'ps.fonttype':42})

ROOT=pathlib.Path('/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category')
REG=ROOT/'results/local_level/regression'
OUT=ROOT/'results/npj_100mi/drivers'; OUT.mkdir(parents=True, exist_ok=True)
def save_panel(fig, name):
    for ext in ('pdf','png'): fig.savefig(OUT/f'{name}.{ext}', dpi=300, bbox_inches='tight')
    print('saved', name)

POOL=pd.read_csv(REG/'pooled_dataset_100mi_primary_exposure.csv')
print('rows', len(POOL), '| by storm', POOL.hurricane.value_counts().to_dict())""")

code("""DV_TO_COL={'Largest drop (within)':'largest_drop_within',
           'Largest drop (inflow)':'largest_drop_inflow',
           'Outflow surge':'largest_increase_outflow'}
DV_ORDER=list(DV_TO_COL)

# 11-predictor spec: ACS/geo (10) + physical exposure wind; precip already among continuous.
CONTINUOUS=['median_household_income','pct_no_vehicle','pct_white','nchs_code','total_population',
            'pop_density','dist_to_track_mi','insurance_coverage_pct','precip_total_7day','wind_vmax_sust']
BINARY=['is_coastal']
MODEL_FEATURES=CONTINUOUS+BINARY
DISPLAY_PREDICTORS=['dist_to_track_mi','wind_vmax_sust','precip_total_7day','median_household_income',
                    'insurance_coverage_pct','pct_white','pct_no_vehicle']
PREDICTOR_LABEL={'dist_to_track_mi':'Distance to track','wind_vmax_sust':'Max wind (vmax)',
    'precip_total_7day':'Precip (7-day)','median_household_income':'Median income',
    'insurance_coverage_pct':'Insurance %','pct_white':'% White','pct_no_vehicle':'% No vehicle',
    'nchs_code':'NCHS code','total_population':'Population','pop_density':'Pop density','is_coastal':'Coastal'}
HURR_COLOR={'helene':'#1f77b4','milton':'#d62728'}
DV_COLOR={'Largest drop (within)':'#2c7fb8','Largest drop (inflow)':'#7fcdbb','Outflow surge':'#d95f0e'}

# z-score continuous globally (binary left as-is) -> POOL_Z
POOL_Z=POOL.copy()
sc=StandardScaler()
POOL_Z[CONTINUOUS]=sc.fit_transform(POOL[CONTINUOUS])
N={h:int((POOL.hurricane==h).sum()) for h in ['helene','milton']}
print('predictors', len(MODEL_FEATURES), '| n', N)""")

code("""# ── Per-storm Bayesian fits (bambi); weakly-informative priors scaled to DV sd ──
# OUTFLOW FIX: drop outflow_degenerate units from the OUTFLOW DV only (Clinch +12595% = ~30x leverage,
# Helene outflow sd 1251->42 without it). within/inflow keep ALL units.
OUTFLOW_COL='largest_increase_outflow'
def fit_df(hk,dv_col):
    d=POOL_Z[POOL_Z.hurricane==hk]
    if dv_col==OUTFLOW_COL: d=d[d['outflow_degenerate']==0]
    return d.copy()
PRIOR_WIDTH_FACTOR=2.5
def make_priors(dv_col, df):
    sd_y=df[dv_col].std(); width=PRIOR_WIDTH_FACTOR*sd_y
    pr={f:bmb.Prior('Normal',mu=0,sigma=width) for f in MODEL_FEATURES}
    pr['Intercept']=bmb.Prior('Normal',mu=0,sigma=10*sd_y); pr['sigma']=bmb.Prior('HalfNormal',sigma=sd_y)
    return pr
SAMPLE=dict(draws=2000,tune=1500,chains=4,target_accept=0.95,random_seed=42,progressbar=False)
RHS=' + '.join(MODEL_FEATURES)
fits={}
for hk in ['helene','milton']:
    for dv_lab,dv_col in DV_TO_COL.items():
        sub=fit_df(hk,dv_col); excl=N[hk]-len(sub)
        print(f'-- fit {hk:6s} {dv_lab} (n={len(sub)}{f", -{excl} degenerate" if excl else ""}) --', flush=True)
        m=bmb.Model(f'{dv_col} ~ {RHS}', sub, family='gaussian', priors=make_priors(dv_col, sub))
        idata=m.fit(**SAMPLE)
        fits[(hk,dv_lab)]={'idata':idata,'model':m,'n':len(sub)}
print('all fits done')""")

code("""# ── MCMC diagnostics ──
diag=[]
print(f'{"storm":<8}{"DV":<24}{"R-hat":>7}{"ESS":>7}{"div":>5}')
for (hk,dv),d in fits.items():
    rh=float(az.rhat(d['idata']).to_array().max()); ess=float(az.ess(d['idata']).to_array().min())
    div=int(d['idata'].sample_stats['diverging'].sum().values)
    diag.append(dict(hurricane=hk,dv=dv,rhat=rh,ess=ess,divergences=div))
    print(f'{hk:<8}{dv:<24}{rh:>7.3f}{ess:>7.0f}{div:>5}{"  !" if rh>1.01 or ess<400 or div>0 else ""}')
pd.DataFrame(diag).to_csv(OUT/'bayes_diagnostics_100mi.csv', index=False)""")

code("""# ── Posterior summary (mean + 95% HDI per storm x DV x predictor) -> CSV ──
rows=[]
for (hk,dv),d in fits.items():
    s=az.summary(d['idata'], var_names=MODEL_FEATURES, hdi_prob=0.95)
    for var in MODEL_FEATURES:
        r=s.loc[var]
        rows.append(dict(hurricane=hk,dv=dv,predictor=var,mean=r['mean'],sd=r['sd'],
            hdi_2_5=r['hdi_2.5%'],hdi_97_5=r['hdi_97.5%'],
            significant=int((r['hdi_2.5%']>0) or (r['hdi_97.5%']<0))))
post=pd.DataFrame(rows); post.to_csv(OUT/'bayes_posterior_summary_100mi.csv', index=False)
print('saved bayes_posterior_summary_100mi.csv', post.shape)
print(post[post.significant==1][['hurricane','dv','predictor','mean','hdi_2_5','hdi_97_5']].round(2).to_string(index=False))""")

code("""# ── OLS per storm (same spec) + VIF -> CSV (supplementary) ──
def ols_fit(hk,dv_col):
    sub=fit_df(hk,dv_col).dropna(subset=[dv_col]+MODEL_FEATURES)
    X=sm.add_constant(sub[MODEL_FEATURES]); return sm.OLS(sub[dv_col],X).fit(), sub
orows=[]
for hk in ['helene','milton']:
    for dv_lab,dv_col in DV_TO_COL.items():
        fit,sub=ols_fit(hk,dv_col); ci=fit.conf_int()
        for var in MODEL_FEATURES:
            orows.append(dict(hurricane=hk,dv=dv_lab,predictor=var,coef=fit.params[var],
                se=fit.bse[var],p=fit.pvalues[var],ci_lo=ci.loc[var,0],ci_hi=ci.loc[var,1],
                r2=fit.rsquared,adj_r2=fit.rsquared_adj,n=int(fit.nobs)))
ols=pd.DataFrame(orows); ols.to_csv(OUT/'ols_coefs_100mi.csv', index=False)
# VIF (pooled design, one per storm)
for hk in ['helene','milton']:
    sub=POOL_Z[POOL_Z.hurricane==hk][MODEL_FEATURES].dropna()
    X=sm.add_constant(sub).values
    vif=pd.DataFrame({'predictor':['const']+MODEL_FEATURES,
        'VIF':[variance_inflation_factor(X,i) for i in range(X.shape[1])]})
    vif.to_csv(OUT/f'vif_{hk}_100mi.csv', index=False)
    print(f'{hk} max VIF (excl const): {vif[vif.predictor!="const"].VIF.max():.1f}')
print('saved ols_coefs_100mi.csv')""")

code("""# ── Bayesian R² (Gelman et al. 2019): posterior median + 95% CrI per storm x DV ──
# Reuses the fitted posteriors (no re-sampling). For each posterior draw s the linear predictor
# mu_s = Intercept_s + X @ beta_s is reconstructed from the coefficient draws (version-independent,
# avoids the bambi predict() API), then  R2_s = var_fit_s / (var_fit_s + var_res_s),  variance taken
# across the n units; var_res from sample residuals (brms / arviz convention). R2 is bounded in (0,1).
# Caveat: with 11 predictors and small n (Milton ~34), in-sample R2 is optimistic -> read with the CrI.
def bayes_r2_posterior(hk, dv_lab, dv_col):
    idata=fits[(hk,dv_lab)]['idata']
    sub=fit_df(hk,dv_col).dropna(subset=[dv_col]+MODEL_FEATURES)
    y=sub[dv_col].to_numpy(); X=sub[MODEL_FEATURES].to_numpy()
    post=idata.posterior
    b0=post['Intercept'].to_numpy().reshape(-1)                                   # (S,)
    B=np.stack([post[f].to_numpy().reshape(-1) for f in MODEL_FEATURES], axis=1)  # (S, P)
    mu=b0[None,:] + X @ B.T                                                        # (n_units, S)
    var_fit=mu.var(axis=0); var_res=(y[:,None]-mu).var(axis=0)                     # per draw, across units
    return var_fit/(var_fit+var_res)                                              # (S,) posterior of R2
BAYES_R2={}; r2rows=[]
print(f'{"storm":<8}{"DV":<24}{"R2_med":>8}   95% CrI')
for hk in ['helene','milton']:
    for dv_lab,dv_col in DV_TO_COL.items():
        r2=bayes_r2_posterior(hk,dv_lab,dv_col)
        med,lo,hi=np.percentile(r2,[50,2.5,97.5])
        BAYES_R2[(hk,dv_lab)]=(float(med),float(lo),float(hi))
        r2rows.append(dict(hurricane=hk,dv=dv_lab,r2_median=float(med),r2_cri_lo=float(lo),
            r2_cri_hi=float(hi),r2_mean=float(r2.mean()),n=fits[(hk,dv_lab)]['n']))
        print(f'{hk:<8}{dv_lab:<24}{med:>8.3f}   [{lo:.3f}, {hi:.3f}]')
pd.DataFrame(r2rows).to_csv(OUT/'bayes_r2_100mi.csv', index=False)
print('saved bayes_r2_100mi.csv')""")

code("""# ── Forest: per-storm (2 rows storms x 3 cols DV), display predictors only ──
def summ(hk,dv): return az.summary(fits[(hk,dv)]['idata'], var_names=MODEL_FEATURES, hdi_prob=0.95)
R2BOX=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=0.65)
yp=np.arange(len(DISPLAY_PREDICTORS))[::-1]
fig,axes=plt.subplots(2,3,figsize=(9.0,6.0))
for i,hk in enumerate(['helene','milton']):
    for j,dv in enumerate(DV_ORDER):
        ax=axes[i,j]; s=summ(hk,dv); col=HURR_COLOR[hk]
        for k,var in enumerate(DISPLAY_PREDICTORS):
            mean=s.loc[var,'mean']; lo,hi=s.loc[var,'hdi_2.5%'],s.loc[var,'hdi_97.5%']; sig=(lo>0)or(hi<0)
            ax.hlines(yp[k],lo,hi,colors=col,linewidth=1.2)
            ax.plot(mean,yp[k],'o',ms=4.6,mfc=col if sig else 'white',mec=col,mew=1.0,zorder=3)
        ax.axvline(0,color='#666',lw=0.6,ls='--'); ax.set_yticks(yp)
        ax.set_yticklabels([PREDICTOR_LABEL[v] for v in DISPLAY_PREDICTORS] if j==0 else ['']*len(yp))
        if j>0: ax.tick_params(axis='y',length=0)
        ax.set_ylim(-0.7,len(DISPLAY_PREDICTORS)-0.3)
        if i==1: ax.set_xlabel('Posterior β (95% HDI)')
        ax.set_title((dv+chr(10)+f'{hk.title()} n={fits[(hk,dv)]["n"]}' if i==0 else f'{hk.title()} n={fits[(hk,dv)]["n"]}'),
                     loc='left',fontsize=8,color=col,pad=4)
        ax.grid(axis='x',ls=':',lw=0.4,alpha=0.7)
        rm,rl,rh=BAYES_R2[(hk,dv)]
        ax.text(0.985,0.105,f'R²={rm:.2f}',transform=ax.transAxes,ha='right',va='bottom',fontsize=6.5,color=col,bbox=R2BOX)
        ax.text(0.985,0.015,f'[{rl:.2f}, {rh:.2f}]',transform=ax.transAxes,ha='right',va='bottom',fontsize=5.5,color=col,bbox=R2BOX)
fig.tight_layout(); save_panel(fig,'figure6a_bayes_per_storm'); plt.close()""")

code("""# ── Forest: storm-overlay per DV (the comparative view) ──
fig,axes=plt.subplots(1,3,figsize=(9.0,3.6)); off={'helene':0.18,'milton':-0.18}
for j,(ax,dv) in enumerate(zip(axes,DV_ORDER)):
    for hk in ['helene','milton']:
        s=summ(hk,dv); col=HURR_COLOR[hk]
        for k,var in enumerate(DISPLAY_PREDICTORS):
            mean=s.loc[var,'mean']; lo,hi=s.loc[var,'hdi_2.5%'],s.loc[var,'hdi_97.5%']; sig=(lo>0)or(hi<0)
            y=yp[k]+off[hk]
            ax.hlines(y,lo,hi,colors=col,lw=1.2,zorder=2)
            ax.plot(mean,y,'o',ms=4.4,mfc=col if sig else 'white',mec=col,mew=1.0,zorder=3)
    ax.axvline(0,color='#666',lw=0.6,ls='--'); ax.set_yticks(yp)
    ax.set_yticklabels([PREDICTOR_LABEL[v] for v in DISPLAY_PREDICTORS] if j==0 else ['']*len(yp))
    if j>0: ax.tick_params(axis='y',length=0)
    ax.set_ylim(-0.7,len(DISPLAY_PREDICTORS)-0.3); ax.set_xlabel('Posterior β (95% HDI)')
    ax.set_title(dv,loc='left',fontsize=8,color=DV_COLOR[dv],pad=4); ax.grid(axis='x',ls=':',lw=0.4,alpha=0.7)
    for ri,hk2 in enumerate(['helene','milton']):
        rm,rl,rh=BAYES_R2[(hk2,dv)]
        ax.text(0.985,0.10-ri*0.082,f'R²={rm:.2f} [{rl:.2f}, {rh:.2f}]',transform=ax.transAxes,
                ha='right',va='bottom',fontsize=5.5,color=HURR_COLOR[hk2],
                bbox=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=0.65))
fig.legend(handles=[Line2D([0],[0],marker='o',color=HURR_COLOR['helene'],label=f'Helene (n={N["helene"]})'),
                    Line2D([0],[0],marker='o',color=HURR_COLOR['milton'],label=f'Milton (n={N["milton"]})'),
                    Line2D([0],[0],marker='o',ls='none',color='#333',mfc='white',label='Hollow = HDI crosses 0')],
           loc='lower center',frameon=False,fontsize=7,ncol=3,bbox_to_anchor=(0.5,-0.04))
fig.tight_layout(rect=[0,0.05,1,1]); save_panel(fig,'figure6a_bayes_overlay'); plt.close()""")

code("""# ── Bayes vs OLS (validation overlay); R² shown as ● Bayes [CrI] vs ■ OLS ──
fig,axes=plt.subplots(2,3,figsize=(9.5,6.0))
for i,hk in enumerate(['helene','milton']):
    for j,dv in enumerate(DV_ORDER):
        dv_col=DV_TO_COL[dv]; ax=axes[i,j]; col=HURR_COLOR[hk]
        fit,_=ols_fit(hk,dv_col); ci=fit.conf_int(); sb=summ(hk,dv)
        for k,var in enumerate(DISPLAY_PREDICTORS):
            ax.hlines(yp[k]+0.18,ci.loc[var,0],ci.loc[var,1],colors='#888',lw=0.9,zorder=2)
            ax.plot(fit.params[var],yp[k]+0.18,'s',ms=3.6,color='#444',zorder=3)
            lo,hi=sb.loc[var,'hdi_2.5%'],sb.loc[var,'hdi_97.5%']; sig=(lo>0)or(hi<0)
            ax.hlines(yp[k]-0.18,lo,hi,colors=col,lw=1.2,zorder=2)
            ax.plot(sb.loc[var,'mean'],yp[k]-0.18,'o',ms=4.4,mfc=col if sig else 'white',mec=col,mew=1.0,zorder=3)
        ax.axvline(0,color='#666',lw=0.6,ls='--'); ax.set_yticks(yp)
        ax.set_yticklabels([PREDICTOR_LABEL[v] for v in DISPLAY_PREDICTORS] if j==0 else ['']*len(yp))
        if j>0: ax.tick_params(axis='y',length=0)
        ax.set_ylim(-0.7,len(DISPLAY_PREDICTORS)-0.3)
        if i==1: ax.set_xlabel('Coefficient (■ OLS, ● Bayes)')
        ax.set_title((dv+chr(10)+f'{hk.title()} n={fits[(hk,dv)]["n"]}' if i==0 else f'{hk.title()} n={fits[(hk,dv)]["n"]}'),loc='left',fontsize=8,color=col,pad=4)
        ax.grid(axis='x',ls=':',lw=0.4,alpha=0.7)
        rm,rl,rh=BAYES_R2[(hk,dv)]
        ax.text(0.985,0.015,f'R²  ●{rm:.2f} [{rl:.2f},{rh:.2f}]   ■{fit.rsquared:.2f}',transform=ax.transAxes,
                ha='right',va='bottom',fontsize=5.0,color='#333',
                bbox=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=0.65))
fig.tight_layout(); save_panel(fig,'figure6a_bayes_vs_ols'); plt.close()
print('06a COMPLETE -> results/npj_100mi/drivers/')""")

nb['cells']=cells
nb['metadata']={'kernelspec':{'display_name':'geo_env','language':'python','name':'geo_env'},
                'language_info':{'name':'python'}}
nbf.write(nb,'06a_global_drivers.ipynb'); print('wrote 06a_global_drivers.ipynb', len(cells),'cells')
