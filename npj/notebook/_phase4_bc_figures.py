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

Scope
-----
**This script owns Figure 1 only.** All Figure 2 panels — the maps, the forest and the GAM
collapse — are built by `_phase4_fig2_panels.py`. An earlier version of this file also emitted
`figureBC2c_gam_collapse`, which meant two scripts wrote the same filename and whichever ran last
won; running this one silently reverted the GAM panel to a superseded design. Keep one owner per
output file.

Output
------
`results/npj_100mi/bc_figures/figureBC1_recovery_contrast.{pdf,png}` — vector PDF for submission
plus PNG at 450 dpi. No EPS: the overlaid alpha-blended histograms do not survive EPS flattening
cleanly, so PDF is the vector format here.

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

#: Package style, dpi 450. Type sizes are held IDENTICAL to `_phase4_fig2_panels.py` — the two
#: display items print side by side in the same paper, and an 8 pt Fig 1 against a 7 pt Fig 2
#: reads as a production error.
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 450, "savefig.bbox": "tight",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})
#: Nature figure widths are 88 mm (single) or 180 mm (double). 180 mm here, matching Fig 2 —
#: the previous 139 mm was neither.
FIG_W = 7.09

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
    # Full 0-25 d common axis, nothing truncated. Only 1 within-unit exceeds 15 d and 2 inflow
    # units exceed 20 d, so panel (a) looks sparse on the right — deliberately. That emptiness IS
    # the result: panel (b) carries mass out there and panel (a) does not.
    xmax = 25.0
    bins = np.arange(0, xmax + 1, 1.0)
    panels = [("within", "Within-area recovery", "a"), ("inflow", "Inflow recovery", "b")]

    # sharex is essential (the panels must be visually comparable on the day axis); sharey is not,
    # and sharing it lets the tall within-area mode squash the inflow panel flat.
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 2.5), sharex=True, sharey=False)

    for ax, (flow, title, letter) in zip(axes, panels):
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

        # Fig 1 is a standalone file (no Illustrator compositing, unlike Fig 2), and the main text
        # cites "Figure 1a"/"Figure 1b" directly — so the letters belong in the artwork.
        ax.set_title(title, pad=4)
        ax.text(-0.10, 1.10, letter, transform=ax.transAxes, va="top", ha="left",
                fontweight="bold", fontsize=9)
        ax.set_xlabel("Days from landfall to baseline")
        ax.text(0.97, 0.95, "\n".join(stats_txt) + f"\n{ptxt} ({verdict})",
                transform=ax.transAxes, ha="right", va="top", fontsize=6.2, linespacing=1.35)
        ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.62), frameon=False, handlelength=1.1)
        ax.set_xlim(0, xmax)

    axes[0].set_ylabel("Fraction of units")
    fig.tight_layout(w_pad=1.2)
    save(fig, "figureBC1_recovery_contrast")


if __name__ == "__main__":
    rec = load_recovery()
    log.info("recovery units: %s",
             rec.groupby(["storm", "flow"]).size().to_dict())
    figure1(rec)
    log.info("done -> %s", OUT.relative_to(ROOT))
