# Finalisation plan — *Nature Cities* **Brief Communication**

**Created:** 2026-08-13
**Live spec:** [`npj/notebook/PLAN.md`](../npj/notebook/PLAN.md) (build) + [`npj/manuscript_nature_cities.md`](../npj/manuscript_nature_cities.md) (framing)
**Status of analysis:** complete. **Status of manuscript:** no draft exists in the live design.

## Locked decisions (2026-08-13)

- **D1 — Format: Brief Communication.** ≤1,500 words, no headings, 3-sentence/≤70-word unreferenced
  abstract, **≤2 displays**, Methods ≤500 words, ~20 references, title ≤10 words / ≤90 char.
- **D2 — Headline: external reconnection, not local restart.** Local activity restarts in ~4.5 d in
  *both* storms; what differs 2× is how long the region stays cut off from outside (5 d vs 11 d).
- **D3 — Data source: draft with `[PROVIDER]` placeholders** in the standard Nature proprietary-data form.

**Consequence of D1:** the work is now **compression and framing, not more analysis**. Five of seven built
figures, both tables, and the entire pooled 06c/08c package move to Supplementary. Nothing needs recomputing.

---

## 0. State of play

| Component | State |
|---|---|
| Compute notebooks (00, 00b–00e, 06a, 06b, 06c, 08, 08c) | ✅ all run, artifacts on disk |
| Panel files in `results/npj_100mi/` | ✅ complete (PDF + PNG ≥300 dpi) |
| Assembled composites (`npj/figure/400ppi/`) | ✅ design, heatmap, regional_recovery, local_analysis |
| `npj/figure/spatial_drivers.ai` | ⚠️ assembled 2026-06-27, no 400 ppi export — **now needed for Fig 2** |
| Fig 7 (Moran + GAM collapse + `s(x,y)`) | ⚠️ panels exist, composite does not — **now SI, lower priority** |
| Tables 1 & 2 | ⚠️ source CSVs exist — **now SI (a table counts against the 2-display cap)** |
| Manuscript prose | ❌ **only a stale draft from the retired design** |
| Data / code availability statements | ❌ not written |

**The stale draft.** `npj/Helene_Milton_manuscript_npj_V2_QY.docx` (2026-05-24) is built on the *retired*
specification — 50-mi cutoff, N = 292, pooled OLS with `is_milton`, distance-band aggregation, 7-day trough
window, "GWR ongoing." Its Results section reports superseded numbers, and its §3.2 + Discussion are built
around the distance-to-track "counterintuitive result" that `notes/findings.md` **retracted** as a 50-mi
sample-selection artefact. Under a BC it is doubly obsolete (wrong design *and* 16× the allowed length).
Mine it for Introduction framing and reference scaffolding only.

---

## 1. Phase 1 — Freeze the numbers ✅ **COMPLETE 2026-08-13**

**Delivered:** [`results/npj_100mi/manuscript_numbers.csv`](../results/npj_100mi/manuscript_numbers.csv)
(69 frozen numbers, each tagged with scale / sample / n and routed to a manuscript block) +
[`MANUSCRIPT_NUMBERS_README.md`](../results/npj_100mi/MANUSCRIPT_NUMBERS_README.md), built by
[`npj/notebook/_phase1_manuscript_numbers.py`](../npj/notebook/_phase1_manuscript_numbers.py) (read-only,
re-runnable).

**Headline confirmed and now on one consistent sample** (20k-cut, matching the Fig 1 histograms):
local restart 4.4 d [3.7, 5.1] vs 4.5 d [4.1, 5.4], **p = 0.294**; external reconnection
11.1 d [8.7, 13.4] vs 5.1 d [4.2, 6.2], **p < 0.001**.

**Two findings that change the drafting:**
1. ⚠ **Table 1's two Recovery rows are stale** — built from a pooled intermediate written 3 h before the
   10-day-window regeneration. Regressions, GWR, Moran and Fig 4 are all unaffected (verified: the three
   regression DVs are byte-identical across both builds). Regenerate Table 1 before submission; it is
   SI-bound under the BC, so off the critical path. Full diagnosis in the README §3.
2. **Outflow surge does not differ between storms** (19% vs 18%, **p = 0.991**); Milton's is merely far
   more dispersed. The older "Milton-wide evacuation surge" framing must not be repeated unqualified.

Original checklist, all discharged:

- [ ] **Convention (was an open item in PLAN.md):** under D2 the headline is a *recovery* number, so lead
      with **local medians + IQR** (the unit-level distribution behind Fig 1) and quote regional category
      ranges only as the "holds across all six categories" support clause.
- [ ] **Reconcile the four Helene-inflow *n*'s** — 89 (all clusters, 10-d window) / 72 (Table 1 recovery) /
      52 (06a regression, 20k-cut) / 46 (Fig 4 recovery, 20k-cut). Each is correct for its subset; every use
      in text or caption must name the basis. At BC length, prefer quoting **one** *n* in the main text and
      putting the rest in the SI methods table.
- [ ] **Freeze the recovery numbers actually supported:**
  - within, local: Helene 4.4 d [3.7, 5.1] vs Milton 4.5 d [4.1, 5.3], **p = 0.29 (n.s.)** ← the null that carries the headline
  - within, regional: Helene 2.8–5.1 d vs Milton 4.2–6.1 d (Helene *faster* — do not imply otherwise)
  - inflow, local: Helene 11 d [8, 13] vs Milton 5.1 d [3.8, 6.1], **p < 0.001**
  - inflow, regional: Helene 11.3–13.3 d vs Milton 4.4–5.5 d
- [ ] **Freeze the shock-depth numbers:** local medians −15% (Helene) vs −27% (Milton) within, p < 0.001;
      regional category ranges 8–13% vs 24–45%.
- [ ] **Freeze the four credible Bayesian effects** (95% HDI excludes 0), all **Helene**: `is_coastal` →
      within drop −4.9 [−8.6, −1.3]; `pct_white` → inflow drop −7.0 [−11.0, −3.4]; `precip_total_7day` →
      inflow drop −9.0 [−14.3, −3.5]; `dist_to_track_mi` → outflow surge −19.9 [−29.6, −9.2].
      **Milton: none** (underpowered, n ≈ 28–33) — say so explicitly rather than leaving it implied.
- [ ] **Freeze the GAM verdict:** inflow `s(x,y)` p = 0.023, deviance explained 0.15 → 0.52;
      `income_varies_p` = 0.118, `insurance_varies_p` = 0.192. Within and outflow: no spatial structure
      (p = 0.87, 0.86).

> ⚠️ **Note the tension to handle honestly in ¶3:** inflow is both the flow that carries the headline recovery
> gap *and* the only flow where `s(x,y)` is significant — i.e. its socioeconomic associations (`pct_white`)
> are the ones that collapse under spatial control. This is not a problem for the paper, but the drafting must
> not accidentally imply the reconnection gap is *explained* by race.

---

## 2. Phase 2 — The two displays ✅ **LOCKED 2026-08-13**

The BC cap is on **display items** (≤2), not panels — so each display may carry multiple panels.

### Fig 1 — the recovery contrast (the headline)
Rebuild from `local_analysis.png` / `figure4_recovery_{within,inflow}`: overlaid per-unit recovery
histograms, Helene blue vs Milton red.

| Panel | Source | Carries |
|---|---|---|
| **1a** within recovery | `figure4_recovery_within` | the **null** — two near-identical distributions (4.4 vs 4.5 d, p = 0.294) |
| **1b** inflow recovery | `figure4_recovery_inflow` | the **gap** — clean separation (11.1 vs 5.1 d, p < 0.001) |
| *1c (optional)* | `figure3_recovery_inflow_HvM` | the gap holds across all six categories |

Both panels must be drawn on the **20k-cut sample** (n = 96/33 within, 46/28 inflow) so the histogram *n*
matches the ¶2 text. The 1a/1b juxtaposition **is** the argument — same axis scale across both panels so the
reader sees the separation appear.

### Fig 2 — where and why (confirmed 2026-08-13)

| Panel | Source | Carries |
|---|---|---|
| **2a** inflow-drop choropleth, both storms | `figure5_flow_maps` (**inflow column** of the 2×3) | *where* the reconnection deficit sits |
| **2b** Helene driver forest, 3 DVs | `drivers/figure6a_hev_per_storm` | exposure governs shock: the 4 credible effects (`is_coastal`, `pct_white`, `precip_total_7day`, `dist_to_track_mi`) |
| **2c** GAM coefficient collapse, inflow | `spatial/figures/figure_gam_inflow_coefs` | `pct_white` → β ≈ 0 once `s(x,y)` enters (p = 0.023, dev. expl. 0.15 → 0.52) |

**Why 2c earns its place despite BC compression.** 2b shows `pct_white` → inflow drop as credible
(−7.0 [−11.0, −3.4]); 2c shows it collapses under spatial control. Carrying **both in one display** makes the
figure tell the honest story by itself, and it is what licenses ¶3's "not separably identifiable from
geography" wording. Without 2c, ¶3 either over-claims that race drives the reconnection gap or hedges
without visible support.

**Blocker:** `npj/figure/spatial_drivers.ai` (2026-06-27) has **no 400 ppi export**. Check first whether that
existing assembly already covers 2b + 2c before rebuilding — if so, Fig 2 is a merge of it with the 2a map
rather than a fresh assembly.

**Demoted to SI by this choice:** category heatmaps, regional recovery (Fig 3), the within/outflow columns of
the flow maps, `figure_gam_inflow_sxy`, `figure6b_moran_summary`, all GWR/LISA panels, Tables 1–2, every
sensitivity analysis, and the pooled 06c/08c package (referee-rebuttal asset, not cited in main text).

Everything else → Supplementary: heatmaps (Fig 2 old), regional recovery (Fig 3 old), full flow maps (Fig 5
old), Moran/LISA/GWR (06b), GAM panels (08), Tables 1–2, the 20k-cut and no-wind sensitivities, the
`uncut/` and `with_pop/` archives, and the pooled 06c/08c package (retained as a referee-rebuttal asset per
PLAN.md, not cited in the main text).

---

## 3. Phase 3 — Write the Brief Communication

**Word budget (~1,500 total, no headings):**

| Block | Words | Content |
|---|---|---|
| ¶1 | ~200 | Stakes (climate-intensified hurricanes, mobility as urban function) → gap (single-event, single-scale studies; rural–urban recovery unexamined) → **"Here we show…"** stating the two-storm comparison and the within/inflow/outflow decomposition |
| ¶2 | ~350 | **Fig 1.** Milton's shock is deeper (−27% vs −15% local median); local restart is identical (~4.5 d, p = 0.29); inflow reconnection differs 2× (5.1 vs 11 d, p < 0.001); holds across all six categories and both scales |
| ¶3 | ~350 | **Fig 2.** Where the deficit sits spatially; exposure (coastal, precipitation, track distance) governs shock magnitude in Helene; Milton underpowered; SES not separably identifiable from geography |
| ¶4 | ~200 | Policy implication (target rural *isolation*, not peak coastal disruption) → n = 2 confound as an honest bound motivating multi-storm work → one-sentence outlook |

**Draft abstract (3 sentences, 67 words — verify before submission):**

> Climate-intensified hurricanes disrupt urban mobility, yet whether recovery is equitable across the
> rural–urban gradient is unclear. Analysing device-based mobility for Hurricanes Helene and Milton, we find
> local activity restarted within ~4.5 days in both storms, whereas reconnection to the outside world took
> 5 days in coastal-urban Florida but 11 in inland-rural Appalachia. The gap lies in external reconnection,
> not local restart, implying planners should target rural isolation.

**Title candidates (≤10 words / ≤90 char):**
1. *Hurricane recovery gaps lie in reconnection, not local restart* — 9 w, 61 ch
2. *Rural isolation, not local disruption, paces hurricane mobility recovery* — 9 w, 71 ch
3. *Inland-rural regions stay cut off twice as long after hurricanes* — 10 w, 65 ch

**Section source map:**

| Block | Build from | Do **not** reuse |
|---|---|---|
| ¶1 | stale draft ¶1–3 (framing still valid, compress ~10×), `literature_review.md` | — |
| ¶2 | `figure4_recovery_stats.csv`, `table1_hev_descriptives.csv`, `regional_metrics_summary_100mi.csv` | any 50-mi / N = 292 number |
| ¶3 | `bayes_posterior_summary_100mi.csv`, `gam_verdict_100mi.csv`, `morans_i_100mi.csv` | the whole pooled-OLS §3.2; "insurance is protective" (pooled-OLS artefact) |
| ¶4 | `manuscript_nature_cities.md` limitations block | the retracted distance-to-track narrative |
| Methods (≤500 w) | `notes/methods_baseline_model.md` — publication-grade but **needs ~5× compression**; full version → SI | stale §2.4/§2.5 (distance-band, GWR-as-primary) |

**Language discipline** (`nature_cities_brief_style_report.md` §5): active voice, "Here we show…", inline
numbers, one idea per sentence. No jargon in main text — "credible interval" not "posterior HDI",
"deviation from expected mobility" not "calendar-AR(1) baseline", "local clusters of severe disruption" not
"LISA quadrant". Assertive on measurements; hedged on generality and mechanism.

**Spatial-confounding wording is precise and non-negotiable** — "socioeconomic status is not separably
identifiable from geography," never "no socioeconomic effect." Adding a spatial smooth can null a genuinely
spatially-structured effect (Hodges & Reich 2010; Paciorek 2010).

---

## 4. Phase 4 — Displays and Supplementary (parallel with Phase 3)

- [ ] Rebuild Fig 1 as a single BC-format display (§2); export 400 ppi + vector.
- [ ] Assemble Fig 2 (§2); requires the missing `400ppi/spatial_drivers.png` export.
- [ ] Write two self-contained captions carrying enough detail that the figures read standalone.
- [ ] Build the SI: everything from §2's demotion list, plus Tables 1–2, the full Methods, and the
      Fig 7 composite (Moran + GAM collapse + `s(x,y)`) — now SI, so assemble at lower priority.
- [ ] Confirm `400ppi/design.png` (2026-06-22): `PLAN.md` and `manuscript_nature_cities.md` both still say
      "assembly TODO" but the file exists. Under a BC it is SI regardless.
- [ ] Cut references 41 → ~20; keep Yao et al. 2025 (ERL), the equity/evacuation core, and the two
      spatial-confounding citations.

---

## 5. Phase 5 — Submission package (parallel)

- [ ] **Data availability** — standard Nature proprietary-data form with `[PROVIDER]` markers (D3), plus a
      representativeness sentence (device data under-sample rural/elderly/low-income — the equity-relevant
      groups, so state it in the limitation too).
- [ ] **Code availability** — repo has 80+ uncommitted modified files and four stale worktrees under
      `.claude/worktrees/`. Clean, commit, tag, make public (the author's own note in the stale draft asks
      for exactly this).
- [ ] Convert `literature/references.docx` to Nature numbered style; verify every DOI.
- [ ] Cover letter (lead with the reconnection-gap headline and its policy hook), author contributions,
      competing interests, ethics statement for device-derived data.
- [ ] Verify current *Nature Cities* BC limits and the significance/contribution statement box against the
      live author guidelines — the style report's format table is from 2026-06-25 and should be re-checked.

---

## 6. Phase 6 — Consistency QA (last, before upload)

- [ ] Main text ≤1,500 words; abstract ≤70 words / 3 sentences; title ≤10 words; **exactly ≤2 displays**;
      Methods ≤500 words. Count them, don't estimate.
- [ ] Every number traces to `manuscript_numbers.csv`.
- [ ] No surviving 50-mi, N = 292, N = 271, or 7-category (Utilities) artefact anywhere.
- [ ] Every *n* labelled with its sample basis.
- [ ] The retracted distance-to-track narrative appears nowhere.
- [ ] ¶3 does not imply the reconnection gap is explained by race (see Phase 1 warning).
- [ ] Limitations present, compressed to BC length: n = 2 confounded events; device representativeness;
      observational; spatial confounding; 20k selection.

---

## Critical path

```
Phase 1 (freeze numbers)  →  Phase 2 (pick 2 displays)  →  Phase 3 (write BC)  →  Phase 6 (QA)  →  submit
                                                        ↘  Phase 4 (displays + SI)  ↗
                                                        ↘  Phase 5 (package)        ↗
```

Phase 1 gates everything. Phase 2 gates ¶2–¶3 because the displays determine what the prose can claim.
Phases 4 and 5 run parallel to drafting.
