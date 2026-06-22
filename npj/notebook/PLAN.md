# npj 100-mi figure package — build plan (AGREED)

All notebooks live in `npj/notebook/`, run at the **100-mile cutoff**, and reuse code from the
existing `notebook/` originals (copy + repoint — originals left untouched).

## Global conventions (locked)
- **Cutoff:** 100 mi everywhere.
- **Local spatial units (REVISED 2026-06-19) = Helene CLUSTERS + Milton COUNTIES (primary).** Helene: 487 counties →
  **101 NCHS-homogeneous Queen-contiguity clusters** (it needs it — many tiny rural Appalachian units). **Milton:
  kept at COUNTY level, N=34** — its per-county within/inflow baselines are already stable (mostly large FL metros,
  NCHS 1–3); empirically (00c) clustering merged only 7/34 counties and blurred the most interpretable units
  (Charlotte's −46% drop, Okeechobee's slow recovery, coastal-vs-interior evacuation contrast), so it is **not**
  used for the primary. The **30-cluster Milton (00c) is retained as an appendix robustness check** showing the
  result is insensitive to clustering. Baseline/DVs/recovery per unit; **primary pooled = 101 Helene clusters + 34
  Milton counties = 135**. The asymmetry is data-driven (cluster where baselines are unstable, keep county-level
  where stable) and fine because the regression is separate-per-storm.
- **Outflow degeneracy = FLAG, don't drop.** Keep all units in the outflow DV; add an `outflow_degenerate` flag
  (mean outflow baseline < 3% of the storm's median outflow → Milton: Glades; Helene: cluster 99/Clinch) and let
  the regularized Bayesian priors absorb the noise. (Note: `largest_drop>0` on outflow is breakage for Helene but
  the normal evacuation surge for Milton.)
- **Categories:** 6 (Travel, Work & Professional, Health, Education, Retail & Leisure, Urban Government). No Utilities.
- **Regression design:** separate per-storm + comparative; **Bayesian primary, OLS supplementary**.
- **DVs:** 3 flow magnitudes — `largest_drop_within`, `largest_drop_inflow`, `largest_increase_outflow`.
  Recovery time is **NOT** a DV (notebook 04 is its justification).
- **Union / FEMA:** sensitivity + covariate only, never the primary sample.
- **Output dir:** `results/npj_100mi/` (figures flat with panel-prefixed names; intermediates in `results/npj_100mi/regional_data/`).
- **One panel = one file** (PDF + PNG, ≥300 dpi). No composites — panels assembled manually by the user.
- **Compute once, plot many.** Every analysis step **persists its figure-ready data to CSV** under `results/npj_100mi/`.
  Figure notebooks (01–06) **load those stored artifacts and only plot** — they must **never** re-run the heavy
  analysis (H5 tensor aggregation, calendar-AR(1) baseline fitting, MCMC sampling, GWR bandwidth search, Moran's I permutations).
  Re-styling a figure should take seconds, not a full re-run. Each plotting notebook starts by reading its
  input CSV(s); if a needed CSV is missing, that is a signal to (re)run the upstream *compute* notebook, not to
  inline the computation into the figure notebook.
- **Distance-band analysis is NOT a main figure** (cluster-level analysis supersedes it). It is retained as a
  **single Supplementary panel** (largest drop vs distance band, faceted by storm) only. The older
  `notes/figure_plan_npj_urban_sustainability.md` (50-mi, pooled-OLS, distance-band fig 4, GWR fig 6) is
  **superseded** — THIS file is the single live figure plan.
- **Physical-exposure covariates:** both **wind** and **precip** are tested in the driver regression (06a),
  as sensitivity covariates. 2024 wind is on disk at
  `global_tc_data-main/03_processed-data/global_hurr_dat/global_storm_winds_2024.rds` (Willoughby model, keyed on
  `ADM2_id` → map to GEOID via the repo's `04_sensitivity/4c_map_shapeID_to_fips`; metric = `vmax_sust`).

## Data-first workflow — stored artifacts (compute → CSV → plot)

| Producer (compute) | Stored figure-ready CSV | Consumed by (plot) |
|---|---|---|
| 00 | `npj_100mi/regional_data/{hrc}/baseline_{flow}_{cat}.csv`, `.../regional_metrics_summary_100mi.csv` | 01c, 02, 03 |
| **00d/00e** (Helene clusters), Milton county (old pipeline) | `results/local_level/{helene_100mi,milton_100mi}/metrics_{within,inflow,outflow}.csv`, `flow_ts_*.csv` | 04, 05 (read these dirs DIRECTLY) |
| `build_primary_pooled.py` → `build_exposure_dataset.py` (from 00d/00e + Milton county + wind/precip) | `results/local_level/regression/pooled_dataset_100mi_primary_exposure.csv` | 06a, 06b |
| 06a | `npj_100mi/drivers/ols_coefs_100mi.csv`, `bayes_posterior_summary_100mi.csv` (mean + 95% HDI per storm × DV × predictor) | 06a plots, manuscript table |
| 06b | `npj_100mi/drivers/morans_i_100mi.csv`, `gwr_local_coefs_helene_100mi.csv`, `gwr_diagnostics_100mi.csv` | 06b maps |

So the expensive steps (00's calendar-AR(1) baseline fits, 06a's MCMC, 06b's GWR/Moran's I) run **once** and write tables; everything
downstream re-reads those tables. This is exactly the pattern `regional_baseline.ipynb` → `regional_metrics.ipynb`
already uses, generalised to the whole package.

## Notebooks

| # | File | Deliverable | Reuses | Data | Status |
|---|---|---|---|---|---|
| 00 | `00_regional_flows_100mi.ipynb` | *prereq + validation gate* | `regional_baseline`, `regional_metrics`, `recovery_function_v2.py` | new compute | ✅ done |
| **00d** | `00d_helene_clustering.ipynb` | *Helene 487→101 clusters (PRIMARY units)* | `helene_spatial_clustering` | compute | ✅ done — reproduces canonical, Δ=0 |
| **00e** | `00e_helene_cluster_recompute.ipynb` | *Helene cluster flows/baseline/metrics (PRIMARY)* | `recompute_flows`,`local_baseline/metrics` | tensor | ✅ done — reproduces canonical, Δ=0 |
| **00b** | `00b_milton_clustering.ipynb` | *Milton 34→30 clusters (APPENDIX)* | `helene_spatial_clustering` | compute | ✅ done — **Milton-only** |
| **00c** | `00c_milton_cluster_recompute.ipynb` | *Milton cluster flows/baseline/metrics (APPENDIX)* | `recompute_flows`,`local_baseline/metrics` | tensor | ✅ done — **Milton-only** |
| 01 | `01_design.ipynb` | 1 — design / conceptual | `figure1_overview` | 1a/1b ready; 1c ← 00 | TODO (user) |
| 02 | `02_regional_heatmap.ipynb` | 2 — category heatmaps | `figure2_categories` | ← 00 | ✅ done |
| 03 | `03_regional_recovery.ipynb` | 3 — category recovery time | `figure3_flow_decomposition` | ← 00 | ✅ done |
| 04 | `04_local_recovery_time distribution.ipynb` | 4 — local recovery histograms (Helene cluster + Milton county) | `figure5b_recovery_descriptive` | metrics CSVs | ✅ done |
| 05 | `05_local_flow_maps.ipynb` | 5 — flow maps (main = **Helene cluster + Milton county**; appendix = Milton clustered + NCHS) | `figure_flow_maps` | Helene ← `helene_100mi/`; Milton ← `milton_100mi/` | **rebuild: Milton @ county** |
| 06a | `06a_global_drivers.ipynb` | 6 — per-storm OLS → Bayesian (+wind/precip) | `figure5_supp_bayesian_independent` | ← `…_primary_exposure.csv` | ✅ done |
| 06b | `06b_spatial_drivers.ipynb` | 6 — Moran's I + LISA + GWR (Helene) | `helene_gwr_100mi`, `gwr_compare_utils` | ← `…_primary_exposure.csv` | ✅ done |

**Local pipeline split (2026-06-22):** Helene clustering+recompute = `00d`+`00e` (PRIMARY units → `helene_100mi/`);
Milton clustering+recompute = `00b`+`00c` (APPENDIX clusters → `milton_clustered_100mi/`); each is **per-storm only**.
Cross-storm pooled datasets are assembled by standalone scripts (not the per-storm notebooks):
`build_primary_pooled.py` (Helene clusters + Milton **counties** = 135, PRIMARY), `build_exposure_dataset.py`
(+wind+precip), `build_clustered_pooled.py` (Helene + Milton **clusters** = 131, APPENDIX).

### 00 — regional flows (critical path)
Re-aggregate regional **within + inflow + outflow** per **6 categories × 2 storms** over the 100-mi county set
→ calendar-AR(1) baselines → trend-based recovery. Also serves as the **validation gate**: confirm baselines pass
diagnostics and category rankings stay sensible vs the 50-mi version. Outputs to `results/npj_100mi/regional_data/`.

### 00b / 00c — Milton clustering + recompute (NEW prerequisite)  ·  rule **B1**, **30 clusters**
Cluster Milton for the **appendix** robustness check only (Helene primary stays at 101 clusters; **Milton primary
stays at 34 counties**).
- **00b** (`helene_spatial_clustering` method, rule B1): load Milton 100-mi counties (34) + NCHS
  (`data/NCHS Urban-Rural Classification…csv`) + ACS + geometry → **merge only NCHS 4–6 with same-NCHS
  contiguous neighbours (connected components); NCHS 1–3 stay standalone** → **30 clusters**. Export
  `results/local_level/milton_clustered_100mi/county_cluster_assignments.csv` (county-level `milton_100mi/`
  kept untouched for the appendix). Also emit appendix maps: `figureB_nchs_milton` (NCHS code per county) and
  **`figureC_clusters_{milton,helene}`** — cluster-illustration maps with counties drawn (thin edges) and
  **cluster boundaries outlined (thick)** so merged groups are visible. The Helene map **reuses the existing
  101-cluster assignment** (no re-clustering). ✅ done.
- **00c** (`recompute_flows` + `helene_cluster_recovery`): aggregate the mobility tensor per Milton cluster →
  calendar-AR(1) baselines → DVs (within/inflow drop, outflow surge) → recovery → write
  `results/local_level/milton_clustered_100mi/metrics_{flow}.csv` (unit_id = cluster, same schema as
  `helene_100mi/`). Then build the **appendix** pooled regression dataset with Milton at cluster level (ACS
  aggregated per cluster) → `pooled_dataset_100mi_clustered.csv` (robustness fit only). The **PRIMARY** 04/05/06
  use Milton **counties** (`milton_100mi/`); the primary pooled is assembled by `build_primary_pooled.py`.

**Cluster dirs:** main/cluster = `helene_100mi/` + `milton_clustered_100mi/`; appendix/county = `milton_100mi/`.

### 01 — design
- 1a: study-area map, 100-mi envelopes + distance bands, both storms.
- 1b: tensor → 6 categories → within/inflow/outflow schematic.
- 1c: worked-example recovery series — **generated for all categories × both storms, each as a separate file** (user chooses + assembles).

### 02 — regional heatmaps
days × 6 categories, % deviation from baseline. **3 flows (within / inflow / outflow) × 2 storms = 6 panels**,
matching the existing 50-mi `figure2` layout. Each panel a separate file.

### 03 — regional recovery
Recovery time per category (matching the existing 50-mi figure). **Recovery only** — no largest-drop panel.
*[interpretation to confirm: per-category recovery-time bar chart, within vs inflow, per storm.]*

### 04 — local recovery distribution (Helene cluster + Milton county) — MATCH `figure5b_recovery_descriptive` style
Overlaid **histograms** (Helene blue + Milton red, α=0.55, white edges) of per-**unit** `recovery_days`
(**Helene = cluster, Milton = county** — the primary basis): y = "Number of units", x = "days from landfall",
dashed per-storm mean lines + μ/sd annotation box — exactly the **left column of the older
`results/npj_figures/figure5b_recovery_descriptive`** (code reused from `figure5_socioeconomic_drivers.ipynb`
panel b, col 0). **Within + inflow only** (outflow has no recovery — surge; the reference omits it too, which
resolves the earlier "all three" note). Bins: within `arange(0,18,1)`, inflow `arange(0,26,2)`. Built on the
**primary** units — Helene cluster metrics (`helene_100mi/`) + Milton **county** metrics (`milton_100mi/`),
i.e. the 135-unit primary sample (NOT the clustered appendix).

> **Recovery trough window = 10 days (updated 2026-06-22, was 7).** `trend_based_recovery` searches for the
> post-landfall trough within `trough_search_days` of landfall. At 7 d the trough for the most severely affected,
> *on-track* Helene clusters (median 30 mi from the track) was pinned to the window edge with the true minimum
> falling just outside — a left-censoring/boundary artifact that dropped 17 clusters to NaN (Helene inflow valid
> 72→**89**) and inflated one cluster's recovery to a 65-day linear extrapolation. A 10-day window captures the
> true (Oct-04+) trough; results are stable across 8–14 d, and windows >~2 weeks were avoided as they admit
> secondary, unrelated minima. The 12 remaining Helene-inflow NaNs are genuine inflow *surges* (no drop to
> recover from). Applied uniformly to **all flows + both storms, local AND regional**. Helene inflow max recovery
> drops 65→24 d; sd 7.9→4.2 d. Regenerate via `_recompute_recovery_10d.py` (reuses saved baselines, no refit).

### 05 — local flow maps  (MAIN = **Helene clusters + Milton counties**; appendix = Milton clustered + NCHS map)

> **REQUEST (locked 2026-06-22):** Produce the **flow maps for both hurricanes** at the **100-mi** cutoff,
> showing the **three flow DVs as choropleth maps** — within-drop, inflow-drop, outflow-surge. The spatial unit
> basis is **asymmetric and matches the locked primary sample**: flows are generated **per county for Milton**
> and **per cluster for Helene**. **Milton's clustering is NOT a main result** — the **county level is the main
> result for Milton**; the 30-cluster Milton version is kept only as an appendix robustness check.

- **Main** (`figure5_flow_maps`): 2×3 choropleth, rows = storms, cols = within / inflow / outflow; metric =
  drop / drop / increase; RdBu, **per-column shared scale with a robust 98th-pct cap** (a Helene outflow cluster
  has a degenerate-baseline +12595% outlier). **Helene** drawn at **cluster level** (cluster value spread onto
  member counties); **Milton** drawn at **county level** (native per-county metrics from `milton_100mi/` — its
  per-county baselines are stable, so no clustering is applied for the main figure).
- **Appendix A** (`figureA_flow_maps_milton_clustered`): Milton **30-cluster** version of the same three DV maps,
  as a robustness check demonstrating the result is insensitive to clustering (it barely merges 7/34 counties).
  A Helene **county-level** panel may accompany it to show why Helene *needs* clustering (its per-county baselines
  are the unstable ones); label accordingly.
- **Appendix B** (`figureB_nchs_map`): rural-urban **NCHS code** choropleth per storm (reuse the map cell from
  `helene_spatial_clustering`), showing the merge basis.

### 06a — global drivers (order: OLS → Bayesian), PRIMARY units (Helene cluster + Milton county)
Per storm, 3 DVs, 10-predictor z-scored spec, on the **primary** pooled dataset — **Helene 101 clusters + Milton
34 counties = 135** (`results/local_level/regression/pooled_dataset_100mi_primary_exposure.csv`, +wind/precip).
OLS (baseline + VIF) then Bayesian (regularized **primary**: forest + overlay + vs-OLS). The Milton-**clustered**
pooled dataset (131 units) is the **appendix** robustness fit only.

### 06b — spatial drivers (order: Moran's I → LISA → GWR), PRIMARY units (Helene cluster + Milton county)
- Moran's I (**Queen + KNN k=4**) on each DV and on OLS residuals — spatial weights over the **primary units**
  (Helene clusters; Milton counties — same units as the 06a regression).
- **LISA** cluster maps for the storm×DV combos with significant global Moran's I (both storms).
- **No DV choropleths here.** The standalone `figure6b_dvmap_*` panels were **dropped as redundant (2026-06-22)** —
  the flow-DV maps are **Figure 5** (`05_local_flow_maps`). 06b outputs only Moran's I tables, LISA maps, and GWR.
- GWR **Helene only**.
- **Support for no Milton GWR:** Milton is only **n=34 counties**; the diagnostic (adaptive bandwidth collapses
  toward global n / local condition-number blow-up at n≈34 with the 10-predictor set) shows GWR is not
  identifiable, so the omission is demonstrated, not asserted.

## Item-6 order: Option A executed as C
A (analytical chain) split into two notebooks: 06a global (OLS→Bayesian), 06b spatial (Moran's I→GWR).

## Build order
1. `00` regional ✅ → `02`, `03` ✅ (regional, cutoff-validated).
2. **`00b` Milton clustering → `00c` Milton cluster recompute + rebuild clustered pooled dataset** (NEW, do next).
3. **Rebuild `04` and `05`.** `05` flow maps with **Helene @ cluster + Milton @ county (main)**; Milton-clustered
   + NCHS maps as appendix. (`04` recovery dist — see its section.)
4. `01` design → `06a` (primary: Helene cluster + Milton county) → `06b` (same primary units).

Note: `02`/`03` are **regional** (whole-region aggregate per category) and are unaffected by the local
clustering change — they stay as built.
