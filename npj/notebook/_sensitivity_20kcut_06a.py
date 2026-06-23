"""SENSITIVITY (20k baseline-volume cutoff) — 06a per-storm Bayesian + OLS driver regression.
Ported from _build_06a.py. ONLY CHANGE vs primary: each flow DV is fit on units whose baseline-window
mean volume (true_mean) for THAT flow >= 20,000 (replaces the outflow-only degenerate filter; the 20k
cutoff subsumes it since Clinch's outflow baseline ~463 << 20k). Outputs -> sensitivity_20kcut/drivers/.
Run in geo_env (pymc/bambi/arviz). Does NOT touch primary results.
"""
import pathlib, warnings
import numpy as np, pandas as pd
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import bambi as bmb, arviz as az
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
warnings.filterwarnings('ignore')
mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
    'font.size':8,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
    'legend.fontsize':7,'axes.linewidth':0.6,'axes.spines.top':False,'axes.spines.right':False,
    'savefig.dpi':300,'savefig.bbox':'tight','pdf.fonttype':42,'ps.fonttype':42})

ROOT=pathlib.Path('/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter/4_hurricane_category')
LL=ROOT/'results/local_level'; REG=LL/'regression'
OUT=ROOT/'results/npj_100mi/sensitivity_20kcut/drivers'; OUT.mkdir(parents=True, exist_ok=True)
VOL_FLOOR=20000.0
def save_panel(fig,name):
    for ext in ('pdf','png'): fig.savefig(OUT/f'{name}.{ext}', dpi=300, bbox_inches='tight')
    print('saved', name)

POOL=pd.read_csv(REG/'pooled_dataset_100mi_primary_exposure.csv'); POOL['unit_id']=POOL['unit_id'].astype(str)

# ── per-(storm,unit,flow) baseline volume keep flags -> wide, merge into POOL ──
DIRS={'helene':'helene_100mi','milton':'milton_100mi'}
_v=[]
for hk,d in DIRS.items():
    bs=pd.read_csv(LL/d/'baseline_summary.csv'); bs['hurricane']=hk
    _v.append(bs[['hurricane','unit_id','flow_type','true_mean']])
VOL=pd.concat(_v,ignore_index=True); VOL['unit_id']=VOL['unit_id'].astype(str)
VOL['k']=(VOL['true_mean']>=VOL_FLOOR).astype(int)
KEEP=VOL.pivot_table(index=['hurricane','unit_id'],columns='flow_type',values='k').reset_index()
KEEP=KEEP.rename(columns={'within':'keep_within','inflow':'keep_inflow','outflow':'keep_outflow'})
POOL=POOL.merge(KEEP,on=['hurricane','unit_id'],how='left')
print('rows',len(POOL),'| by storm',POOL.hurricane.value_counts().to_dict())

DV_TO_COL={'Largest drop (within)':'largest_drop_within',
           'Largest drop (inflow)':'largest_drop_inflow',
           'Outflow surge':'largest_increase_outflow'}
DV_KEEP={'largest_drop_within':'keep_within','largest_drop_inflow':'keep_inflow',
         'largest_increase_outflow':'keep_outflow'}
DV_ORDER=list(DV_TO_COL)
CONTINUOUS=['median_household_income','pct_no_vehicle','pct_white','nchs_code','total_population',
            'pop_density','dist_to_track_mi','insurance_coverage_pct','precip_total_7day','wind_vmax_sust']
BINARY=['is_coastal']; MODEL_FEATURES=CONTINUOUS+BINARY
DISPLAY_PREDICTORS=['dist_to_track_mi','wind_vmax_sust','precip_total_7day','median_household_income',
                    'insurance_coverage_pct','pct_white','pct_no_vehicle']
PREDICTOR_LABEL={'dist_to_track_mi':'Distance to track','wind_vmax_sust':'Max wind (vmax)',
    'precip_total_7day':'Precip (7-day)','median_household_income':'Median income',
    'insurance_coverage_pct':'Insurance %','pct_white':'% White','pct_no_vehicle':'% No vehicle',
    'nchs_code':'NCHS code','total_population':'Population','pop_density':'Pop density','is_coastal':'Coastal'}
HURR_COLOR={'helene':'#1f77b4','milton':'#d62728'}
DV_COLOR={'Largest drop (within)':'#2c7fb8','Largest drop (inflow)':'#7fcdbb','Outflow surge':'#d95f0e'}

POOL_Z=POOL.copy(); POOL_Z[CONTINUOUS]=StandardScaler().fit_transform(POOL[CONTINUOUS])
N={h:int((POOL.hurricane==h).sum()) for h in ['helene','milton']}

# ── 20k CUTOFF applied here (per-flow) ──
def fit_df(hk,dv_col):
    d=POOL_Z[POOL_Z.hurricane==hk]
    d=d[d[DV_KEEP[dv_col]]==1]
    return d.copy()
PRIOR_WIDTH_FACTOR=2.5
def make_priors(dv_col,df):
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
        print(f'-- fit {hk:6s} {dv_lab} (n={len(sub)}, -{excl} below 20k) --', flush=True)
        m=bmb.Model(f'{dv_col} ~ {RHS}', sub, family='gaussian', priors=make_priors(dv_col,sub))
        idata=m.fit(**SAMPLE); fits[(hk,dv_lab)]={'idata':idata,'model':m,'n':len(sub)}
print('all fits done', flush=True)

# diagnostics
diag=[]
for (hk,dv),d in fits.items():
    rh=float(az.rhat(d['idata']).to_array().max()); ess=float(az.ess(d['idata']).to_array().min())
    div=int(d['idata'].sample_stats['diverging'].sum().values)
    diag.append(dict(hurricane=hk,dv=dv,n=d['n'],rhat=rh,ess=ess,divergences=div))
pd.DataFrame(diag).to_csv(OUT/'bayes_diagnostics_100mi.csv', index=False)
print(pd.DataFrame(diag).round(3).to_string(index=False))

# posterior summary
rows=[]
for (hk,dv),d in fits.items():
    s=az.summary(d['idata'], var_names=MODEL_FEATURES, hdi_prob=0.95)
    for var in MODEL_FEATURES:
        r=s.loc[var]
        rows.append(dict(hurricane=hk,dv=dv,n=d['n'],predictor=var,mean=r['mean'],sd=r['sd'],
            hdi_2_5=r['hdi_2.5%'],hdi_97_5=r['hdi_97.5%'],
            significant=int((r['hdi_2.5%']>0) or (r['hdi_97.5%']<0))))
post=pd.DataFrame(rows); post.to_csv(OUT/'bayes_posterior_summary_100mi.csv', index=False)
print('\nSIGNIFICANT (95% HDI excludes 0):')
print(post[post.significant==1][['hurricane','dv','predictor','mean','hdi_2_5','hdi_97_5']].round(2).to_string(index=False))

# OLS
def ols_fit(hk,dv_col):
    sub=fit_df(hk,dv_col).dropna(subset=[dv_col]+MODEL_FEATURES)
    X=sm.add_constant(sub[MODEL_FEATURES]); return sm.OLS(sub[dv_col],X).fit(), sub
orows=[]
for hk in ['helene','milton']:
    for dv_lab,dv_col in DV_TO_COL.items():
        fit,sub=ols_fit(hk,dv_col); ci=fit.conf_int()
        for var in MODEL_FEATURES:
            orows.append(dict(hurricane=hk,dv=dv_lab,predictor=var,coef=fit.params[var],se=fit.bse[var],
                p=fit.pvalues[var],ci_lo=ci.loc[var,0],ci_hi=ci.loc[var,1],
                r2=fit.rsquared,adj_r2=fit.rsquared_adj,n=int(fit.nobs)))
pd.DataFrame(orows).to_csv(OUT/'ols_coefs_100mi.csv', index=False)

# Bayesian R2 (Gelman 2019)
def bayes_r2_posterior(hk,dv_lab,dv_col):
    idata=fits[(hk,dv_lab)]['idata']; sub=fit_df(hk,dv_col).dropna(subset=[dv_col]+MODEL_FEATURES)
    y=sub[dv_col].to_numpy(); X=sub[MODEL_FEATURES].to_numpy(); post=idata.posterior
    b0=post['Intercept'].to_numpy().reshape(-1)
    B=np.stack([post[f].to_numpy().reshape(-1) for f in MODEL_FEATURES], axis=1)
    mu=b0[None,:]+X@B.T; var_fit=mu.var(axis=0); var_res=(y[:,None]-mu).var(axis=0)
    return var_fit/(var_fit+var_res)
BAYES_R2={}; r2rows=[]
for hk in ['helene','milton']:
    for dv_lab,dv_col in DV_TO_COL.items():
        r2=bayes_r2_posterior(hk,dv_lab,dv_col); med,lo,hi=np.percentile(r2,[50,2.5,97.5])
        BAYES_R2[(hk,dv_lab)]=(float(med),float(lo),float(hi))
        r2rows.append(dict(hurricane=hk,dv=dv_lab,r2_median=float(med),r2_cri_lo=float(lo),
            r2_cri_hi=float(hi),r2_mean=float(r2.mean()),n=fits[(hk,dv_lab)]['n']))
pd.DataFrame(r2rows).to_csv(OUT/'bayes_r2_100mi.csv', index=False)

def summ(hk,dv): return az.summary(fits[(hk,dv)]['idata'], var_names=MODEL_FEATURES, hdi_prob=0.95)
yp=np.arange(len(DISPLAY_PREDICTORS))[::-1]; R2BOX=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=0.65)

# forest: per-storm
fig,axes=plt.subplots(2,3,figsize=(9.0,6.0))
for i,hk in enumerate(['helene','milton']):
    for j,dv in enumerate(DV_ORDER):
        ax=axes[i,j]; s=summ(hk,dv); col=HURR_COLOR[hk]
        for k,var in enumerate(DISPLAY_PREDICTORS):
            mean=s.loc[var,'mean']; lo,hi=s.loc[var,'hdi_2.5%'],s.loc[var,'hdi_97.5%']; sig=(lo>0)or(hi<0)
            ax.hlines(yp[k],lo,hi,colors=col,linewidth=1.2); ax.plot(mean,yp[k],'o',ms=4.6,mfc=col if sig else 'white',mec=col,mew=1.0,zorder=3)
        ax.axvline(0,color='#666',lw=0.6,ls='--'); ax.set_yticks(yp)
        ax.set_yticklabels([PREDICTOR_LABEL[v] for v in DISPLAY_PREDICTORS] if j==0 else ['']*len(yp))
        if j>0: ax.tick_params(axis='y',length=0)
        ax.set_ylim(-0.7,len(DISPLAY_PREDICTORS)-0.3)
        if i==1: ax.set_xlabel('Posterior β (95% HDI)')
        ax.set_title((dv+chr(10)+f'{hk.title()} n={fits[(hk,dv)]["n"]}' if i==0 else f'{hk.title()} n={fits[(hk,dv)]["n"]}'),loc='left',fontsize=8,color=col,pad=4)
        ax.grid(axis='x',ls=':',lw=0.4,alpha=0.7)
        rm,rl,rh=BAYES_R2[(hk,dv)]
        ax.text(0.985,0.105,f'R²={rm:.2f}',transform=ax.transAxes,ha='right',va='bottom',fontsize=6.5,color=col,bbox=R2BOX)
        ax.text(0.985,0.015,f'[{rl:.2f}, {rh:.2f}]',transform=ax.transAxes,ha='right',va='bottom',fontsize=5.5,color=col,bbox=R2BOX)
fig.suptitle('06a Bayesian drivers — 20k baseline-volume cutoff',fontsize=9,fontweight='bold')
fig.tight_layout(); save_panel(fig,'figure6a_bayes_per_storm_20kcut'); plt.close()

# forest: storm overlay
fig,axes=plt.subplots(1,3,figsize=(9.0,3.6)); off={'helene':0.18,'milton':-0.18}
for j,(ax,dv) in enumerate(zip(axes,DV_ORDER)):
    for hk in ['helene','milton']:
        s=summ(hk,dv); col=HURR_COLOR[hk]
        for k,var in enumerate(DISPLAY_PREDICTORS):
            mean=s.loc[var,'mean']; lo,hi=s.loc[var,'hdi_2.5%'],s.loc[var,'hdi_97.5%']; sig=(lo>0)or(hi<0); y=yp[k]+off[hk]
            ax.hlines(y,lo,hi,colors=col,lw=1.2,zorder=2); ax.plot(mean,y,'o',ms=4.4,mfc=col if sig else 'white',mec=col,mew=1.0,zorder=3)
    ax.axvline(0,color='#666',lw=0.6,ls='--'); ax.set_yticks(yp)
    ax.set_yticklabels([PREDICTOR_LABEL[v] for v in DISPLAY_PREDICTORS] if j==0 else ['']*len(yp))
    if j>0: ax.tick_params(axis='y',length=0)
    ax.set_ylim(-0.7,len(DISPLAY_PREDICTORS)-0.3); ax.set_xlabel('Posterior β (95% HDI)')
    ax.set_title(dv,loc='left',fontsize=8,color=DV_COLOR[dv],pad=4); ax.grid(axis='x',ls=':',lw=0.4,alpha=0.7)
    for ri,hk2 in enumerate(['helene','milton']):
        rm,rl,rh=BAYES_R2[(hk2,dv)]
        ax.text(0.985,0.10-ri*0.082,f'R²={rm:.2f} [{rl:.2f}, {rh:.2f}]',transform=ax.transAxes,ha='right',va='bottom',
                fontsize=5.5,color=HURR_COLOR[hk2],bbox=R2BOX)
fig.legend(handles=[Line2D([0],[0],marker='o',color=HURR_COLOR['helene'],label='Helene'),
                    Line2D([0],[0],marker='o',color=HURR_COLOR['milton'],label='Milton'),
                    Line2D([0],[0],marker='o',ls='none',color='#333',mfc='white',label='Hollow = HDI crosses 0')],
           loc='lower center',frameon=False,fontsize=7,ncol=3,bbox_to_anchor=(0.5,-0.04))
fig.suptitle('06a Bayesian drivers (storm overlay) — 20k cutoff',fontsize=9,fontweight='bold')
fig.tight_layout(rect=[0,0.05,1,0.96]); save_panel(fig,'figure6a_bayes_overlay_20kcut'); plt.close()
print('06a SENSITIVITY COMPLETE ->', OUT, flush=True)
