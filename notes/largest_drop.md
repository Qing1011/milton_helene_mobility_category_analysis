# Tasks

To investigate the maximum reduction in county-level mobility (aggregated across all categories) during hurricane events, measure trend-based recovery time, and analyze associations with local socioeconomic factors.

Flow types analyzed: **within-region** (A→A), **inflow** (not_A→A), **outflow** (A→not_A).

---

## Notebook 1: Data Preparation, Baseline, and Recovery Metrics (`regression_largest_drop_v2a.ipynb`)
**Objective:** Process raw mobility data, establish SARIMAX baselines, compute disruption and recovery metrics per county, export results and per-county plots.

- **Data Loading & Flow Decomposition**: Load weekly H5 mobility files and decompose into within-region, inflow, and outflow per county using `ma.region_mobility()`. Sum all 17 raw categories to get total county-level flow for each flow type.

- **Baseline Computation**: For each county and flow type, fit a SARIMAX model (AR(1) with day-of-week, month, and year dummies) on pre-hurricane training data (2023 Jul–Oct + 2024 Jul to 7 days before landing). Uses `recovery_function_v2.py` which fixes the X_train NaN masking bug from v1.

- **Largest Drop Calculation** (within, inflow): Compute relative deviation from baseline and identify the minimum % deviation during the landing week [landing, landing+6d].

- **Outflow Increase Calculation**: Compute the maximum positive % deviation above baseline during a 2-week window [landing−7d, landing+6d] to capture pre-landfall evacuation surge.

- **Trend-Based Recovery Time** (within, inflow): Apply smoothed relative deviation → trough detection → monotonic recovery segment extraction → Theil–Sen robust slope fitting. Recovery time measured from landing date: τ = (trough − landing) + (−intercept / slope).

- **Visual Validation**: Export per-county baseline validation plots (observed vs predicted with 95% CI) and per-county recovery plots (raw/smoothed deviation, trough, monotonic segment, Theil–Sen fit, recovery annotation).

- **Data Export**: Export per hurricane to `results/{hurricane}/`:
  - `baseline_{within,inflow,outflow}.csv` — SARIMAX predictions
  - `largest_drop_{within,inflow}.csv` — peak disruption
  - `outflow_increase.csv` — evacuation surge
  - `recovery_{within,inflow}.csv` — trend-based recovery time
  - `figures/` — per-county baseline + recovery plots

---

## Notebook 2: Impact Assessment and Socioeconomic Analysis (`regression_largest_drop_v2b.ipynb`)
**Objective:** Quantify the mobility drop against baselines computed in Notebook 1, integrate ACS socioeconomic variables, and run OLS regressions with full diagnostics.

- **Import Precomputed Results:** Load `largest_drop_{within,inflow}.csv` from Notebook 1 for both hurricanes. No raw H5 loading required.

- **Socioeconomic Data Integration:** Download (or load cached) ACS 2022 5-year estimates and merge with drop results on integer GEOID. Variables:
  - `total_population` (B01003)
  - `median_household_income` (B19013)
  - `pct_no_vehicle` — % households without vehicle (B08201)
  - `insurance_coverage_pct` — % with health insurance coverage (B27010)
  - Note: `poverty_rate_pct` dropped (correlated with income); `insurance_coverage_pct` added in v2.

- **Exploratory Data Analysis (EDA):** Scatter plots of each feature vs largest drop with Pearson/Spearman correlation, correlation heatmaps, and drop distribution histograms. Generated per hurricane × flow type.

- **Regression Modeling:** OLS regression with standardized coefficients, run separately for each hurricane × flow type combination. Full diagnostics include:
  - Variance Inflation Factor (VIF) for multicollinearity
  - Breusch-Pagan test for heteroscedasticity
  - Shapiro-Wilk test for residual normality
  - Durbin-Watson statistic for autocorrelation
  - Diagnostic plots: residuals vs fitted, Q-Q, histogram, scale-location

- **Cross-Hurricane Comparison:** Grouped bar charts of standardized coefficients by hurricane, combined scatter plots (drop vs income, colored by hurricane, sized by population), and model summary table (R², Adj. R², F-stat).

- **Final Results Export:** Regression text summaries and coefficient CSVs exported per hurricane to `results/{hurricane}/`.