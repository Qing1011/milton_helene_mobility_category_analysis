"""Phase 1 — freeze every number the *Nature Cities* Brief Communication will quote.

Builds a single source of truth (`results/npj_100mi/manuscript_numbers.csv`) in which every
quotable value is tagged with **scale** (regional | local), **sample** (all_units | 20k_cut),
and **n**, so that no number can be quoted in the manuscript without its basis attached.

Why this script exists
----------------------
Four different Helene-inflow sample sizes circulate in the package (89 / 72 / 52 / 46). Each is
correct for its own subset, but unlabelled they read as inconsistent. This script recomputes all
of them from canonical sources and records the reconciliation.

It also works around a stale intermediate: `pooled_dataset_100mi_primary_exposure.csv` was written
at 13:36 on 2026-06-22, *before* `_recompute_recovery_10d.py` regenerated the metrics at 16:56 with
the 10-day trough window. Its `recovery_days_*` columns therefore hold superseded 7-day-window
values (Helene inflow: 72 valid, median 11.03 vs the canonical 89 valid, median 11.31). The three
regression DVs in that file are byte-identical to the refreshed build, so 06a/06b are unaffected —
only Table 1's two Recovery rows were built on the stale column. **Recovery here is always read
from the canonical `results/local_level/{storm}_100mi/metrics_{flow}.csv`.**

Sources (all read-only)
-----------------------
- `results/local_level/{helene,milton}_100mi/metrics_{within,inflow,outflow}.csv`  (canonical, 10-d window)
- `results/npj_100mi/sensitivity_20kcut/volume_keep_mask_20k.csv`                  (per-flow 20k gate)
- `results/local_level/regression/pooled_dataset_100mi_primary_exposure.csv`       (covariates only)
- `results/npj_100mi/regional_data/regional_metrics_summary_100mi.csv`             (regional)
- `results/npj_100mi/drivers/bayes_{posterior_summary,r2}_100mi.csv`               (drivers)
- `results/npj_100mi/spatial/{gam_verdict,morans_i}_100mi.csv`                     (spatial)

Outputs
-------
- `results/npj_100mi/manuscript_numbers.csv`
- `results/npj_100mi/MANUSCRIPT_NUMBERS_README.md`

Run with the `extreme` conda env (pandas + scipy).
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("phase1")

ROOT = Path(
    "/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter"
    "/4_hurricane_category"
)
LOCAL = ROOT / "results/local_level"
NPJ = ROOT / "results/npj_100mi"
OUT_CSV = NPJ / "manuscript_numbers.csv"
OUT_MD = NPJ / "MANUSCRIPT_NUMBERS_README.md"

STORMS = ("helene", "milton")
FLOWS = ("within", "inflow", "outflow")
#: Live spec is 6 categories — Utilities is excluded from the npj/Nature Cities package.
UTILITIES = "Utilities"

rows: list[dict] = []


def emit(**kw) -> None:
    """Append one frozen number to the manuscript table."""
    rows.append(kw)


def med_iqr(s: pd.Series, dp: int = 1) -> str:
    """Format a series as ``median [q25, q75]``."""
    s = s.dropna()
    return f"{s.median():.{dp}f} [{s.quantile(.25):.{dp}f}, {s.quantile(.75):.{dp}f}]"


def mwu(a: pd.Series, b: pd.Series) -> float:
    """Two-sided Mann-Whitney U p-value on the non-null overlap."""
    a, b = a.dropna(), b.dropna()
    if len(a) < 3 or len(b) < 3:
        return np.nan
    return stats.mannwhitneyu(a, b, alternative="two-sided")[1]


def pfmt(p: float) -> str:
    """Format a p-value for manuscript use."""
    if np.isnan(p):
        return "n/a"
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def flow_key(dv_label: str) -> str:
    """Map a DV label ('Largest drop (inflow)', 'Outflow surge') to a bare flow key."""
    for flow in FLOWS:
        if flow in dv_label.lower():
            return flow.upper()
    return dv_label.replace(" ", "_").upper()


# --------------------------------------------------------------------------------------
# Load canonical local metrics (10-day trough window) and the per-flow 20k volume gate
# --------------------------------------------------------------------------------------
log.info("loading canonical local metrics + 20k mask")

metrics: dict[tuple[str, str], pd.DataFrame] = {}
for storm in STORMS:
    for flow in FLOWS:
        df = pd.read_csv(LOCAL / f"{storm}_100mi/metrics_{flow}.csv")
        metrics[(storm, flow)] = df

mask = pd.read_csv(NPJ / "sensitivity_20kcut/volume_keep_mask_20k.csv")
mask["storm"] = mask["storm"].str.lower()
keep: dict[tuple[str, str], set] = {
    (s, f): set(g.loc[g["keep"] == 1, "unit_id"])
    for (s, f), g in mask.groupby(["storm", "flow_type"])
}


def subset(storm: str, flow: str, sample: str) -> pd.DataFrame:
    """Return the metrics frame for a storm/flow under ``all_units`` or ``20k_cut``."""
    df = metrics[(storm, flow)]
    if sample == "20k_cut":
        df = df[df["unit_id"].isin(keep[(storm, flow)])]
    return df


# --------------------------------------------------------------------------------------
# A. Local recovery — the headline (D2: external reconnection, not local restart)
# --------------------------------------------------------------------------------------
log.info("A. local recovery")

for sample in ("20k_cut", "all_units"):
    for flow in ("within", "inflow"):
        series = {s: subset(s, flow, sample)["recovery_days"] for s in STORMS}
        p = mwu(series["helene"], series["milton"])
        for storm in STORMS:
            s = series[storm].dropna()
            emit(
                id=f"REC-{flow.upper()}-LOCAL-{storm.upper()}-{sample.upper()}",
                block="P2" if sample == "20k_cut" else "SI",
                quantity=f"Recovery time, {flow}",
                storm=storm,
                scale="local",
                flow=flow,
                sample=sample,
                n=len(s),
                value=med_iqr(s),
                stat="median [IQR] days from landfall",
                extra=f"mean {s.mean():.2f}, sd {s.std():.2f}",
                source_file=f"results/local_level/{storm}_100mi/metrics_{flow}.csv",
                note="canonical 10-day trough window",
            )
        emit(
            id=f"REC-{flow.upper()}-LOCAL-TEST-{sample.upper()}",
            block="P2" if sample == "20k_cut" else "SI",
            quantity=f"Recovery time, {flow} — Helene vs Milton",
            storm="both",
            scale="local",
            flow=flow,
            sample=sample,
            n=f"{series['helene'].notna().sum()} vs {series['milton'].notna().sum()}",
            value=pfmt(p),
            stat="Mann-Whitney U, two-sided",
            extra="",
            source_file="computed here",
            note=(
                "THE NULL THAT CARRIES THE HEADLINE — local restart does not differ"
                if flow == "within"
                else "THE HEADLINE GAP — external reconnection differs ~2x"
            ),
        )

# --------------------------------------------------------------------------------------
# B. Local shock depth
# --------------------------------------------------------------------------------------
log.info("B. local shock depth")

DV = {"within": "largest_drop", "inflow": "largest_drop", "outflow": "largest_increase"}
for sample in ("20k_cut", "all_units"):
    for flow in FLOWS:
        col = DV[flow]
        series = {s: subset(s, flow, sample)[col] for s in STORMS}
        p = mwu(series["helene"], series["milton"])
        label = "Outflow surge" if flow == "outflow" else f"Largest drop, {flow}"
        for storm in STORMS:
            s = series[storm].dropna()
            emit(
                id=f"DV-{flow.upper()}-LOCAL-{storm.upper()}-{sample.upper()}",
                block="P2" if sample == "20k_cut" else "SI",
                quantity=label,
                storm=storm,
                scale="local",
                flow=flow,
                sample=sample,
                n=len(s),
                value=med_iqr(s, dp=0) + "%",
                stat="median [IQR] % deviation from baseline",
                extra=f"mean {s.mean():.1f}, sd {s.std():.1f}",
                source_file=f"results/local_level/{storm}_100mi/metrics_{flow}.csv",
                note="",
            )
        emit(
            id=f"DV-{flow.upper()}-LOCAL-TEST-{sample.upper()}",
            block="P2" if sample == "20k_cut" else "SI",
            quantity=f"{label} — Helene vs Milton",
            storm="both",
            scale="local",
            flow=flow,
            sample=sample,
            n=f"{series['helene'].notna().sum()} vs {series['milton'].notna().sum()}",
            value=pfmt(p),
            stat="Mann-Whitney U, two-sided",
            extra="",
            source_file="computed here",
            note="",
        )

# --------------------------------------------------------------------------------------
# C. Regional (6 categories, Utilities excluded) — the "holds across categories" clause
# --------------------------------------------------------------------------------------
log.info("C. regional, 6 categories")

reg = pd.read_csv(NPJ / "regional_data/regional_metrics_summary_100mi.csv")
reg6 = reg[reg["category"] != UTILITIES].copy()
assert reg6["category"].nunique() == 6, "expected 6 categories after dropping Utilities"

for storm in STORMS:
    for flow in ("within", "inflow"):
        g = reg6[(reg6.hurricane == storm) & (reg6.flow_type == flow)]
        d = g["largest_drop"]
        emit(
            id=f"DV-{flow.upper()}-REGIONAL-{storm.upper()}",
            block="P2",
            quantity=f"Largest drop, {flow}",
            storm=storm,
            scale="regional",
            flow=flow,
            sample="6 categories",
            n=len(g),
            value=f"{abs(d.max()):.0f}–{abs(d.min()):.0f}%",
            stat="range across 6 categories (% below baseline)",
            extra=f"median {abs(d.median()):.1f}%",
            source_file="results/npj_100mi/regional_data/regional_metrics_summary_100mi.csv",
            note="Utilities excluded per live 6-category scope",
        )
        r = g["recovery_days"]
        emit(
            id=f"REC-{flow.upper()}-REGIONAL-{storm.upper()}",
            block="P2",
            quantity=f"Recovery time, {flow}",
            storm=storm,
            scale="regional",
            flow=flow,
            sample="6 categories",
            n=int(r.notna().sum()),
            value=f"{r.min():.1f}–{r.max():.1f} d",
            stat="range across 6 categories (days from landfall)",
            extra=f"median {r.median():.1f} d",
            source_file="results/npj_100mi/regional_data/regional_metrics_summary_100mi.csv",
            note=(
                "NB Helene recovers FASTER than Milton on within — do not imply otherwise"
                if flow == "within"
                else ""
            ),
        )

# --------------------------------------------------------------------------------------
# D. Bayesian drivers — credible effects only, plus the explicit Milton null
# --------------------------------------------------------------------------------------
log.info("D. Bayesian drivers")

bayes = pd.read_csv(NPJ / "drivers/bayes_posterior_summary_100mi.csv")
r2 = pd.read_csv(NPJ / "drivers/bayes_r2_100mi.csv")
sig = bayes[bayes["significant"] == 1]

for _, r in sig.iterrows():
    n = int(r2[(r2.hurricane == r.hurricane) & (r2.dv == r.dv)]["n"].iloc[0])
    emit(
        id=f"BAYES-{r.hurricane.upper()}-{r.predictor.upper()}",
        block="P3",
        quantity=f"{r.predictor} → {r.dv}",
        storm=r.hurricane,
        scale="local",
        flow=r.dv,
        sample="20k_cut",
        n=n,
        value=f"{r['mean']:.1f} [{r.hdi_2_5:.1f}, {r.hdi_97_5:.1f}]",
        stat="posterior mean [95% HDI], z-scored predictor",
        extra=f"sd {r.sd:.2f}",
        source_file="results/npj_100mi/drivers/bayes_posterior_summary_100mi.csv",
        note="95% HDI excludes zero",
    )

n_milton_sig = int((sig.hurricane == "milton").sum())
emit(
    id="BAYES-MILTON-NULL",
    block="P3",
    quantity="Credible drivers, Milton",
    storm="milton",
    scale="local",
    flow="all 3 DVs",
    sample="20k_cut",
    n="33 / 28 / 29",
    value=f"none ({n_milton_sig} of 27 predictor×DV effects)",
    stat="95% HDI excludes zero",
    extra="",
    source_file="results/npj_100mi/drivers/bayes_posterior_summary_100mi.csv",
    note="STATE EXPLICITLY — underpowered, not evidence of absence",
)

for _, r in r2.iterrows():
    emit(
        id=f"R2-{r.hurricane.upper()}-{flow_key(r.dv)}",
        block="SI",
        quantity=f"Bayesian R² — {r.dv}",
        storm=r.hurricane,
        scale="local",
        flow=r.dv,
        sample="20k_cut",
        n=int(r["n"]),
        value=f"{r.r2_median:.2f} [{r.r2_cri_lo:.2f}, {r.r2_cri_hi:.2f}]",
        stat="posterior median R² [95% CrI]",
        extra="",
        source_file="results/npj_100mi/drivers/bayes_r2_100mi.csv",
        note="",
    )

# --------------------------------------------------------------------------------------
# E. Spatial GAM verdict
# --------------------------------------------------------------------------------------
log.info("E. GAM verdict")

gam = pd.read_csv(NPJ / "spatial/gam_verdict_100mi.csv")
for _, r in gam.iterrows():
    emit(
        id=f"GAM-{r.DV.upper()}",
        block="P3",
        quantity=f"Spatial smooth s(x,y) — Helene {r.DV}",
        storm="helene",
        scale="local",
        flow=r.DV,
        sample="20k_cut",
        n=int(r["n"]),
        value=f"p = {r.s_xy_p:.3f}; dev. expl. {r.devexpl_M0:.2f} → {r.devexpl_M1:.2f}",
        stat="mgcv penalized smooth test",
        extra=f"income_varies p = {r.income_varies_p:.3f}, insurance_varies p = {r.insurance_varies_p:.3f}",
        source_file="results/npj_100mi/spatial/gam_verdict_100mi.csv",
        note=(
            "ONLY flow with significant smooth geography — the flow carrying the headline. "
            "SES here is not separably identifiable from geography."
            if r.DV == "inflow"
            else "no smooth spatial structure"
        ),
    )

# --------------------------------------------------------------------------------------
# F. Moran's I — raw DV vs OLS residual (the "geography absorbs it" result)
# --------------------------------------------------------------------------------------
log.info("F. Moran's I")

mor = pd.read_csv(NPJ / "spatial/morans_i_100mi.csv")
for _, r in mor[mor.weight == "Queen"].iterrows():
    emit(
        id=f"MORAN-{r.storm.upper()}-{flow_key(r.dv)}-{r.target.upper()}",
        block="P3" if r.target == "raw" else "SI",
        quantity=f"Moran's I ({r.target}) — {r.dv}",
        storm=r.storm,
        scale="local",
        flow=r.dv,
        sample="20k_cut",
        n=int(r["n"]),
        value=f"I = {r.moran_I:.3f}, p = {r.p_sim:.3f}",
        stat="Moran's I, Queen contiguity, 999 permutations",
        extra="",
        source_file="results/npj_100mi/spatial/morans_i_100mi.csv",
        note="KNN4 variant in source file",
    )

# --------------------------------------------------------------------------------------
# G. Sample-size reconciliation — the four Helene-inflow n's
# --------------------------------------------------------------------------------------
log.info("G. sample-size reconciliation")

h_inflow_all = metrics[("helene", "inflow")]
h_inflow_cut = subset("helene", "inflow", "20k_cut")
recon = [
    (
        "N-HELENE-INFLOW-ALL-UNITS",
        "All Helene clusters",
        len(h_inflow_all),
        "every clustered unit, before any volume gate",
    ),
    (
        "N-HELENE-INFLOW-ALL-RECOVERY",
        "All clusters with a valid inflow recovery",
        int(h_inflow_all["recovery_days"].notna().sum()),
        "10-day trough window; NaNs are genuine inflow surges with no drop to recover from",
    ),
    (
        "N-HELENE-INFLOW-20K",
        "20k-cut inflow regression sample",
        len(h_inflow_cut),
        "baseline-window mean inflow >= 20,000 visits/day; this is the 06a/06b n",
    ),
    (
        "N-HELENE-INFLOW-20K-RECOVERY",
        "20k-cut units with a valid inflow recovery",
        int(h_inflow_cut["recovery_days"].notna().sum()),
        "the Figure 1 histogram n",
    ),
]
for rid, label, n, why in recon:
    emit(
        id=rid,
        block="METHODS",
        quantity=label,
        storm="helene",
        scale="local",
        flow="inflow",
        sample="varies",
        n=n,
        value=str(n),
        stat="count",
        extra="",
        source_file="results/local_level/helene_100mi/metrics_inflow.csv",
        note=why,
    )

emit(
    id="N-STALE-TABLE1-WARNING",
    block="METHODS",
    quantity="Superseded Helene inflow recovery n in Table 1",
    storm="helene",
    scale="local",
    flow="inflow",
    sample="all_units",
    n=72,
    value="72 (SUPERSEDED)",
    stat="count",
    extra="",
    source_file="results/npj_100mi/drivers/table1_hev_descriptives.csv",
    note=(
        "Table 1 was built from pooled_dataset_100mi_primary_exposure.csv (13:36), written before "
        "_recompute_recovery_10d.py refreshed the metrics (16:56). Its recovery columns hold "
        "7-day-window values. Regenerate Table 1 against the canonical metrics before submission. "
        "Regression DVs in that file are byte-identical to the refreshed build, so 06a/06b stand."
    ),
)

# --------------------------------------------------------------------------------------
# Write
# --------------------------------------------------------------------------------------
COLS = [
    "id", "block", "quantity", "storm", "scale", "flow", "sample",
    "n", "value", "stat", "extra", "source_file", "note",
]
out = pd.DataFrame(rows)[COLS]
out.to_csv(OUT_CSV, index=False)
log.info("wrote %s (%d frozen numbers)", OUT_CSV.relative_to(ROOT), len(out))

for blk in ("P2", "P3", "P4", "METHODS", "SI"):
    log.info("  block %-8s %3d", blk, int((out.block == blk).sum()))
