# Findings — Hurricane Milton County-Level Analysis (N=21)

## Previous Observations (descriptive, from scatter plots)

- Higher income → smaller within-region drop (visible in scatter, not significant)
- Higher income → larger outflow increase (visible in scatter, not significant)
- Inflow: no clear relationship with income
- Outflow increase positively correlated with income and insurance coverage (visible, not significant in regression)
- Within recovery time negatively correlated with insurance coverage % — but driven by Okeechobee (see below)
- Higher income → faster within-region recovery (Milton), not significant

---

## Systematic Analysis (2026-03-26)

### 1. OLS Regression: No Robust Significance

Multiple OLS specifications were tested for Milton's 21 counties:

**DVs tested**: largest_drop (within), recovery_days (within), outflow_increase, total_disruption (recovery × |drop|)

**IVs tested**: total_population, median_household_income, pct_no_vehicle, insurance_coverage_pct, dist_to_track_mi, and interactions

| Model | DV | R² | Adj. R² | F p-value | Result |
|---|---|---|---|---|---|
| Socioeconomic only | Largest drop | 0.042 | -0.198 | 0.948 | Not significant |
| Socioeconomic only | Recovery time | 0.309 | 0.136 | 0.180 | Not significant |
| Socioeconomic only | Outflow increase | 0.109 | -0.114 | 0.745 | Not significant |
| Drop + distance | Recovery time | 0.008 | -0.102 | 0.932 | Not significant |
| Drop + dist + socio | Recovery time | 0.318 | 0.025 | 0.417 | Not significant |
| Drop × distance interaction | Recovery time | 0.008 | -0.167 | 0.986 | Not significant |
| Distance only | Total disruption | 0.044 | -0.006 | 0.359 | Not significant |
| Dist + socioeconomic | Total disruption | 0.176 | -0.098 | 0.671 | Not significant |

**No model achieves F p < 0.05.** All adjusted R² values are near zero or negative.

### 2. Insurance Coverage Effect Is Driven by One County

With all 21 counties, `insurance_coverage_pct` appeared significant for recovery time (coef = -0.288, p = 0.032). However, removing **Okeechobee** (the single outlier with recovery = 6.2 days, vs mean 4.8):

| Variable | All 21 (p) | Without Okeechobee (p) |
|---|---|---|
| insurance_coverage_pct | **0.032** | 0.599 |
| pct_no_vehicle | 0.691 | 0.080 |
| median_household_income | 0.698 | 0.119 |

The "significant" insurance effect vanishes entirely. With N=21, a single observation can flip which variable appears significant. No OLS result is stable.

### 3. Disruption Magnitude Does Not Predict Recovery

recovery_days ~ largest_drop: R² = 0.008, p = 0.71. Counties with deeper drops did not take longer to recover. Charlotte had the largest drop (-47%) but recovered in 4.5 days; Okeechobee had a moderate drop (-36%) but the slowest recovery (6.2 days). **Disruption severity and recovery speed are decoupled** for Milton.

### 4. Spatial Diagnostics (Moran's I)

| DV | Moran's I (Queen) | p | Moran's I (KNN) | p |
|---|---|---|---|---|
| Largest drop | 0.223 | **0.046** | 0.138 | 0.147 |
| Recovery time | 0.005 | 0.691 | 0.015 | 0.617 |
| Outflow increase | 0.327 | **0.006** | 0.408 | **0.0004** |

- **Outflow increase** has strong spatial autocorrelation — nearby counties evacuated similarly. This reflects evacuation zone geography, not socioeconomic factors.
- **Largest drop** has weak spatial autocorrelation (Queen weights only, p=0.046). Coastal counties (Lee, Charlotte) cluster together.
- **Recovery time** has no spatial autocorrelation. Residuals are spatially random.
- **Residuals vs distance-to-track**: not significant for any DV (all p > 0.2). The spatial clustering is **neighborhood-based**, not a clean distance gradient.

### 5. Income–Distance Confound

Income and distance-to-track are correlated in Milton:
- Q4 (highest income): median distance = 11.3 mi (Manatee, Sarasota, Brevard near the track)
- Q1 (lowest income): median distance = 39.7 mi (DeSoto, Hardee, Okeechobee, Highlands farther away)
- Pearson r = -0.218 (p=0.34), Spearman ρ = -0.295 (p=0.19) — not significant but descriptively notable

### 6. Distance-Adjusted Analysis Confirms Null Result

After residualizing each DV against distance-to-track:

**Partial correlations (income–DV | distance):**

| DV | Raw r | Raw p | Partial r | Partial p |
|---|---|---|---|---|
| Largest drop | 0.074 | 0.751 | 0.024 | 0.919 |
| Recovery time | -0.038 | 0.871 | -0.040 | 0.866 |
| Outflow increase | 0.272 | 0.232 | 0.255 | 0.278 |
| Total disruption | -0.087 | 0.709 | -0.043 | 0.858 |

All partial correlations are near zero and non-significant. Distance was neither masking nor inflating an income effect — **there is no income effect to find**.

**Kruskal-Wallis on distance-adjusted DVs:**

| DV | Raw KW p | Adjusted KW p | Raw MW Q1vQ4 p | Adjusted MW Q1vQ4 p |
|---|---|---|---|---|
| Largest drop | 0.530 | 0.719 | 0.329 | 0.792 |
| Recovery time | 0.932 | 0.932 | 0.931 | 0.931 |
| Outflow increase | 0.328 | 0.406 | 1.000 | 0.931 |
| Total disruption | 0.698 | 0.898 | 0.537 | 0.662 |

Adjusting for distance makes p-values **worse, not better**. The confound was not hiding an income effect.

### 7. Recovery Time Is Remarkably Uniform

Milton's within-region recovery time ranges from 4.1 to 6.2 days (excluding Okeechobee: 4.1–5.5 days). Median recovery across all four income quartiles is virtually identical (4.77–4.84 days). This uniformity may reflect:
- Milton's broad wind field affecting all counties similarly
- Well-forecasted storm → uniform preparedness regardless of income
- Florida's relatively strong infrastructure and emergency management
- The 50-mile cutoff selecting counties with broadly similar exposure

---

## Conclusions for Milton

1. **No statistically significant socioeconomic predictor** of mobility disruption or recovery was found across any model specification (OLS, Kruskal-Wallis, partial correlation), whether raw or distance-adjusted.

2. **The null result is robust**: it holds across 4 DVs, multiple IV combinations, with and without Okeechobee, and after controlling for distance-to-track.

3. **Outflow increase shows spatial clustering** (Moran's I p < 0.001) driven by evacuation zone geography, not income.

4. **Sample size (N=21) limits statistical power**. It is possible that real effects exist but are too small to detect with 21 counties. Formal inference should be reserved for Helene (N=271).

5. **Descriptive presentation** (quartile boxplots, scatter + LOWESS, residual maps) is the appropriate way to report Milton results. The visual patterns are suggestive but not statistically confirmable.

---

## Notebooks

| Notebook | Purpose |
|---|---|
| `spatial_diagnostics_milton.ipynb` | LOWESS scatter plots, Moran's I, residual maps |
| `quartile_analysis_milton.ipynb` | Income quartile boxplots, Kruskal-Wallis tests |
| `confound_analysis_milton.ipynb` | Distance-adjusted analysis, partial correlations |
| `regression_largest_drop_v2b.ipynb` | Pooled OLS (baseline reference) |

## Output Directories

| Directory | Contents |
|---|---|
| `results/spatial_diagnostics_milton/` | Distance CSV, diagnostic summary, scatter plots, residual maps |
| `results/quartile_analysis_milton/` | KW summary, quartile descriptives, boxplots, panel figure |
| `results/confound_analysis_milton/` | Partial correlations, raw vs adjusted comparison, side-by-side boxplots |

Here's the full interpretation:

---

## Results Summary

### Model Fit (Adj. R²)

| DV | Adj. R² | F p-value | Verdict |
|---|---|---|---|
| **Largest Drop — Within** | **0.728** | **<0.001** | Strong model |
| **Total Disruption — Within** | **0.523** | **<0.001** | Moderate-strong |
| **Outflow Increase** | **0.341** | **<0.001** | Moderate |
| **Largest Drop — Inflow** | **0.388** | **<0.001** | Moderate |
| Recovery Time — Within | 0.148 | 0.056 | Weak/borderline |
| Recovery Time — Inflow | 0.192 | 0.036 | Weak |
| Total Disruption — Inflow | 0.098 | 0.156 | Not significant |

### Significant Predictors (p < 0.05)

**1. Hurricane dummy (`is_milton`)** — the strongest predictor
- Within drop: **-17.3** (Milton drops 17% more than Helene) — p < 0.001
- Within total disruption: **+107** (Milton has much larger total disruption) — p < 0.001
- Inflow drop: **-15.4** (Milton's inflow drops more) — p = 0.009
- Milton is simply a more disruptive hurricane across the board

**2. Distance to track (`dist_to_track_mi`)**
- Within drop: **-1.84** (farther = more negative drop) — p = 0.039
- This is counterintuitive with the negative sign convention. It means farther counties had **larger drops**. Possible explanation: Helene's far-from-track counties in Appalachian NC experienced severe flooding and landslides despite distance from the wind track. The "track distance" doesn't capture rainfall/flood impact well.
- Within recovery: **+0.51** (farther = slower recovery) — p = 0.044
- Within total disruption: **+22.9** (farther = more total disruption) — p = 0.005
- Outflow increase: **-7.1** (farther = less evacuation) — p = 0.052 — this makes sense (less evacuation far from track)

**3. Insurance coverage (`insurance_coverage_pct`)**
- Within drop: **+1.98** (higher insurance = less severe drop) — p = 0.044
- Within recovery: **-0.68** (higher insurance = faster recovery) — p = 0.016
- Within total disruption: **-28.4** (higher insurance = less total disruption) — p = 0.002
- Consistent story: insurance coverage is protective across all within-flow metrics

**4. Income (`median_household_income`)**
- Within recovery: **+0.90** (higher income = slower recovery) — p = 0.017
- Outflow increase: **+17.4** (higher income = more evacuation) — p = 0.002
- Inflow drop: **-4.25** (higher income = larger inflow drop) — p = 0.083
- Interpretation: wealthier areas evacuate more (outflow spike) and lose more inflow, and paradoxically recover slower within-region — possibly because wealthy residents who evacuated take longer to return

**5. Coastal (`is_coastal`)**
- Outflow increase: **+38.8** (coastal = 39% more outflow increase) — p < 0.001
- This is the strongest outflow predictor — coastal counties evacuate massively

**6. Pct White (`pct_white`)**
- Inflow recovery: **+4.4** (whiter = slower inflow recovery) — p = 0.015
- Inflow total disruption: **+116** (whiter = much more inflow disruption) — p = 0.020
- Echoes the Milton-only finding — whiter/more rural areas receive less incoming support

### Key Narratives

1. **Hurricane severity matters most**: Milton (Cat 5) caused ~17% more within-flow drop than Helene (Cat 4), controlling for everything else.

2. **Insurance is consistently protective**: Higher insurance coverage → smaller drops, faster recovery, less total disruption. This is the most robust socioeconomic finding.

3. **Wealth enables evacuation but delays return**: Higher-income counties had larger outflow spikes (they can afford to leave) but slower within-region recovery (they stay away longer).

4. **Coastal = massive evacuation**: Being coastal adds ~39% to outflow increase, the strongest single predictor of evacuation behavior.

5. **Distance to track is complex**: Farther counties had larger within-flow drops — likely because Helene's flooding extended far inland (Appalachian NC). This challenges the assumption that track distance = impact severity.

6. **Race affects inflow recovery**: Whiter/more rural areas had slower inflow recovery and more inflow disruption — consistent with less external support reaching these communities.
