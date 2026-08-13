# `manuscript_numbers.csv` — frozen single source of truth

**Built:** 2026-08-13 by [`npj/notebook/_phase1_manuscript_numbers.py`](../../npj/notebook/_phase1_manuscript_numbers.py)
**For:** *Nature Cities* Brief Communication (see [`notes/finalisation_plan.md`](../../notes/finalisation_plan.md))

Every number the manuscript quotes must come from this file, cited by its `id`. Each row carries
**scale** (regional | local), **sample** (all_units | 20k_cut | 6 categories), and **n**, so no value
can be used without its basis attached.

`block` routes each number to where it is used: `P2` (¶2, the recovery contrast), `P3` (¶3, spatial +
drivers), `METHODS`, `SI`.

---

## 1. The headline, frozen

Under decision **D2** the headline is *external reconnection, not local restart*. Both halves are now
computed on the same sample (20k-cut, matching the Figure 1 histograms) from the canonical 10-day-window
metrics:

| Quantity | Helene | Milton | Test |
|---|---|---|---|
| **Local restart** (within recovery) | 4.4 d [3.7, 5.1] · n = 96 | 4.5 d [4.1, 5.4] · n = 33 | **p = 0.294 — no difference** |
| **External reconnection** (inflow recovery) | 11.1 d [8.7, 13.4] · n = 46 | 5.1 d [4.2, 6.2] · n = 28 | **p < 0.001 — 2.2× gap** |
| Shock depth, within | −15% [−17, −11] | −27% [−33, −20] | p < 0.001 |
| Shock depth, inflow | −20% [−29, −13] | −33% [−42, −24] | p < 0.001 |

Regional (6 categories) corroborates and is the "holds across all six categories" clause:
inflow recovery **11.3–13.3 d** (Helene) vs **4.4–5.5 d** (Milton).

### Two guardrails the drafting must respect

1. **Never imply Milton recovers faster in general.** At the regional scale Helene's *within* recovery
   is **faster** (3.2–5.1 d vs 4.7–6.1 d), and at local scale the two are tied (p = 0.29). The gap is
   inflow-only. This is the point of the paper, not a caveat to bury.
2. **Outflow surge does not differ between storms** — Helene 19% [5, 31] vs Milton 18% [−3, 55],
   **p = 0.991**. Milton's evacuation is far more *dispersed* (IQR spans −3 to 55), i.e. concentrated in
   specific coastal units rather than region-wide. Do not repeat the older framing of a Milton-wide
   evacuation surge without this qualification.

---

## 2. The four Helene-inflow *n*'s, reconciled

All four are correct; they are nested subsets. Quote **one** in the main text and put the rest here.

| *n* | What it is | Where it belongs |
|---|---|---|
| **101** | all Helene clusters, before any gate | Methods (unit definition) |
| **89** | clusters with a valid inflow recovery (10-d trough window) | SI; the 12 NaNs are genuine inflow *surges* with no drop to recover from |
| **52** | 20k-cut inflow sample (baseline mean ≥ 20,000 visits/day) | ¶3 — this is the 06a/06b regression *n* |
| **46** | 20k-cut units with a valid inflow recovery | ¶2 — **the Figure 1 histogram *n*** |

---

## 3. ⚠ Defect found: Table 1's Recovery rows are stale

`results/npj_100mi/drivers/table1_hev_descriptives.csv` reports **Helene inflow recovery = 11 [8, 13],
n = 72**. That is a **7-day-trough-window** value.

**Cause.** `_table1_hev_descriptives.py` reads `pooled_dataset_100mi_primary_exposure.csv`, written
**2026-06-22 13:36** — *before* `_recompute_recovery_10d.py` regenerated the metrics at **16:56** with the
10-day window (`PLAN.md`: "Helene inflow valid 72 → 89"). The rebuilt `pooled_dataset_100mi_primary.csv`
(17:37) has the correct 89; the `_exposure` variant was never refreshed.

**Blast radius — contained:**

| Artefact | Affected? | Why |
|---|---|---|
| Table 1, two `Recovery` rows | ❌ **stale** | reads the un-refreshed column (n = 72, median 11.03 vs canonical n = 89, median 11.31) |
| 06a / 06b regressions, all Bayesian + GWR + Moran results | ✅ **unaffected** | the three DVs are flow *magnitudes*; `largest_drop` / `largest_increase` do not depend on `trough_search_days`, and are **byte-identical** across both pooled files (verified) |
| Figure 4 / Figure 1 histograms | ✅ **unaffected** | notebook 04 reads the canonical `{storm}_100mi/metrics_*.csv` directly, per `PLAN.md` |
| `manuscript_numbers.csv` | ✅ **correct** | recovery is always read from the canonical metrics, never from the pooled file |

**Action before submission:** regenerate Table 1 against the canonical metrics (Table 1 is SI-bound under
the BC format, so this is not on the critical path). The median moves 11.03 → 11.31 d — the story does not
change, only the *n* and IQR.

---

## 4. Drivers and spatial structure (¶3)

Four credible effects (95% HDI excludes zero), **all Helene**:

| Predictor → DV | Posterior mean [95% HDI] | n |
|---|---|---|
| `is_coastal` → within drop | −4.9 [−8.6, −1.3] | 96 |
| `pct_white` → inflow drop | −7.0 [−11.0, −3.4] | 52 |
| `precip_total_7day` → inflow drop | −9.0 [−14.3, −3.5] | 52 |
| `dist_to_track_mi` → outflow surge | −19.9 [−29.6, −9.2] | 74 |

**Milton: zero of 27 predictor × DV effects credible** (n ≈ 28–33). State this explicitly as
*underpowered*, never as evidence of absence.

**Spatial GAM.** Inflow is the **only** flow with significant smooth geography — `s(x,y)` p = 0.023,
deviance explained 0.15 → 0.52. Within (p = 0.87) and outflow (p = 0.86) have none.

> ⚠ **The tension ¶3 must handle honestly.** Inflow carries the headline recovery gap *and* is the one
> flow whose socioeconomic association (`pct_white`) collapses under spatial control. Do not let the prose
> imply the reconnection gap is *explained by race*. The defensible statement is that socioeconomic
> structure is **not separably identifiable from geography** for this flow — adding a spatial smooth can
> null a genuinely spatially-structured effect (Hodges & Reich 2010; Paciorek 2010). Exposure
> (precipitation, coastal, track distance) is the survivor.

---

## 5. Regenerating

```bash
/opt/homebrew/Caskroom/miniforge/base/envs/extreme/bin/python npj/notebook/_phase1_manuscript_numbers.py
```

Read-only with respect to all upstream artefacts; safe to re-run. If any upstream CSV is refreshed,
re-run this and re-check every `id` cited in the manuscript.
