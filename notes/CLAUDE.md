# Hurricane Mobility Disruption and Recovery Analysis

Reference Repository: https://github.com/Qing1011/hurricane_mobility

---

## 1. Project Objective

This project quantifies and compares mobility disruptions and recovery dynamics associated with:

- Hurricane Helene  (2024-09-26)
- Hurricane Milton  (2024-10-09)

The analysis is conducted across mobility categories and spatial scales (regional and distance-band levels).

Categories include:
- Travel
- Work & Professional
- Health
- Education
- Retail & Leisure
- Urban Government
- Utilities

Core goals:

1. Estimate counterfactual (baseline) mobility.
2. Quantify disruption magnitude.
3. Define and measure recovery time.
4. Compare patterns across categories and hurricanes.
5. Identify spatially varying socioeconomic drivers of recovery heterogeneity using GWR.

---

## 2. Data Structure

Mobility data is structured as a 4D tensor:

`M[day, category, destination, origin]`

Where:

- `day`: daily index
- `category`: mobility or POI category (17 raw categories → 7 groups)
- `destination`: geographic unit receiving mobility
- `origin`: geographic unit generating mobility

Additional datasets:

- County-level socioeconomic variables (ACS 2022 5-year estimates)
- Hurricane-affected region definitions (counties within 50-mile cutoff of track)
- Hurricane track geometry (for distance computation)

---

## 3. Baseline Model (Counterfactual Mobility)

### 3.1 SARIMAX with Exogenous Dummies

For each category/region or distance-band:

- Fit a SARIMAX model: AR(1) with exogenous day-of-week, month, and year dummies.
- Model specification: order=(1,0,0), seasonal_order=(0,0,0,0), with intercept.
- Training data: 2023 Jul–Oct + 2024 Jul to 7 days before landing (hurricane-adaptive window).
- Log-transform: $y_{log} = \log(1 + y)$, back-transformed via $\exp(y_{log}) - 1$.

Baseline prediction:

$\hat{M}_t^{(baseline)}$

This represents counterfactual mobility in the absence of hurricane impact.

Implementation: `recovery_function_v2.py` — `prepare_time_series_with_exog()`, `fit_arimax_model()`, `get_predictions_and_ci()`.

v2 fix: `X_train` now correctly filtered by boolean NaN mask (`X_train_0[mask]` instead of `X_train_0.loc[mask.index]`), resolving SARIMA failures for inflow counties with zero-flow days.

---

## 4. Flow Type Decomposition

Mobility is decomposed into three flow types at two spatial scales.

### 4.1 Regional Level (all counties in A aggregated)

For the entire affected region A:
- **Within-region** $W(t) = \sum_{o \in A} \sum_{d \in A} M(t,d,o)$ — trips where both endpoints are in A
- **Inflow** $I(t) = \sum_{o \notin A} \sum_{d \in A} M(t,d,o)$ — trips from outside A to A
- **Outflow** $O(t) = \sum_{o \in A} \sum_{d \notin A} M(t,d,o)$ — trips from A to outside A

Implementation: `ma.region_mobility(Ms, selected_idx)` from `analysis.py`.

### 4.2 Local Level (per county j or per cluster C)

For a single county $j$ (or cluster $C$) within affected region $A$:

- **Within** $W_j(t) = \sum_{d \in A} M(t,d,j)$ — trips FROM county $j$ TO anywhere in $A$ (including $j$ itself). Captures how much this local unit contributes to regional circulation.
- **Outflow** $O_j(t) = \sum_{d \notin A} M(t,d,j)$ — trips FROM county $j$ TO destinations OUTSIDE $A$. Captures evacuation and exit dynamics.
- **Inflow** $I_j(t) = \sum_{o \notin A} M(t,j,o)$ — trips TO county $j$ FROM origins OUTSIDE $A$. Captures external support arriving at this specific local unit.

For a cluster $C \subset A$ (set of counties), replace $j$ with $C$:
- $W_C(t) = \sum_{j \in C} \sum_{d \in A} M(t,d,j)$ — trips from cluster to anywhere in A
- $O_C(t) = \sum_{j \in C} \sum_{d \notin A} M(t,d,j)$ — trips from cluster to outside A
- $I_C(t) = \sum_{j \in C} \sum_{o \notin A} M(t,j,o)$ — trips to cluster from outside A

**Key distinction from regional level**: At the regional level, "within" means both endpoints in A. At the local level, "within" means trips FROM the local unit TO anywhere in A — this captures the local unit's functional connectivity to the rest of the affected region, not just internal-to-local-unit trips.

**Implementation**: `compute_local_flows()` in `recompute_flows.ipynb`. Uses the corrected formulation:
```python
# For county j with index j_idx, and A_idx = all affected county indices:
v_j = M_sum[:, :, j_idx]          # shape (days, all_destinations) — trips FROM j
within_j = v_j[:, A_idx].sum(1)   # trips from j to A
outflow_j = v_j.sum(1) - within_j # trips from j to not-A

fv_j = M_sum[:, j_idx, :]         # shape (days, all_origins) — trips TO j
total_to_j = fv_j.sum(1)
inflow_from_A = fv_j[:, A_idx].sum(1)
inflow_j = total_to_j - inflow_from_A  # trips to j from not-A
```

**Bug history**: The original `analysis.py::region_mobility()` had a bug in inflow computation where `within_region` (computed from outgoing direction j→A) was subtracted from total incoming (→j), producing negative inflow for large counties. Fixed in `recompute_flows.ipynb`.

### 4.3 Scope of Analysis

| Scale | Within | Inflow | Outflow |
|-------|--------|--------|---------|
| Regional (category comparison) | ✓ disruption + recovery | ✓ disruption + recovery | ✓ outflow increase (descriptive) |
| Local — Milton (21 counties) | ✓ disruption + recovery | ✓ disruption + recovery | ✓ outflow increase |
| Local — Helene (clusters of 271 counties) | ✓ disruption + recovery | ✓ disruption + recovery | ✓ outflow increase |

All three flow types are analyzed at both scales. Outflow increase is reported as the largest positive deviation from baseline (evacuation surge).

---

## 5. Disruption Metrics

### 5.1 Largest Drop (Within, Inflow only)

Largest negative deviation from baseline within the landing week [landing, landing+6d]:

$\Delta_{min} = \min_t \frac{M_t − \hat{M}_t^{(baseline)}}{\hat{M}_t^{(baseline)}} \times 100$

Day of largest drop:

$t_{drop} = \arg\min_t \frac{M_t − \hat{M}_t^{(baseline)}}{\hat{M}_t^{(baseline)}}$

This measures peak disruption intensity as a percentage deviation from baseline.

### 5.2 Outflow Increase (descriptive only)

Largest positive deviation above baseline within a 2-week window [landing−7d, landing+6d]:

$\Delta_{max} = \max_t \frac{M_t − \hat{M}_t^{(baseline)}}{\hat{M}_t^{(baseline)}} \times 100$

Captures pre-landfall evacuation surge and landing-week outbound spike. Reported as a descriptive metric; not used in recovery time or regression analysis.

---

### 5.3 Recovery Time (Trend-Based Method with Theil–Sen Robust Estimation)

Applied to **within-region and inflow at regional level; within-region only at county/distance-band level**.

Recovery time is defined as:

1. Compute relative deviation: $rd_t = (M_t − \hat{M}_t) / \hat{M}_t$
2. Smooth with a centred 3-day moving average.
3. Find the trough (most negative smoothed value within 7 days after landing).
4. Extract the **monotonic recovery segment**: walk forward from trough, keeping only the initial non-decreasing run.
5. Fit **Theil–Sen robust slope** (median-based, resistant to outliers) on the monotonic segment:
   $\hat{rd}(t) = \alpha + \beta t$
6. Recovery time **measured from landing date**:
   $\tau = (t_{trough} - t_{landing}) + (-\alpha / \beta)$

where $-\alpha / \beta$ gives the number of days from trough to zero-crossing of the Theil–Sen line.

This measures the number of days from hurricane landing for mobility to return to baseline.

Implementation: `trend_based_recovery()` in both `trend_based_recovery_region_v2.ipynb` (regional) and `regression_largest_drop_v2a.ipynb` (distance-band).

---

## 6. Regional-Level Analysis (Category Comparison)

**Notebook**: `trend_based_recovery_region_v2.ipynb`

For the affected region (all counties aggregated), analyzes **7 categories × 2 flow types = 14 time series** (within + inflow):

### 6.1 Per Flow Type × Category

For each of the 14 combinations:

1. Fit SARIMAX baseline on pre-hurricane data
2. Compute relative deviation from baseline during forecast window
3. Apply trend-based recovery (smooth → trough → monotonic → Theil–Sen → recovery time)
4. Generate recovery plots with raw/smoothed deviation, trough, monotonic segment, and Theil–Sen fit line

### 6.2 Comparative Outputs

- Per-flow-type bar charts of recovery time by category
- Cross-flow grouped bar chart (Within vs Inflow)
- Summary CSV: `recovery_fig/{hurricane}_trend_based_region/recovery_summary_3flow.csv`

---

## 7. Distance-Band Analysis (Replacing Per-County Analysis)

### 7.1 Rationale

Individual county-level SARIMAX baselines are unstable for rural counties with low mobility volumes, producing noisy relative deviations and unreliable recovery estimates. Distance-band aggregation solves this by:
- Increasing signal volume per unit (more stable baselines)
- Creating a natural spatial gradient from the hurricane track
- Enabling clearer interpretation of how disruption/recovery varies with proximity
- Providing enough observations per band for robust Theil–Sen fitting

### 7.2 Distance-Band Definition

Counties are grouped into concentric distance bands based on the minimum distance from the county centroid to the hurricane track:

- Band 1: 0–10 miles (direct track)
- Band 2: 10–25 miles (near-track)
- Band 3: 25–50 miles (peripheral)

(Band boundaries may be adjusted based on county count and population distribution.)

For each band, **within-region mobility** is **summed** across all constituent counties before fitting SARIMAX and computing metrics. This produces one time series per band × category. (Inflow is not analyzed at the band/county level — see Section 4.1.)

### 7.3 Distance Computation

For each county:
$d_i = \min_{p \in \text{track}} \| \text{centroid}(i) - p \|$

where the hurricane track is represented as a polyline of observed positions and the distance is computed geodesically.

### 7.4 Notebook Workflow (to be implemented as `regression_largest_drop_v3a.ipynb`)

**Step 1: Assign counties to distance bands**
- Load hurricane track coordinates
- Compute county centroid → track distance for all affected counties
- Assign each county to a distance band

**Step 2: Aggregate within-region mobility by band**
- For each band, sum within-region flows across constituent counties
- Result: one time series per band × category

**Step 3: Compute metrics per band**
- Fit SARIMAX baseline per band (much more stable than per-county)
- Compute largest drop and trend-based recovery time per band
- Generate band-level recovery plots

**Step 4: Export**
- `distance_band_metrics_within.csv` — per-band disruption and recovery
- Band-level recovery plots

---

## 8. Spatial Diagnostics — Milton (N=21)

### 8.0 Context

Global OLS regression on Milton's 21 counties is not statistically significant for within-flow largest drop, recovery time, or outflow increase. There are nonlinear patterns visible in scatter plots, but it is unclear whether the nonlinearity is spatial in nature.

### 8.1 Diagnostic Notebook: `spatial_diagnostics_milton.ipynb`

This notebook determines the nature of the nonlinearity before choosing a modelling approach:

1. **Compute county centroid → track distance** using Milton storm track shapefile (`milton_storm_track.shp`) and county boundaries, projected to EPSG:5070 (Albers Equal Area).

2. **Scatter + LOWESS plots colored by distance-to-track** for each DV × IV pair:
   - If LOWESS deviates from OLS line → nonlinearity exists
   - If color gradient follows the nonlinear pattern → spatial nonlinearity
   - If color is randomly scattered → non-spatial nonlinearity

3. **OLS regression + Moran's I on residuals**:
   - Queen contiguity weights and KNN(k=4) weights
   - Significant Moran's I → residuals are spatially clustered → spatial model needed
   - Non-significant Moran's I → nonlinearity is non-spatial → GAM appropriate

4. **Residuals vs distance-to-track** (Spearman correlation):
   - Significant → distance is a missing predictor or interaction term
   - Non-significant → distance does not explain residual pattern

### 8.2 Decision Tree (based on diagnostic results)

| Moran's I | Resid~Dist | Scatter color | Recommended model |
|-----------|------------|---------------|-------------------|
| Not sig. | Not sig. | Random | GAM (1-2 smooth terms, max ~5 effective df for N=21) |
| Significant | Significant | Gradient | Distance interaction: $y \sim \beta_1 x + \beta_2 d + \beta_3 (x \cdot d)$ |
| Not sig. | Significant | Gradient | Add distance-to-track as IV, or interaction model |
| Significant | Not sig. | Clustered | Spatial lag or spatial error model (if N permits) |

### 8.3 Candidate Models for N=21

**GAM** (if nonlinearity is non-spatial):
$y_i = \beta_0 + f_1(x_{1i}) + \beta_2 x_{2i} + \ldots + \epsilon_i$
- 1-2 smooth terms (3-4 effective df each), other IVs linear
- Total effective parameters ≤ 6-7 for N=21
- LOOCV to verify genuine improvement over OLS

**Distance interaction** (if nonlinearity is spatial):
$y_i = \beta_0 + \beta_1 x_i + \beta_2 d_i + \beta_3 (x_i \cdot d_i) + \epsilon_i$
- Only +2 parameters over simple OLS
- Tests whether the socioeconomic effect depends on proximity to track

**Piecewise regression** (if threshold pattern visible):
$y_i = \beta_0 + \beta_1 x_i \cdot \mathbf{1}(d_i < c) + \beta_2 x_i \cdot \mathbf{1}(d_i \geq c) + \epsilon_i$

---

## 9. Regression: Geographically Weighted Regression (GWR) — Helene (Pending)

> **Note**: GWR is deferred until Helene county grouping is resolved.
> Milton (N=21) is too small for GWR. The section below documents the planned
> methodology for when Helene (N=271) is ready.

### 9.1 Motivation

Global OLS assumes that the relationship between socioeconomic variables and mobility disruption/recovery is spatially constant. However, hurricane impacts are inherently spatial — the effects of income, vehicle access, etc. on disruption likely vary with distance to the track. GWR allows regression coefficients to vary continuously across space.

### 9.2 Model Specification

For each county $i$, GWR estimates a local regression:

$y_i = \beta_0(u_i, v_i) + \sum_{k=1}^{p} \beta_k(u_i, v_i) \cdot x_{ik} + \epsilon_i$

where:
- $y_i$: dependent variable (largest drop or recovery time) at county $i$
- $(u_i, v_i)$: spatial coordinates of county $i$ centroid
- $\beta_k(u_i, v_i)$: spatially varying coefficient for predictor $k$
- $x_{ik}$: predictor $k$ at county $i$ (socioeconomic variable)
- $\epsilon_i$: error term

### 9.3 Estimation

Each local regression is estimated by weighted least squares:

$\hat{\boldsymbol{\beta}}(u_i, v_i) = (\mathbf{X}^T \mathbf{W}_i \mathbf{X})^{-1} \mathbf{X}^T \mathbf{W}_i \mathbf{y}$

where $\mathbf{W}_i = \text{diag}(w_{i1}, w_{i2}, \ldots, w_{in})$ is a diagonal weight matrix. Observations near county $i$ receive higher weight.

### 9.4 Spatial Kernel: Distance to Hurricane Track

Instead of using Euclidean distance between county centroids (standard GWR), we define the kernel based on **distance to the hurricane track**:

$w_{ij} = K\left(\frac{d_j}{h}\right)$

where:
- $d_j = \min_{p \in \text{track}} \| \text{centroid}(j) - p \|$ is the distance from county $j$ centroid to the nearest point on the hurricane track
- $h$ is the bandwidth (chosen by cross-validation or AICc minimization)
- $K(\cdot)$ is a kernel function

**Kernel options:**
- Gaussian: $K(z) = \exp(-\frac{1}{2} z^2)$
- Bisquare (compact support): $K(z) = (1 - z^2)^2 \mathbf{1}_{|z| \leq 1}$
- Adaptive bandwidth: $h_i$ set to the distance to the $k$-th nearest neighbour (in track-distance space), ensuring each local model uses the same number of effective observations

**Rationale for track-distance kernel:**
Counties at similar distances from the track experience similar wind speeds, rainfall, and storm surge. This aligns the spatial weighting with the physical gradient of hurricane impact rather than arbitrary geographic proximity.

### 9.5 Bandwidth Selection

Optimal bandwidth $h$ is selected by minimizing the corrected Akaike Information Criterion:

$\text{AICc} = 2n \ln(\hat{\sigma}) + n \ln(2\pi) + n \cdot \frac{n + \text{tr}(\mathbf{S})}{n - 2 - \text{tr}(\mathbf{S})}$

where $\mathbf{S}$ is the hat matrix and $\hat{\sigma}^2$ is the estimated residual variance. This balances model fit against effective degrees of freedom.

### 9.6 Dependent Variables

- `largest_drop_within` — max % reduction in within-region mobility
- `recovery_within` — trend-based recovery days (within)

(Inflow is analyzed at the regional level only — see Section 4.1. County/band-level GWR uses within-region metrics.)

### 9.7 Independent Variables (ACS 2022 5-year estimates)

- `total_population` (B01003)
- `median_household_income` (B19013)
- `pct_no_vehicle` — % households without vehicle (B08201)
- `insurance_coverage_pct` — % with health insurance (B27010)
- `distance_to_track` — minimum distance from county centroid to hurricane track (km)

### 9.8 Diagnostics

- **Local R²**: mapped to show where the model explains more/less variance
- **Local coefficient maps**: spatial variation of each $\beta_k$ across the study area
- **Local t-statistics**: significance of each coefficient at each location
- **Monte Carlo significance test**: for spatial non-stationarity of coefficients (H₀: coefficients are globally constant)
- **Comparison with OLS**: AICc comparison, F-test for GWR vs OLS improvement
- **Multicollinearity**: local condition number and VIF at each location

### 9.9 Implementation

Python: `mgwr` package (Multiscale GWR)
- `mgwr.gwr.GWR` for standard GWR
- `mgwr.sel_bw.Sel_BW` for bandwidth selection
- Custom distance matrix using track-distance rather than Euclidean distance

**Note on sample size**: GWR requires sufficient spatial observations. Milton (21 counties) is too small for reliable GWR — use pooled GWR across both hurricanes with a hurricane dummy, or restrict GWR to Helene (271 counties) only. Alternatively, use mixed GWR (some coefficients global, some local) to reduce parameter count.

### 9.10 Notebook (to be implemented as `regression_largest_drop_v3b.ipynb`)

1. Load precomputed metrics from distance-band / county-level analysis
2. Compute county centroid → track distance
3. Build custom distance matrix (track-distance based)
4. Run GWR with AICc bandwidth selection
5. Generate coefficient maps, local R² maps, significance maps
6. Compare with global OLS via AICc
7. Export results and maps

---

## 10. Core Outputs

### Regional Level

- 14 recovery time series (7 categories × 2 flow types: within + inflow) per hurricane
- Category-specific disruption profiles with Theil–Sen robust recovery slopes
- Comparative recovery bar charts (per flow type and cross-flow)
- Inflow plots with 2023 comparison reference
- Summary CSV: `recovery_summary_3flow.csv`

### Distance-Band Level (replacing per-county)

- Per-band SARIMAX baseline validation plots
- Per-band trend-based recovery plots (3–5 bands per hurricane)
- Band-level disruption and recovery metric CSVs

### Spatial Diagnostics (Milton)

- Scatter + LOWESS plots colored by distance-to-track (DV × IV pairs)
- OLS residual choropleth maps
- Residuals vs distance-to-track plots
- Moran's I summary table (Queen + KNN weights)
- Diagnostic summary CSV: `results/spatial_diagnostics_milton/diagnostic_summary.csv`

### Regression (GWR — Helene, pending)

- Local coefficient maps (spatial variation of socioeconomic effects)
- Local R² map
- Local significance maps
- AICc comparison: GWR vs global OLS
- Summary tables of coefficient ranges and spatial non-stationarity tests

---

## 11. Conceptual Contribution

This framework enables:

- Quantification of functional vulnerability across mobility categories
- Measurement of recovery dynamics following extreme weather
- Detection of **spatially varying** socioeconomic drivers of resilience through GWR
- Comparative assessment across hurricanes
- Analysis of disruption gradients along the hurricane track corridor

---

## 12. Key Files

| File | Purpose |
|------|---------|
| `trend_based_recovery_region_v2.ipynb` | Regional-level recovery analysis (7 categories × 2 flow types) |
| `regression_largest_drop_v2a.ipynb` | County-level data prep, baseline, metrics (Notebook 1) — to be updated to v3a with distance-band |
| `regression_largest_drop_v2b.ipynb` | County-level pooled OLS regression (Notebook 2) — baseline reference |
| `spatial_diagnostics_milton.ipynb` | Spatial diagnostics: LOWESS, Moran's I, residual maps (Milton N=21) |
| `recovery_function_v2.py` | Shared SARIMAX fitting and prediction functions (v2 bug fix) |
| `geoid_idx_names.csv` | County GEOID ↔ index mapping |
| `acs_socioeconomic_v2.csv` | Cached ACS socioeconomic variables |
| `largest_drop.md` | Task specification for county-level analysis notebooks |

---

## 13. Potential Extensions

- Multiscale GWR (MGWR): allow each predictor to have its own optimal bandwidth
- Nonlinear recovery models (exponential, piecewise)
- Hierarchical / Bayesian modeling for recovery with shrinkage across bands
- Interaction effects between distance-to-track and socioeconomic factors
- Network spillover analysis using the origin–destination tensor
- Temporal GWR for time-varying coefficient estimation

---

### Coding guidelines:
- Never edits the codes or notebooks directly. Instead, provide suggestions in the form of comments or markdown cells. Create a new version of the cell, code or notebook with the suggested changes, and share it for review. Always maintain a clear version history and document all changes made.
