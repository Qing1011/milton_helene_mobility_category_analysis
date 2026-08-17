/**
 * Build the Nature Cities Brief Communication as a submission-format .docx.
 *
 * Source of truth is npj/manuscript_BC_draft_v1.md; this script encodes the same text with
 * submission formatting (12 pt, double-spaced, continuous line numbers, superscript citations).
 * Every number in it traces to results/npj_100mi/manuscript_numbers.csv.
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  LineNumberRestartFormat, convertInchesToTwip,
} = require("docx");

const FONT = "Times New Roman";
const SZ = 24;        // half-points => 12 pt
const LINE = 480;     // 240 = single; 480 = double

/** Body paragraph with optional overrides. */
const P = (children, opts = {}) =>
  new Paragraph({
    spacing: { line: opts.line || LINE, after: opts.after ?? 0 },
    alignment: opts.align,
    indent: opts.indent,
    keepNext: opts.keepNext,
    children,
  });

/** Plain run. */
const T = (text, opts = {}) =>
  new TextRun({ text, font: FONT, size: opts.size || SZ, bold: opts.bold, italics: opts.italics,
                superScript: opts.sup, color: opts.color });

/**
 * Convert a light markup string into runs.
 *   *italic*      -> italic
 *   **bold**      -> bold
 *   ^{1,2}        -> superscript (citations)
 */
function rich(s, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|\^\{[^}]+\})/g;
  let last = 0, m;
  while ((m = re.exec(s)) !== null) {
    if (m.index > last) out.push(T(s.slice(last, m.index), base));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(T(tok.slice(2, -2), { ...base, bold: true }));
    else if (tok.startsWith("^{")) out.push(T(tok.slice(2, -1), { ...base, sup: true }));
    else out.push(T(tok.slice(1, -1), { ...base, italics: true }));
    last = m.index + tok.length;
  }
  if (last < s.length) out.push(T(s.slice(last), base));
  return out;
}

const H = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 160, line: LINE },
    keepNext: true,
    children: [T(text, { bold: true })],
  });

// ── content ────────────────────────────────────────────────────────────────────────────
const TITLE = "Hurricane recovery gaps lie in reconnection, not local restart";

const ABSTRACT =
  "Climate-intensified hurricanes disrupt urban mobility, yet whether recovery is equitable across " +
  "the rural–urban gradient is unclear. Analysing device-based mobility for Hurricanes Helene and " +
  "Milton, we find local activity restarted within ~4.5 days in both storms, whereas reconnection to " +
  "the outside world took 5 days in coastal-urban Florida but 11 in inland-rural Appalachia. The gap " +
  "lies in external reconnection, not local restart, implying planners should target rural isolation.";

const BODY = [
  "Tropical cyclones are intensifying under climate change^{1}, and their public-health and economic " +
  "burdens are rising accordingly^{2–4}. Human mobility — the daily movement that sustains work, care, " +
  "schooling and commerce — offers a sensitive readout of how urban systems absorb and recover from " +
  "these shocks^{5}. Most disaster-mobility research has nonetheless concentrated on evacuation: who " +
  "leaves before landfall, and how that decision is stratified by income, race and vehicle " +
  "access^{6–9}. Recovery has received less attention, and where it has been studied it is typically " +
  "for a single event in a single metropolitan region^{10–12}, leaving unresolved whether communities " +
  "differing in urbanicity recover at comparable speed. This matters because the equity-relevant " +
  "question for adaptation planning is not only who can leave, but who is left waiting. The 2024 " +
  "Atlantic season offers an unusual natural comparison: Hurricanes Helene and Milton struck the " +
  "southeastern United States 13 days apart, one inland and rural, the other coastal and urban. Prior " +
  "work compared their aggregate regional mobility during the landfall week^{13} but did not measure " +
  "recovery, resolve activity categories, or examine local spatial structure. Here we decompose " +
  "mobility into within-area, inflow and outflow components across six activity categories and two " +
  "spatial scales, and show that the rural–urban recovery gap lies almost entirely in external " +
  "reconnection rather than in local restart.",

  "Milton delivered the deeper shock, and every activity category agrees. Figure 1a,b and 1d,e show " +
  "daily deviation from the counterfactual baseline for each of six categories, from one week before " +
  "landfall to two weeks after. Within-area mobility fell by 24–45% across categories under Milton " +
  "against 8–13% under Helene — between two and four times deeper in every category — and inflow fell " +
  "by 27–60% against 20–27%. The two shocks also differ in shape, not only in depth: Milton's " +
  "within-area decline is a narrow, intense band (Fig. 1b), whereas Helene's inflow deficit is " +
  "shallower but far broader (Fig. 1d), persisting well beyond the landfall week. Recovery does not " +
  "follow shock depth. Figure 1c and 1f give the time from landfall until each category returns to " +
  "baseline. Within-area recovery is indistinguishable between the storms — 3.2–5.1 days under Helene " +
  "against 4.7–6.1 days under Milton — and in five of six categories Helene is the *faster* of the " +
  "two, despite absorbing the shallower shock. Inflow separates cleanly and in the same direction in " +
  "all six categories: 11.3–13.3 days under Helene against 4.4–5.5 days under Milton, a gap of 6.5–8.3 " +
  "days per category. The pattern repeats at the local scale, where per-unit within-area recovery is " +
  "statistically indistinguishable between storms (median 4.4 days, interquartile range 3.7–5.1, " +
  "*n* = 96 clusters for Helene; 4.5 days, IQR 4.1–5.4, *n* = 33 counties for Milton; Mann–Whitney " +
  "*P* = 0.294) while inflow recovery differs more than twofold (11.1 against 5.1 days; *P* < 0.001; " +
  "Supplementary Fig. 1). Local activity therefore restarts on a similar clock regardless of urbanicity " +
  "or shock depth, while the time a region spends cut off from outside traffic differs more than " +
  "twofold. Because within-area flow counts trips beginning and ending inside the same unit whereas " +
  "inflow counts arrivals from outside the affected region, this contrast localizes the rural penalty " +
  "to external connectivity — the return of commuters, visitors, suppliers and aid — rather than to " +
  "the resumption of internal activity.",

  "Figure 2 asks where the reconnection deficit falls and what predicts it. Figure 2a maps the largest " +
  "inflow decline per local unit for both storms. Within Helene the deficit is not a simple distance " +
  "gradient (Spearman ρ = 0.11 with distance to track, *P* = 0.431, *n* = 52): the deepest declines, " +
  "between −35% and −46%, fall in units spanning both the landfall vicinity and the inland interior. " +
  "Figure 2b shows posterior distributions from per-storm Bayesian regressions of each flow outcome on " +
  "nine standardized predictors spanning hazard, exposure, vulnerability and settlement structure. " +
  "Under Helene, four effects have 95% highest-density intervals (HDI) excluding zero: coastal location " +
  "deepens the within-area drop (β = −4.9, 95% HDI −8.6 to −1.3, *n* = 96), seven-day precipitation " +
  "(β = −9.0, −14.3 to −3.5) and the percentage of White residents (β = −7.0, −11.0 to −3.4; both " +
  "*n* = 52) deepen the inflow drop, and distance to track dampens the outflow surge (β = −19.9, " +
  "−29.6 to −9.2, *n* = 74). Under Milton none of 27 predictor-by-outcome combinations reached " +
  "credibility (*n* = 28–33) — a power limitation at that sample size, not evidence that drivers are " +
  "absent; the storms are also indistinguishable in outflow surge itself (*P* = 0.991). The apparent " +
  "socioeconomic signal does not survive geographic control. Figure 2c contrasts coefficients for " +
  "Helene's inflow model before and after adding a penalized two-dimensional spatial smooth " +
  "*s*(*x*,*y*). The smooth is significant (*P* = 0.023) and raises deviance explained from 0.15 to " +
  "0.52; under it the percentage-White association collapses from β = −4.00 (*P* = 0.046) to β = 0.37 " +
  "(*P* = 0.891), while coastal location strengthens from β = −0.10 (*P* = 0.984) to β = −13.36 " +
  "(*P* = 0.040). We therefore report socioeconomic composition as not separably identifiable from " +
  "geography for this flow, rather than as having no effect: adding a spatial smooth can null a " +
  "genuinely spatially structured effect^{14,15}, so this analysis bounds what the data can distinguish " +
  "rather than settling the question. Physical exposure — rainfall, coastal position and distance to " +
  "track — is what survives the control. Residual spatial autocorrelation is negligible in five of six " +
  "storm-by-flow models (Moran's I ≤ 0.07, all *P* > 0.20), indicating that these predictors already " +
  "absorb the neighbourhood-scale clustering present in the raw outcomes (I = 0.11–0.35); Milton's " +
  "inflow model is the exception (I = 0.22, *P* = 0.039). One boundary deserves emphasis. Within " +
  "Helene, reconnection speed is not predicted by how rural a unit is (Spearman ρ = 0.07 with " +
  "urban–rural code, *P* = 0.637, *n* = 46) but by proximity to the track (ρ = −0.46, *P* = 0.001). The " +
  "rural–urban contrast reported here is therefore a difference *between* the two affected regions, not " +
  "a gradient within either — an ecological distinction that matters for how the result is generalized.",

  "These results reframe what post-hurricane resource allocation should target. Peak disruption is a " +
  "coastal-urban phenomenon, and it is also the phenomenon that resolves fastest; the protracted burden " +
  "is the inland-rural region's extended isolation from outside traffic, which no measure of shock " +
  "depth would flag. Because within-area recovery is uniform across both storms, damage-weighted triage " +
  "that follows the depth of the initial drop would systematically under-serve precisely the " +
  "communities that stay disconnected longest. Restoring external connectivity — principally the road " +
  "and bridge links carrying inbound traffic — is therefore the lever with the greatest equity leverage " +
  "after inland flooding events. Two limitations bound these conclusions. First, the design compares " +
  "two events, and inland/coastal, rural/urban and rain/surge covary across them; we therefore treat " +
  "Helene and Milton as contrasting archetypes rather than as a causal contrast between geography " +
  "types, and separating these axes requires a multi-storm panel. Second, device-based mobility " +
  "under-represents rural, elderly and low-income populations^{5}, the groups most relevant to an " +
  "equity claim — a bias that would, if anything, understate the rural recovery penalty reported here. " +
  "Within those bounds the finding is specific and actionable: the rural–urban gap in hurricane " +
  "mobility recovery is a gap in reconnection, not in restart.",
];

const METHODS = [
  ["Study design.",
   "Affected regions comprise counties whose centroid lies within 100 miles of the storm's IBTrACS best " +
   "track^{16}: 487 counties for Helene (landfall 26 September 2024) and 34 for Milton (9 October 2024), " +
   "together 521 counties and 42.9 million residents. The 100-mile cutoff, rather than the 50-mile " +
   "definition used previously^{13}, captures Helene's inland flooding footprint including the southern " +
   "Appalachian counties; at 50 miles that region is excluded and exposure gradients invert."],
  ["Mobility data.",
   "Daily origin–destination visit counts derive from device-based foot-traffic records (Advan Research " +
   "Weekly Patterns, distributed via Dewey Data^{17}) [VERIFY provider + terms]. Point-of-interest " +
   "categories were aggregated into six activity groups: Travel, Work & Professional, Health, Education, " +
   "Retail & Leisure, and Urban Government. For each unit we form three daily flows: within-area W(t) " +
   "(origin and destination both inside the unit), inflow I(t) (origin outside the affected region, " +
   "destination inside the unit), and outflow O(t) (the reverse)."],
  ["Spatial units.",
   "Helene's 487 counties were merged into 101 clusters by joining contiguous counties sharing a " +
   "National Center for Health Statistics (NCHS) urban–rural code [CITATION NEEDED], because per-county " +
   "baselines are unstable for its many small rural units. Milton's 34 counties have stable per-county " +
   "baselines and were left unaggregated — an asymmetry driven by baseline stability, not convenience."],
  ["Counterfactual baseline.",
   "For each unit and flow, daily volume M(t) was modelled as a calendar regression with AR(1) errors on " +
   "the log scale: log(1 + M(t)) = c + Σ β(d)·DOW + Σ γ(m)·MON + δ·YEAR2024 + η(t), with " +
   "η(t) = φ·η(t−1) + ε(t). It was fitted by state-space maximum likelihood on 2023 July–October plus " +
   "2024 July through seven days before landfall, so no storm-affected day enters the fit. Calendar " +
   "dummies rather than a stochastic seasonal term were used because mobility seasonality is " +
   "deterministic, which is more stable for small units. Predictions back-transform as " +
   "M̂(t) = exp(·) − 1, and disruption is the relative deviation rd(t) = (M(t) − M̂(t)) / M̂(t)."],
  ["Metrics.",
   "Largest drop is the minimum of rd(t) over [t(L), t(L)+6] (within-area, inflow); outflow surge is the " +
   "maximum over [t(L)−3, t(L)+6], the window covering evacuation lead time. Recovery time is " +
   "τ = (t(trough) − t(L)) + (−a/b), where a and b are the intercept and slope of a Theil–Sen robust " +
   "line^{18,19} fitted to the monotonic recovery segment of the 3-day-smoothed rd(t), and t(trough) is " +
   "its minimum within 10 days of landfall. Theil–Sen resists outliers in the noisy post-trough window; " +
   "the 10-day window avoids left-censoring the trough of severely disrupted on-track units."],
  ["Sample restriction.",
   "Per flow, units with baseline-window mean volume below 20,000 visits/day were excluded, removing a " +
   "noisy low-volume tail (retained, within/inflow/outflow: Helene 96/52/74, Milton 33/28/29)."],
  ["Regression.",
   "Per storm and outcome we fitted regularized Bayesian linear models on nine z-scored predictors — " +
   "7-day precipitation [CITATION NEEDED: PRISM], distance to track, coastal indicator, median income, " +
   "% White, insurance coverage, % without vehicle, NCHS code, population density — from American " +
   "Community Survey (ACS) 2022 5-year estimates^{20}. Storms were fitted separately because pooling " +
   "imposes common slopes across two events that differ on multiple axes; a pooled specification is " +
   "reported in Supplementary Information. Residual spatial autocorrelation was assessed by Moran's I " +
   "under Queen contiguity^{21}, and spatial confounding by refitting in a generalized additive " +
   "framework with a penalized thin-plate smooth s(x,y) [CITATION NEEDED: Wood, mgcv], which tests " +
   "whether an association survives adjustment for smooth large-scale geography."],
];

const CAPTIONS = [
  ["Fig. 1 | The rural–urban gap is in reconnection, not restart.",
   "Regional mobility by activity category. **a**,**b**, Daily within-area deviation from the " +
   "counterfactual baseline for Helene (**a**) and Milton (**b**), six activity categories × 22 days " +
   "(landfall −7 to +14); red denotes decline, blue increase, on a scale shared between storms. " +
   "**c**, Within-area recovery time — days from landfall until each category returns to baseline — " +
   "Helene (purple) against Milton (green). **d**,**e**,**f**, The same three panels for inflow. " +
   "Recovery axes in **c** and **f** share a 0–15 day scale, so bar length is comparable between flows. " +
   "Milton's shock is two to four times deeper (**b** vs **a**), yet only inflow recovery separates the " +
   "storms (**f**); within-area recovery does not (**c**). Outflow is a surge rather than a decline and " +
   "therefore has no recovery time; it appears in Fig. 2. Storm colours are deliberately purple/green " +
   "so that red and blue are reserved for the direction of change."],
  ["Fig. 2 | Exposure, not socioeconomic composition, structures the spatial pattern.",
   "**a**, Largest inflow decline per local unit for both storms. **b**, Posterior means and 95% highest-" +
   "density intervals from per-storm Bayesian regressions of three flow outcomes on nine standardized " +
   "predictors; filled markers denote intervals excluding zero. **c**, Helene inflow coefficients before " +
   "and after adding a penalized spatial smooth s(x,y); the percentage-White association collapses to " +
   "zero while coastal location strengthens."],
  ["Supplementary Fig. 1 | Local recovery has little variance to model.",
   "Per-unit recovery-time distributions for within-area (**a**) and inflow (**b**) flows, Helene " +
   "clusters against Milton counties, on a common 0–25 day axis; units restricted to baseline mean " +
   "volume ≥ 20,000 visits/day. Within-area distributions overlap (*P* = 0.294) with an interquartile " +
   "range of about 1.4 days, which is why recovery is reported descriptively by category rather than " +
   "used as a regression outcome."],
];

const REFS = [
  "IPCC. Climate Change 2022: Impacts, Adaptation and Vulnerability (2023). doi:10.1017/9781009325844",
  "Parks, R. M. & Guinto, R. R. Tropical cyclones and public health. doi:10.1289/EHP12241",
  "Parks, R. M. et al. Short-term excess mortality after tropical cyclones. Sci. Adv. (2023). doi:10.1126/sciadv.adg6633",
  "NOAA NCEI. U.S. Billion-Dollar Weather and Climate Disasters.",
  "Yabe, T. et al. Mobile phone location data for disasters. Comput. Environ. Urban Syst. (2022). doi:10.1016/j.compenvurbsys.2022.101777",
  "Thompson, R. R., Garfin, D. R. & Silver, R. C. Evacuation from natural disasters. Risk Anal. (2017). doi:10.1111/risa.12654",
  "Deng, H. et al. Race and wealth disparities in evacuation (2021). doi:10.1057/s41599-021-00824-8",
  "Huang, S.-K., Lindell, M. K. & Prater, C. S. Hurricane evacuation meta-analysis (2016). doi:10.1177/0013916515578485",
  "Anand, H. et al. Income and race disparities in hurricane evacuation are contingent upon study case and design. Sci. Rep.",
  "Wang, Q. & Taylor, J. E. Hurricane Sandy mobility resilience. PLoS ONE (2014). doi:10.1371/journal.pone.0112608",
  "Wang, S. et al. Hurricane Ian mobility vulnerability and recovery (2024). doi:10.1080/21681376.2024.2369550",
  "Hong, B. et al. Inequality in community resilience from mobility data. Nat. Commun. (2021). doi:10.1038/s41467-021-22160-w",
  "Yao, Q. et al. Adaptive mobility responses during Hurricanes Helene and Milton in 2024. Environ. Res. Lett. (2025). doi:10.1088/1748-9326/ae0e39",
  "[CITATION NEEDED] Hodges, J. S. & Reich, B. J. Adding spatially-correlated errors can mess up the fixed effect you love. Am. Stat. (2010).",
  "[CITATION NEEDED] Paciorek, C. J. The importance of scale for spatial-confounding bias. Stat. Sci. (2010).",
  "NOAA IBTrACS. International Best Track Archive for Climate Stewardship.",
  "Advan Research, Weekly Patterns, via Dewey Data. doi:10.82551/X1PP-1F65 [VERIFY]",
  "Theil, H. A rank-invariant method of linear and polynomial regression analysis (1950).",
  "Sen, P. K. Estimates of the regression coefficient based on Kendall's tau. JASA (1968). doi:10.1080/01621459.1968.10480934",
  "U.S. Census Bureau. American Community Survey 2022 5-year estimates.",
  "Moran, P. A. P. Notes on continuous stochastic phenomena. Biometrika (1950). doi:10.1093/biomet/37.1-2.17",
];

// ── assemble ───────────────────────────────────────────────────────────────────────────
const children = [];

children.push(P([T(TITLE, { bold: true, size: 32 })], { after: 200, line: 300 }));
children.push(P([T("Authors and affiliations [TO ADD]", { italics: true, color: "808080" })],
                { after: 320, line: 300 }));

children.push(H("Abstract"));
children.push(P(rich(ABSTRACT), { after: 200 }));

children.push(H("Main text"));
BODY.forEach((para) => children.push(P(rich(para), { after: 160 })));

children.push(H("Methods"));
METHODS.forEach(([lead, text]) =>
  children.push(P([T(lead + " ", { bold: true }), ...rich(text)], { after: 140 })));

children.push(H("Figure captions"));
CAPTIONS.forEach(([lead, text]) =>
  children.push(P([T(lead + " ", { bold: true }), ...rich(text)], { after: 140 })));

children.push(H("References"));
REFS.forEach((r, i) =>
  children.push(P([T(`${i + 1}. `), ...rich(r)],
                  { after: 60, line: 300, indent: { left: convertInchesToTwip(0.3), hanging: convertInchesToTwip(0.3) } })));

const doc = new Document({
  creator: "Qing Yao",
  title: TITLE,
  description: "Nature Cities Brief Communication — draft v1",
  styles: {
    default: {
      heading1: { run: { font: FONT, size: 26, bold: true, color: "000000" } },
    },
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } },
      lineNumbers: { countBy: 1, restart: LineNumberRestartFormat.CONTINUOUS },
    },
    children,
  }],
});

const out = process.argv[2];
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log("wrote", out, (buf.length / 1024).toFixed(1) + " KB");
});
