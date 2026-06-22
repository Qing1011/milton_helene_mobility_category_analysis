# Findings — Hurricane Milton County-Level Analysis (N=21)

> **Status note (2026-06-22):** This file is the **historical analysis record** — the Milton N=21 (50-mi) study and
> the 2026-05-18 pooled-OLS cutoff-sensitivity work. For the **npj submission** it is **demoted to Supplementary**:
> the npj primary regression is **separate per-storm Bayesian** (not pooled OLS with `is_milton`), at the **100-mi**
> cutoff, with local units = **Helene clusters + Milton counties (N=135 pooled, Milton stays per-county)**. The
> pooled-spec `dist_to_track` sign-flip and precip-NS stories below are pooled-specification artefacts and are
> re-examined per-storm in the npj package. **Live spec = `npj/notebook/PLAN.md`.**

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

   > **⚠ RETRACTED 2026-05-18 — see §"Affected-region cutoff sensitivity" below.** The negative coefficient was a sample-selection artefact of the 50-mile cutoff. At a 100-mile cutoff (which includes Buncombe/Yancey/Avery NC — the actual Helene disaster region), the coefficient flips back to the orthodox positive sign. There is no puzzle.

6. **Race affects inflow recovery**: Whiter/more rural areas had slower inflow recovery and more inflow disruption — consistent with less external support reaching these communities.

---

## Affected-region cutoff sensitivity (2026-05-18) — **the "puzzle" was an artefact**

The pooled regression in §"Results Summary" used a 50-mile Helene cutoff (271 counties → 38 NCHS-homogeneous clusters; pooled N = 59). The 100-mile cutoff already prepared in [`recompute_flows.ipynb`](../notebook/recompute_flows.ipynb) yields 487 counties → 101 clusters (pooled N = 135 with 34 Milton + 101 Helene units) and **includes Buncombe NC (Asheville, cluster 17) and the rest of the Appalachian disaster region** that the 50-mi cutoff excluded.

### Headline — `dist_to_track_mi` flips sign across cutoffs

| Sample | N | β(dist_to_track_mi) | p | Adj. R² | Direction |
|---|---:|---:|---:|---:|---|
| **50 mi cutoff** | 59 | **−2.12** | **0.028** | 0.56 | Counterintuitive (the "puzzle") |
| **100 mi cutoff** | 135 | **+1.10** | 0.091 | 0.36 | Orthodox (farther = smaller drop) |

The 50-mi negative β was identified almost entirely from a truncated coastal/south-Georgia subset that excludes the inland-flooding region. Once Asheville and the southern-Appalachian counties are included, the wind-decay direction is restored.

**Implications:**
- Key Narrative 5 above is retracted. Track-distance is not a misspecified exposure proxy; it just needs an affected-region definition that doesn't cut off the disaster.
- The hydrologic-exposure variable is no longer required to "fix" anything.
- The `is_milton` effect shrinks but stays highly significant (β = −7.3 at 50 mi → β = −4.6 at 100 mi, p < 0.001 in both) — the storm-specific contrast holds across cutoffs.

### Hydrologic-exposure variable (PRISM 7-day precipitation) — orthodox sign, not significant

Five aggregation alternatives, all run at the 100-mi pooled sample:

| Precip aggregation | β | p | Adj. R² | Verdict |
|---|---:|---:|---:|---|
| pop-weighted mean (7-day total) | −0.62 | 0.37 | 0.355 | NS |
| max within-cluster (7-day total) | −0.45 | 0.52 | 0.353 | NS |
| **pop-weighted mean (peak day)** | **−1.23** | **0.092** | 0.366 | **closest** |
| max within-cluster (peak day) | −1.08 | 0.14 | 0.362 | NS |
| max within-cluster (p90 daily) | −0.62 | 0.37 | 0.355 | NS |

All five aggregations carry the **orthodox negative sign** (more rain → larger mobility drop), but none clears p < 0.05 after `is_milton` is in the model. Three contributing reasons:

1. `is_milton` absorbs the between-hurricane precip difference (Milton mean 172 mm vs Helene mean 118 mm).
2. PRISM county-mean smooths the orographic peaks that drove Helene's catastrophic rainfall. Validation against known truth: PRISM gives Buncombe NC 230 mm county-mean for the 7-day window vs ≈ 350–600 mm at the wettest mountain locations.
3. Pooled correlation between precipitation and track distance is only −0.21, so the two variables are not strong substitutes.

The peak-day population-weighted aggregation comes closest (p = 0.09), consistent with mobility disruption being driven by *intensity* (flash-flood-relevant) rather than *total accumulation*.

### Recommended framing for the manuscript

> *"At a 50-mile affected-region cutoff, `dist_to_track_mi` showed a counterintuitive negative association with mobility disruption (β = −2.12, p = 0.028). Expanding the cutoff to 100 miles — capturing Helene's documented inland-flooding footprint, including Buncombe County, NC — restored the orthodox wind-decay direction (β = +1.10, p = 0.091, N = 135). The 50-mile result was therefore a sample-selection artefact rather than evidence of exposure misspecification. PRISM peak-day precipitation carries the expected negative sign (β = −1.23, p = 0.09) but does not reach significance once the storm dummy is included, in part because county-mean precipitation dampens the orographic peaks that drove Helene's catastrophic rainfall. We report the 100-mile pooled regression as our primary specification and the 50-mile result as sensitivity (Supplementary)."*

### Artefacts produced

- `results/local_level/regression/pooled_dataset_100mi.csv` — augmented pooled dataset, N = 135
- `results/local_level/regression/pooled_dataset_100mi_with_precip.csv` — with `precip_total_3day`, `precip_total_7day`
- `results/local_level/regression/pooled_dataset_100mi_peakprecip.csv` — with all 5 alternative aggregations
- `results/exposure/county_ppt_daily_100mi.csv` — daily PRISM ppt for 516 counties × 13 days
