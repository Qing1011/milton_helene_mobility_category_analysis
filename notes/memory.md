# Project Progress Log

## Project: Hurricane Mobility Disruption and Recovery Analysis
## Author: Qing Yao (qy2290@columbia.edu)

---

## Current Status (2026-03-26)

### Completed Components

1. **Regional-level recovery analysis** (`trend_based_recovery_region_v2.ipynb`)
   - SARIMAX baseline + Theil-Sen trend-based recovery for 7 categories × 3 flow types
   - Recovery summary CSVs and bar charts for both Milton and Helene
   - Inflow plots with 2023 comparison reference
   - Status: ✅ Complete

2. **County-level data prep and metrics** (`regression_largest_drop_v2a.ipynb`)
   - Per-county SARIMAX baseline (within, inflow, outflow)
   - Largest drop (within, inflow), outflow increase, trend-based recovery
   - Per-county recovery plots and baseline validation plots
   - Exports to `results/{hurricane}/`
   - Status: ✅ Complete, but county-level noise issues identified (see below)

3. **County-level OLS regression** (`regression_largest_drop_v2b.ipynb`)
   - Pooled OLS across both hurricanes with hurricane dummy
   - 5 DVs: largest_drop_{within,inflow}, outflow_increase, recovery_{within,inflow}
   - ACS socioeconomic predictors: population, income, no_vehicle, insurance
   - Full diagnostics: VIF, Breusch-Pagan, Shapiro-Wilk, Durbin-Watson
   - Status: ✅ Complete, but to be replaced by GWR approach

4. **Recovery function library** (`recovery_function_v2.py`)
   - v2 bug fix: X_train NaN masking corrected
   - Shared across all analysis notebooks
   - Status: ✅ Stable

5. **Existing figures** (`recovery_fig_v1/`)
   - Regional trend-based recovery bar charts (within, inflow, outflow) for Milton & Helene
   - Per-county relative difference plots (206 PNGs) — very noisy for small counties
   - Status: ✅ Generated, pending revision

---

### Decisions Made (2026-03-26)

1. **Outflow excluded from disruption/recovery analysis**
   - Outflow shows fundamentally different dynamics: evacuation surge (positive spike) for Milton vs drop for Helene
   - The trend-based recovery function only detects negative troughs → N/A for many Milton outflow categories
   - Decision: Report outflow increase as descriptive metric only; focus disruption/recovery on within-region and inflow (regional) or within-region only (county/band)
   - Rationale: Within-region captures local functioning; inflow captures aid/return dynamics at the regional level.

1b. **Inflow excluded at county/band level**
   - Inflow to a single county j from outside A is not meaningful — external origins have no reason to specifically visit county j
   - County-level inflow is dominated by idiosyncratic OD pairs, not systematic disruption signals
   - Decision: Inflow analyzed at regional level only; county/band-level analysis uses within-region flow exclusively
   - GWR dependent variables: `largest_drop_within` and `recovery_within` only

2. **Replace per-county analysis with distance-band aggregation**
   - Problem: County-level SARIMAX baselines are unstable for rural counties (low volumes → noisy time series → unreliable recovery estimates)
   - Solution: Group counties into distance bands from the hurricane track (e.g., 0-10mi, 10-25mi, 25-50mi)
   - Benefits: More stable baselines, natural spatial gradient, cleaner recovery estimation
   - Implementation: New notebook `regression_largest_drop_v3a.ipynb`

3. **Replace global OLS with Geographically Weighted Regression (GWR)**
   - Problem: OLS assumes spatially constant coefficients, but hurricane impacts are spatially graded
   - Solution: GWR with track-distance-based spatial kernel
   - Kernel: Weight observations by distance from county centroid to hurricane track
   - Bandwidth selection via AICc minimization
   - Implementation: New notebook `regression_largest_drop_v3b.ipynb` using `mgwr` package
   - Note: Milton (21 counties) too small for GWR alone; either pool with Helene or restrict to Helene (271 counties)

---

### Known Issues

1. **County-level noise**: Individual county time series (especially rural, low-population counties) produce very noisy relative deviations. SARIMAX baseline often has wide CI bands that encompass the true values, making recovery detection unreliable. → Addressed by distance-band aggregation.

2. **Helene outflow vs Milton outflow asymmetry**: Helene outflow drops below baseline (infrastructure damage prevented departure); Milton outflow surges above baseline (forecasted evacuation). This is a real physical difference, not a code bug. The current trend_based_recovery function is designed for recovery from drops and cannot measure recovery from positive spikes. → Addressed by excluding outflow from recovery analysis.

3. **Variable naming in `recovery_time_county.ipynb`**: The `region_out_counties()` function computes total outgoing trips (to ALL destinations including other selected counties), not pure outflow. The variable `Within_ts_merged` is actually merged category groups of total outgoing flow, not within-region flow. This notebook is superseded by `regression_largest_drop_v2a.ipynb` which correctly uses `ma.region_mobility()`.

4. **Milton sample size for GWR**: Only 21 counties within the 50-mile cutoff. GWR requires more spatial observations for reliable local estimation. Options: (a) pool both hurricanes with dummy, (b) restrict GWR to Helene, (c) use mixed GWR with some global coefficients.

---

### Next Steps (TODO)

- [x] Create `spatial_diagnostics_milton.ipynb` — scatter+LOWESS, Moran's I, residual maps (2026-03-26)
- [ ] **RUN the spatial diagnostics notebook** and interpret results to decide modelling approach:
  - If non-spatial nonlinearity → implement GAM
  - If spatial nonlinearity → implement distance interaction model
  - If threshold → implement piecewise regression
- [ ] Implement distance-band aggregation notebook (`regression_largest_drop_v3a.ipynb`) — for Helene
  - Compute county centroid → hurricane track distance
  - Define distance bands (0-10, 10-25, 25-50 miles or similar)
  - Aggregate mobility by band, fit SARIMAX, compute metrics
  - Generate band-level recovery plots
- [ ] Decide Helene county grouping strategy (distance-band vs spatial smoothing vs spatial clustering)
- [ ] Implement GWR for Helene (`regression_largest_drop_v3b.ipynb`) — after Helene grouping resolved
- [ ] Update `trend_based_recovery_region_v2.ipynb` to drop outflow recovery panels (keep outflow increase as descriptive)

---

### File Version History

| Date | File | Change |
|------|------|--------|
| 2025-01 | `recovery_function.py` | Initial SARIMAX + recovery functions |
| 2025-01 | `recovery_function_v2.py` | Fixed X_train NaN masking bug |
| 2025-02 | `regression_largest_drop_v2a.ipynb` | County-level data prep with correct flow decomposition |
| 2025-02 | `regression_largest_drop_v2b.ipynb` | Pooled OLS regression across hurricanes |
| 2025-02 | `trend_based_recovery_region_v2.ipynb` | Regional Theil-Sen recovery with 2023 comparison |
| 2026-03-26 | `CLAUDE.md` | Updated: outflow excluded from recovery; distance-band replaces county-level; GWR replaces OLS |
| 2026-03-26 | `memory.md` | Created: project progress tracking |
| 2026-03-26 | `CLAUDE.md` | Added Section 4.1 (flow scope by spatial scale); inflow excluded at county level |
| 2026-03-26 | `CLAUDE.md` | Added Section 8 (spatial diagnostics); renumbered GWR to Section 9; marked GWR as Helene-pending |
| 2026-03-26 | `spatial_diagnostics_milton.ipynb` | Created: LOWESS+distance color, OLS+Moran's I, residual maps for Milton N=21 |
