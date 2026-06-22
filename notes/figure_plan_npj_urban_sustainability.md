# Figure Plan — npj Urban Sustainability Submission

> ⚠️ **SUPERSEDED (2026-06-19, rev. 2026-06-22).** This plan reflects the earlier design (50-mi cutoff, pooled OLS
> with `is_milton`, distance-band as Figure 4, GWR as Figure 6). The **live figure plan is now `npj/notebook/PLAN.md`**
> (100-mi; local units = **Helene clusters + Milton counties (primary)**, Milton clustering = appendix robustness;
> separate per-storm Bayesian primary; distance-band demoted to a single Supplementary panel). Kept for history only
> — do not build from this file.

**Target journal**: npj Urban Sustainability (Nature Portfolio)
**Paper**: Hurricane mobility disruption and recovery — Helene (2024-09-26) & Milton (2024-10-09)

---

## IMPORTANT: Category exclusion

**Do NOT include the Utilities category in any figure.**

All analyses, plots, bar charts, heatmaps, and comparisons should use **6 categories only**:

1. Travel
2. Work & Professional
3. Health
4. Education
5. Retail & Leisure
6. Urban Government

(Utilities is excluded from all main and supplementary figures.)

All counts in this plan that previously referenced "7 categories" should be read as **6 categories**. Time-series matrices (e.g., 6 categories × 2 flow types = **12 series** at the regional level, not 14).

---

## Journal constraints

- Main display items: up to 8 (figures + tables combined); typical articles use 4–6 main figures.
- Width: 89 mm (single column) or 183 mm (double column); ≥300 dpi; vector format preferred (PDF/EPS).
- Sans-serif font (Arial/Helvetica), bold lowercase panel labels (`a`, `b`, `c`…), colorblind-safe palettes that survive greyscale conversion.
- Self-contained captions stating *n*, statistical test, effect direction.
- Editorial preference for integrative multi-panel figures with one narrative beat per figure.

---

## Main figures (6)

### Figure 1 — Study setup and conceptual framework
- **(a)** Map: Helene + Milton tracks, the 50-mile affected envelopes, distance bands (0–10 / 10–25 / 25–50 mi), county shading.
- **(b)** Schematic: 4-D mobility tensor → 6 categories → within / inflow / outflow decomposition at regional vs. local scales.
- **(c)** Worked example time series for one category (raw, calendar-AR(1) baseline + CI, trough, Theil–Sen recovery slope, recovery time annotation).

*Purpose: anchor the methodology in one read.*

### Figure 2 — Regional disruption & recovery across the 6 mobility categories
- **(a–b)** Heatmap or small-multiples of relative deviation (% from baseline) across days × 6 categories, one panel per hurricane.
- **(c)** Grouped bar chart: largest drop (within) per category, Helene vs. Milton.
- **(d)** Grouped bar chart: trend-based recovery time per category.

*Purpose: which urban functions are most vulnerable / slowest to recover.*

### Figure 3 — Flow-type decomposition (within / inflow / outflow)
- **(a)** Within vs. inflow recovery times across the 6 categories (paired bars).
- **(b)** Outflow surge (evacuation) per category, with the −3d to +6d window highlighted.
- **(c)** One illustrative category (e.g., Health or Retail & Leisure) showing all three flows on one time axis.

*Purpose: "recovery" depends on which network direction you measure.*

### Figure 4 — Distance-band gradient
- **(a)** Largest drop vs. distance band (3 bands × 6 categories), facetted by hurricane.
- **(b)** Recovery time vs. distance band.
- **(c)** Map: counties colored by band-level recovery for one diagnostic category.

*Purpose: connect physical exposure gradient to functional response.*

### Figure 5 — Socioeconomic drivers (pooled OLS, Helene + Milton)
- **(a)** Forest plot of standardized coefficients for the significant predictors (`is_milton`, distance, insurance, income, `is_coastal`, `pct_white`) across the 4 well-fit DVs.
- **(b)** Partial-effect plot for **insurance coverage** (protective across all within metrics — most robust finding).
- **(c)** Partial-effect plot for **income** showing the evacuation-vs-return paradox (↑ outflow surge, ↑ recovery days).

*Purpose: carry the inequity/sustainability message npj cares about.*

### Figure 6 — Spatial heterogeneity
- **(a)** Moran's I residual map for outflow increase (Milton) — spatial clustering of evacuation.
- **(b–d)** GWR local coefficient maps for Helene (income, insurance, vehicle access) + local R².

*Fallback if GWR not ready by submission*: replace b–d with Milton quartile boxplots and LOWESS scatter colored by distance-to-track from `spatial_diagnostics_milton.ipynb`.

*Purpose: close the loop on "spatially varying drivers of urban resilience."*

---

## Supplementary figures

- calendar-AR(1) baseline validation per category × region (residual diagnostics, 2023 holdout overlay).
- Full **12** regional recovery panels (6 categories × within/inflow) for each hurricane.
- Per-county recovery plots for Milton (N=21); cluster-level for Helene.
- Sensitivity to distance-band cutoffs and the 50-mile affected-region threshold.
- Robustness check without Okeechobee (stability of insurance effect).
- Correlation matrix / VIF table for ACS predictors.

---

## Tables (count against the 8-item budget)

- **Table 1**: Hurricane + sample descriptors (counties, population, 6 categories, study window).
- **Table 2**: Pooled OLS results for the 4 well-fit DVs (standardized coefficients, robust SE, *n*, R²).

---

## Practical reminders

- Build all figures at final print size from the start — never scale up.
- Use one consistent diverging palette for % deviation (e.g., RdBu) and one categorical palette for the 6 categories across **all** figures.
- npj reviewers tend to ask for effect sizes + CIs over p-values — show CIs on every bar and forest plot.
- Verify the latest figure-file spec on the [npj Urban Sustainability submission guidelines](https://www.nature.com/npjurbansustain/submission-guidelines) immediately before submission.
