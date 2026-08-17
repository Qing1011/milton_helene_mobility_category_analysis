# Hurricane recovery gaps lie in reconnection, not local restart

*Nature Cities* Brief Communication — **draft v1**, 2026-08-13
All numbers cite `results/npj_100mi/manuscript_numbers.csv` (Phase 1 frozen set).

---

## Abstract

*(3 sentences, 67 words)*

Climate-intensified hurricanes disrupt urban mobility, yet whether recovery is equitable across the
rural–urban gradient is unclear. Analysing device-based mobility for Hurricanes Helene and Milton, we find
local activity restarted within ~4.5 days in both storms, whereas reconnection to the outside world took
5 days in coastal-urban Florida but 11 in inland-rural Appalachia. The gap lies in external reconnection,
not local restart, implying planners should target rural isolation.

---

## Main text

*(no headings in the submitted version; paragraph markers shown here for review only)*

**¶1.** Tropical cyclones are intensifying under climate change<sup>1</sup>, and their public-health and
economic burdens are rising accordingly<sup>2–4</sup>. Human mobility — the daily movement that sustains
work, care, schooling and commerce — offers a sensitive readout of how urban systems absorb and recover from
these shocks<sup>5</sup>. Most disaster-mobility research has nonetheless concentrated on evacuation: who
leaves before landfall, and how that decision is stratified by income, race and vehicle
access<sup>6–9</sup>. Recovery has received less attention, and where it has been studied it is typically
for a single event in a single metropolitan region<sup>10–12</sup>, leaving unresolved whether communities
differing in urbanicity recover at comparable speed. This matters because the equity-relevant question for
adaptation planning is not only who can leave, but who is left waiting. The 2024 Atlantic season offers an
unusual natural comparison: Hurricanes Helene and Milton struck the southeastern United States 13 days
apart, one inland and rural, the other coastal and urban. Prior work compared their aggregate regional
mobility during the landfall week<sup>13</sup> but did not measure recovery, resolve activity categories, or
examine local spatial structure. Here we decompose mobility into within-area, inflow and outflow components
across six activity categories and two spatial scales, and show that the rural–urban recovery gap lies almost
entirely in external reconnection rather than in local restart.

**¶2.** Milton delivered the deeper shock, and every activity category agrees. Figure 1a,b and 1d,e show
daily deviation from the counterfactual baseline for each of six categories, from one week before landfall to
two weeks after. Within-area mobility fell by 24–45% across categories under Milton against 8–13% under
Helene — between two and four times deeper in every category — and inflow fell by 27–60% against 20–27%. The
two shocks also differ in shape, not only in depth: Milton's within-area decline is a narrow, intense band
(Fig. 1b), whereas Helene's inflow deficit is shallower but far broader (Fig. 1d), persisting well beyond the
landfall week. Recovery does not follow shock depth. Figure 1c and 1f give the time from landfall until each
category returns to baseline. Within-area recovery is indistinguishable between the storms — 3.2–5.1 days
under Helene against 4.7–6.1 days under Milton — and in five of six categories Helene is the *faster* of the
two, despite absorbing the shallower shock. Inflow separates cleanly and in the same direction in all six
categories: 11.3–13.3 days under Helene against 4.4–5.5 days under Milton, a gap of 6.5–8.3 days per
category. The pattern repeats at the local scale, where per-unit within-area recovery is statistically
indistinguishable between storms (median 4.4 days, interquartile range 3.7–5.1, *n* = 96 clusters for Helene;
4.5 days, IQR 4.1–5.4, *n* = 33 counties for Milton; Mann–Whitney *P* = 0.294) while inflow recovery differs
more than twofold (11.1 against 5.1 days; *P* < 0.001; Supplementary Fig. 1). Local activity therefore
restarts on a similar clock regardless of urbanicity or shock depth, while the time a region spends cut off
from outside traffic differs more than twofold. Because within-area flow counts trips beginning and ending
inside the same unit whereas inflow counts arrivals from outside the affected region, this contrast localizes
the rural penalty to external connectivity — the return of commuters, visitors, suppliers and aid — rather
than to the resumption of internal activity.

**¶3.** Figure 2 asks where the reconnection deficit falls and what predicts it. Figure 2a maps the largest
inflow decline per local unit for both storms. Within Helene the deficit is not a simple distance gradient
(Spearman ρ = 0.11 with distance to track, *p* = 0.431, *n* = 52): the deepest declines, between −35% and
−46%, fall in units spanning both the landfall vicinity and the inland interior. Figure 2b shows
posterior distributions from per-storm Bayesian regressions of each flow outcome on nine standardized
predictors spanning hazard, exposure, vulnerability and settlement structure. Under Helene, four effects have
95% highest-density intervals (HDI) excluding zero: coastal location deepens the within-area drop
(β = −4.9, 95% HDI −8.6 to −1.3, *n* = 96), seven-day precipitation (β = −9.0, −14.3 to −3.5) and the
percentage of White residents (β = −7.0, −11.0 to −3.4; both *n* = 52) deepen the inflow drop, and distance
to track dampens the outflow surge (β = −19.9, −29.6 to −9.2, *n* = 74). Under Milton none of 27
predictor-by-outcome combinations reached credibility (*n* = 28–33) — a power limitation at that sample size,
not evidence that drivers are absent. The apparent socioeconomic signal does not survive geographic control.
Figure 2c contrasts coefficients for Helene's inflow model before and after adding a penalized
two-dimensional spatial smooth *s*(*x*,*y*). The smooth is significant (*p* = 0.023) and raises deviance
explained from 0.15 to 0.52; under it the percentage-White association collapses from β = −4.00
(*p* = 0.046) to β = 0.37 (*p* = 0.891), while coastal location strengthens from β = −0.10 (*p* = 0.984) to
β = −13.36 (*p* = 0.040). We therefore report socioeconomic composition as not separably identifiable from
geography for this flow, rather than as having no effect: adding a spatial smooth can null a genuinely
spatially structured effect<sup>14,15</sup>, so this analysis bounds what the data can distinguish rather
than settling the question. Physical exposure — rainfall, coastal position and distance to track — is what
survives the control. Residual spatial autocorrelation is negligible in five of six storm-by-flow models
(Moran's I ≤ 0.07, all *p* > 0.20), indicating that these predictors already absorb the neighbourhood-scale
clustering present in the raw outcomes (I = 0.11–0.35); Milton's inflow model is the exception (I = 0.22,
*p* = 0.039). One boundary deserves emphasis. Within Helene, reconnection speed is not predicted by how rural
a unit is (Spearman ρ = 0.07 with urban–rural code, *p* = 0.637, *n* = 46) but by proximity to the track
(ρ = −0.46, *p* = 0.001). The rural–urban contrast reported here is therefore a difference *between* the two
affected regions, not a gradient within either — an ecological distinction that matters for how the result is
generalized.

**¶4.** These results reframe what post-hurricane resource allocation should target. Peak disruption is a
coastal-urban phenomenon, and it is also the phenomenon that resolves fastest; the protracted burden is the
inland-rural region's extended isolation from outside traffic, which no measure of shock depth would flag.
Because within-area recovery is uniform across both storms, damage-weighted triage that follows the depth of
the initial drop would systematically under-serve precisely the communities that stay disconnected longest.
Restoring external connectivity — principally the road and bridge links carrying inbound traffic — is
therefore the lever with the greatest equity leverage after inland flooding events. Two limitations bound
these conclusions. First, the design compares two events, and inland/coastal, rural/urban and rain/surge
covary across them; we therefore treat Helene and Milton as contrasting archetypes rather than as a causal
contrast between geography types, and separating these axes requires a multi-storm panel. Second,
device-based mobility under-represents rural, elderly and low-income populations<sup>5</sup>, the groups most
relevant to an equity claim — a bias that would, if anything, understate the rural recovery penalty reported
here. Within those bounds the finding is specific and actionable: the rural–urban gap in hurricane mobility
recovery is a gap in reconnection, not in restart.

---

## Methods

*(≤500 words)*

**Study design.** Affected regions comprise counties whose centroid lies within 100 miles of the storm's
IBTrACS best track<sup>16</sup>: 487 counties for Helene (landfall 26 September 2024) and 34 for Milton
(9 October 2024), together 521 counties and 42.9 million residents. The 100-mile cutoff, rather than the
50-mile definition used previously<sup>13</sup>, captures Helene's inland flooding footprint including the
southern Appalachian counties; at 50 miles that region is excluded and exposure gradients invert.

**Mobility data.** Daily origin–destination visit counts derive from device-based foot-traffic records
(Advan Research Weekly Patterns, distributed via Dewey Data<sup>17</sup>) `[VERIFY provider + terms]`.
Point-of-interest categories were aggregated into six activity groups: Travel, Work & Professional, Health,
Education, Retail & Leisure, and Urban Government. For each unit we form three daily flows: within-area
$W(t)$ (origin and destination both inside the unit), inflow $I(t)$ (origin outside the affected region,
destination inside the unit), and outflow $O(t)$ (the reverse).

**Spatial units.** Helene's 487 counties were merged into 101 clusters by joining contiguous counties sharing
a National Center for Health Statistics (NCHS) urban–rural code `[CITATION NEEDED: NCHS scheme]`, because
per-county baselines are unstable for its many small rural units. Milton's 34 counties have stable per-county
baselines and were left unaggregated — an asymmetry driven by baseline stability, not convenience.

**Counterfactual baseline.** For each unit and flow, daily volume $M_t$ was modelled as a calendar regression
with AR(1) errors on the log scale,

$$\log(1+M_t)=c+\sum_{d=1}^{6}\beta_d \mathrm{DOW}_{d,t}+\sum_{m}\gamma_m \mathrm{MON}_{m,t}+\delta\,\mathrm{YEAR2024}_t+\eta_t,\qquad \eta_t=\phi\eta_{t-1}+\varepsilon_t$$

fitted by state-space maximum likelihood on 2023 July–October plus 2024 July through seven days before
landfall, so no storm-affected day enters the fit. Calendar dummies rather than a stochastic seasonal term
were used because mobility seasonality is deterministic, which is more stable for small units. Predictions
back-transform as $\hat M_t=\exp(\cdot)-1$, and disruption is the relative deviation
$rd_t=(M_t-\hat M_t)/\hat M_t$.

**Metrics.** Largest drop is $\min_t rd_t$ over $[t_L, t_L+6]$ (within-area, inflow); outflow surge is
$\max_t rd_t$ over $[t_L-3, t_L+6]$, the window covering evacuation lead time. Recovery time is
$\tau=(t_\text{trough}-t_L)+(-a/b)$, where $a$ and $b$ are the intercept and slope of a Theil–Sen robust
line<sup>18,19</sup> fitted to the monotonic recovery segment of the 3-day-smoothed $rd_t$, and
$t_\text{trough}$ is its minimum within 10 days of landfall. Theil–Sen resists outliers in the noisy
post-trough window; the 10-day window avoids left-censoring the trough of severely disrupted on-track units.

**Sample restriction.** Per flow, units with baseline-window mean volume below 20,000 visits/day were
excluded, removing a noisy low-volume tail (retained, within/inflow/outflow: Helene 96/52/74, Milton
33/28/29).

**Regression.** Per storm and outcome we fitted regularized Bayesian linear models on nine z-scored
predictors — 7-day precipitation `[CITATION NEEDED: PRISM]`, distance to track, coastal indicator, median
income, % White, insurance coverage, % without vehicle, NCHS code, population density — from American
Community Survey (ACS) 2022 5-year estimates<sup>20</sup>. Storms were fitted separately because pooling
imposes common slopes across two events that differ on multiple axes; a pooled specification is reported in
Supplementary Information. Residual spatial autocorrelation was assessed by Moran's I under Queen
contiguity<sup>21</sup>, and spatial confounding by refitting in a generalized additive framework with a
penalized thin-plate smooth $s(x,y)$ `[CITATION NEEDED: Wood, mgcv]`, which tests whether an association
survives adjustment for smooth large-scale geography.

---

## References (target ~20)

1. IPCC. *Climate Change 2022: Impacts, Adaptation and Vulnerability* (2023). doi:10.1017/9781009325844
2. Parks, R. M. & Guinto, R. R. Tropical cyclones and public health. doi:10.1289/EHP12241
3. Parks, R. M. *et al.* Short-term excess mortality after tropical cyclones. *Sci. Adv.* (2023). doi:10.1126/sciadv.adg6633
4. NOAA NCEI. *U.S. Billion-Dollar Weather and Climate Disasters.*
5. Yabe, T. *et al.* Mobile phone location data for disasters. *Comput. Environ. Urban Syst.* (2022). doi:10.1016/j.compenvurbsys.2022.101777
6. Thompson, R. R., Garfin, D. R. & Silver, R. C. Evacuation from natural disasters. *Risk Anal.* (2017). doi:10.1111/risa.12654
7. Deng, H. *et al.* Race and wealth disparities in evacuation. (2021). doi:10.1057/s41599-021-00824-8
8. Huang, S.-K., Lindell, M. K. & Prater, C. S. Hurricane evacuation meta-analysis. (2016). doi:10.1177/0013916515578485
9. Anand, H. *et al.* Income and race disparities in hurricane evacuation are contingent upon study case and design. *Sci. Rep.*
10. Wang, Q. & Taylor, J. E. Hurricane Sandy mobility resilience. *PLoS ONE* (2014). doi:10.1371/journal.pone.0112608
11. Wang, S. *et al.* Hurricane Ian mobility vulnerability and recovery. (2024). doi:10.1080/21681376.2024.2369550
12. Hong, B. *et al.* Inequality in community resilience from mobility data. *Nat. Commun.* (2021). doi:10.1038/s41467-021-22160-w
13. Yao, Q. *et al.* Adaptive mobility responses during Hurricanes Helene and Milton in 2024. *Environ. Res. Lett.* (2025). doi:10.1088/1748-9326/ae0e39
14. `[CITATION NEEDED]` Hodges, J. S. & Reich, B. J. Adding spatially-correlated errors can mess up the fixed effect you love. *Am. Stat.* (2010).
15. `[CITATION NEEDED]` Paciorek, C. J. The importance of scale for spatial-confounding bias. *Stat. Sci.* (2010).
16. NOAA IBTrACS. doi/url per NCEI.
17. Advan Research, Weekly Patterns, via Dewey Data. doi:10.82551/X1PP-1F65 `[VERIFY]`
18. Theil, H. A rank-invariant method of linear and polynomial regression analysis (1950).
19. Sen, P. K. Estimates of the regression coefficient based on Kendall's tau. *JASA* (1968). doi:10.1080/01621459.1968.10480934
20. U.S. Census Bureau. American Community Survey 2022 5-year estimates.
21. Moran, P. A. P. Notes on continuous stochastic phenomena. *Biometrika* (1950). doi:10.1093/biomet/37.1-2.17
22. `[CITATION NEEDED]` Wood, S. N. *mgcv* / thin-plate regression splines.
23. `[CITATION NEEDED]` NCHS Urban–Rural Classification Scheme for Counties.
24. `[CITATION NEEDED]` PRISM Climate Group, daily precipitation.

---

## Figures

**Fig. 1 | The rural–urban gap is in reconnection, not restart.** Regional mobility by activity category.
**a**,**b**, Daily within-area deviation from the counterfactual baseline for Helene (**a**) and Milton
(**b**), six activity categories × 22 days (landfall −7 to +14); red denotes decline, blue increase, on a
scale shared between storms. **c**, Within-area recovery time — days from landfall until each category
returns to baseline — Helene (purple) against Milton (green). **d**,**e**,**f**, The same three panels for
inflow. Recovery axes in **c** and **f** share a 0–15 day scale, so bar length is comparable between flows.
Milton's shock is two to four times deeper (**b** vs **a**), yet only inflow recovery separates the storms
(**f**); within-area recovery does not (**c**). Outflow is a surge rather than a decline and therefore has no
recovery time; it appears in Fig. 2. Storm colours are deliberately purple/green so that red and blue are
reserved for the direction of change.

**Supplementary Fig. 1 | Local recovery has little variance to model.** Per-unit recovery-time distributions
for within-area (**a**) and inflow (**b**) flows, Helene clusters against Milton counties, on a common
0–25 day axis; units restricted to baseline mean volume ≥ 20,000 visits/day. Within-area distributions
overlap (*P* = 0.294) with an interquartile range of about 1.4 days, which is why recovery is reported
descriptively by category rather than used as a regression outcome.

**Fig. 2 | Exposure, not socioeconomic composition, structures the spatial pattern.**
**a**, Largest inflow decline per local unit for both storms. **b**, Posterior means and 95% HDI from
per-storm Bayesian regressions of three flow outcomes on nine standardized predictors; filled markers denote
intervals excluding zero. **c**, Helene inflow coefficients before and after adding a penalized spatial
smooth *s*(*x*,*y*); the percentage-White association collapses to zero while coastal location strengthens.
