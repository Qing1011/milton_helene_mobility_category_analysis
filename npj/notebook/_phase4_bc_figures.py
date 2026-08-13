"""Phase 4 — build the *Nature Cities* Brief Communication display items.

Plot-only: reads stored artifacts, runs no analysis (per `npj/notebook/PLAN.md`,
"compute once, plot many"). Every plotted quantity matches a frozen `id` in
`results/npj_100mi/manuscript_numbers.csv`.

What this builds
----------------
**Figure 1** (`figureBC1_recovery_contrast`) — the headline. Two panels on a **common x-axis**
so the reader can compare them directly: (a) within-area recovery, where the two storms overlap
(medians 4.4 vs 4.5 d, p = 0.294); (b) inflow recovery, where they separate (11.1 vs 5.1 d,
p < 0.001). This is a rebuild rather than a re-use of `figure4_recovery_{within,inflow}`, for two
reasons: those are separate files on **different axes** (within 0-18, inflow 0-26), which defeats
the visual comparison the argument rests on; and they annotate **mean/sd** while the manuscript
quotes **median [IQR]**, so figure and text would disagree. Histograms are normalized to *fraction
of units* because n differs almost threefold between storms (96 vs 33), and raw counts would make
Milton visually negligible.

**Figure 2c** (`figureBC2c_gam_collapse`) — the spatial-confounding panel, drawn as a
before/after dumbbell rather than a coefficient forest: each predictor's Helene-inflow effect
without and with a penalized spatial smooth s(x,y). Reads more directly than a two-model forest
for the one question it must answer — which effects survive adjustment for geography.

Not built here
--------------
- **Fig 2a** (inflow choropleth) needs `geopandas` + county geometry, neither available in this
  environment. Source it from the existing `results/npj_100mi/figure5_flow_maps.pdf` (inflow column).
- **Fig 2b** (Bayesian forest) is already built as `drivers/figure6a_hev_per_storm.pdf` and is
  fit for purpose; not duplicated.

Output
------
`results/npj_100mi/bc_figures/` — PDF (vector, submission) + PNG at 450 dpi.
EPS is emitted only for Fig 2c; Fig 1's overlaid alpha-blended histograms do not survive EPS
flattening cleanly, so PDF is the vector format there.

Run with the `extreme` conda env.
"""

import logging
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("phase4")

ROOT = Path(
    "/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter"
    "/4_hurricane_category"
)
LOCAL = ROOT / "results/local_level"
NPJ = ROOT / "results/npj_100mi"
OUT = NPJ / "bc_figures"
OUT.mkdir(parents=True, exist_ok=True)

#: Package style (matches `04_local_recovery_time distribution.ipynb`), with dpi raised to 450.
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5,
    "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 450, "savefig.bbox": "tight",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

HURR_COLOR = {"helene": "#1f77b4", "milton": "#d62728"}
HURR_DIR = {"helene": "helene_100mi", "milton": "milton_100mi"}
VOL_FLOOR = 20_000.0  #: per-flow baseline-volume gate (visits/day)


def save(fig, stem: str, eps: bool = False) -> None:
    """Write a figure to PDF + PNG (+ EPS when alpha-blending permits)."""
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=450, bbox_inches="tight")
    if eps:
        fig.savefig(OUT / f"{stem}.eps", bbox_inches="tight")
    plt.close(fig)
    log.info("saved %s", stem)


def load_recovery() -> pd.DataFrame:
    """Per-unit recovery days on the 20k-cut sample, from canonical metrics (10-d window)."""
    recs = []
    for storm, d in HURR_DIR.items():
        bs = pd.read_csv(LOCAL / d / "baseline_summary.csv")
        bs["unit_id"] = bs["unit_id"].astype(str)
        for flow in ("within", "inflow"):
            keep = set(bs.loc[(bs.flow_type == flow) & (bs.true_mean >= VOL_FLOOR), "unit_id"])
            m = pd.read_csv(LOCAL / d / f"metrics_{flow}.csv")[["unit_id", "recovery_days"]]
            m["unit_id"] = m["unit_id"].astype(str)
            m = m[m["unit_id"].isin(keep)].dropna(subset=["recovery_days"])
            m["storm"], m["flow"] = storm, flow
            recs.append(m)
    return pd.concat(recs, ignore_index=True)


# ======================================================================================
# Figure 1 — the recovery contrast
# ======================================================================================
def figure1(rec: pd.DataFrame) -> None:
    """Two panels, common x-axis: within-area overlap vs inflow separation."""
    xmax = 25.0
    bins = np.arange(0, xmax + 1, 1.0)
    panels = [("within", "Within-area recovery"), ("inflow", "Inflow recovery")]

    # sharex is essential (the panels must be visually comparable on the day axis); sharey is not,
    # and sharing it lets the tall within-area mode squash the inflow panel flat.
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 2.5), sharex=True, sharey=False)

    for ax, (flow, title) in zip(axes, panels):
        stats_txt = []
        for storm in ("helene", "milton"):
            s = rec.loc[(rec.storm == storm) & (rec.flow == flow), "recovery_days"]
            # fraction of units, so the two storms are comparable despite n = 96 vs 33
            ax.hist(s, bins=bins, weights=np.full(len(s), 1 / len(s)),
                    alpha=0.55, color=HURR_COLOR[storm], edgecolor="white", linewidth=0.4,
                    label=f"{storm.title()} (n = {len(s)})", zorder=2)
            ax.axvline(s.median(), color=HURR_COLOR[storm], lw=1.1, ls="--", zorder=3)
            stats_txt.append(
                f"{storm.title()}  {s.median():.1f} [{s.quantile(.25):.1f}, {s.quantile(.75):.1f}]"
            )

        a = rec.loc[(rec.storm == "helene") & (rec.flow == flow), "recovery_days"]
        b = rec.loc[(rec.storm == "milton") & (rec.flow == flow), "recovery_days"]
        p = stats.mannwhitneyu(a, b, alternative="two-sided")[1]
        ptxt = "P < 0.001" if p < 0.001 else f"P = {p:.3f}"
        verdict = "overlapping" if p >= 0.05 else "separated"

        ax.set_title(title, pad=4)
        ax.set_xlabel("Days from landfall to baseline")
        ax.text(0.97, 0.95, "\n".join(stats_txt) + f"\n{ptxt} ({verdict})",
                transform=ax.transAxes, ha="right", va="top", fontsize=6.2, linespacing=1.35)
        ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.62), frameon=False, handlelength=1.1)
        ax.set_xlim(0, xmax)

    axes[0].set_ylabel("Fraction of units")
    fig.tight_layout(w_pad=1.2)
    save(fig, "figureBC1_recovery_contrast")


# ======================================================================================
# Figure 2c — GAM coefficient collapse (Helene inflow)
# ======================================================================================
def figure2c() -> None:
    """Before/after dumbbell: which Helene-inflow effects survive a spatial smooth?"""
    d = pd.read_csv(NPJ / "spatial/_gam_tmp/helene_inflow_coefs.csv")
    d = d[d.term != "(Intercept)"].copy()

    LABEL = {"income": "Median income", "insurance": "Insurance %", "white": "% White",
             "dist": "Distance to track", "coastal": "Coastal"}
    m0 = d[d.model == "M0_nospace"].set_index("term")
    m1 = d[d.model == "M1_space"].set_index("term")
    order = m0.index.tolist()

    #: the two rows the manuscript discusses — shaded so the eye lands on them first
    HIGHLIGHT = {"white", "coastal"}

    fig, ax = plt.subplots(figsize=(3.6, 2.4))
    for i, term in enumerate(order):
        y = len(order) - 1 - i
        if term in HIGHLIGHT:
            ax.axhspan(y - 0.42, y + 0.42, color="#f2f2f2", zorder=0)
        e0, e1 = m0.loc[term, "estimate"], m1.loc[term, "estimate"]
        ax.plot([e0, e1], [y, y], color="0.6", lw=0.9, zorder=1)
        ax.annotate("", xy=(e1, y), xytext=(e0, y), zorder=1,
                    arrowprops=dict(arrowstyle="-|>", color="0.55", lw=0.9, shrinkA=3, shrinkB=0))
        for est, se, pv, col, mk in [
            (e0, m0.loc[term, "se"], m0.loc[term, "p"], "#7f7f7f", "o"),
            (e1, m1.loc[term, "se"], m1.loc[term, "p"], "#1f77b4", "s"),
        ]:
            ax.plot([est - 1.96 * se, est + 1.96 * se], [y, y], color=col, lw=0.8, alpha=0.5, zorder=2)
            ax.plot(est, y, mk, ms=4.5, color=col, mfc=col if pv < 0.05 else "white",
                    mew=0.9, zorder=3)

    ax.axvline(0, color="0.3", lw=0.7, ls="--", zorder=0)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([LABEL[t] for t in reversed(order)])
    ax.set_ylim(-0.6, len(order) - 0.4)          # tighten: default limits waste vertical space
    ax.set_xlabel("Effect on inflow decline (pp)")

    handles = [
        plt.Line2D([], [], marker="o", ls="", color="#7f7f7f", ms=4.5, label="without $s(x,y)$"),
        plt.Line2D([], [], marker="s", ls="", color="#1f77b4", ms=4.5, label="with $s(x,y)$"),
        plt.Line2D([], [], marker="o", ls="", color="0.3", ms=4.5, mfc="white", label="P ≥ 0.05"),
    ]
    # placed below the axes: inside the plot it collided with the "Distance to track" row
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.28),
              frameon=False, handlelength=1.0, ncol=3, columnspacing=1.2)
    fig.tight_layout()
    save(fig, "figureBC2c_gam_collapse", eps=True)


if __name__ == "__main__":
    rec = load_recovery()
    log.info("recovery units: %s",
             rec.groupby(["storm", "flow"]).size().to_dict())
    figure1(rec)
    figure2c()
    log.info("done -> %s", OUT.relative_to(ROOT))
