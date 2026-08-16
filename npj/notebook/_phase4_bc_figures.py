"""Phase 4 — build Figure 1 (regional, by activity category) and its SI companion.

Story structure (revised 2026-08-13)
------------------------------------
    Fig 1  REGIONAL, by category   — how hard the shock was (flow change) + how long it lasted (recovery)
    Fig 2  LOCAL                   — where it fell (maps) + what predicts it (drivers), magnitudes only

Recovery is reported **only at the regional/category level**, and the local analysis carries flow
magnitudes only. That is not a presentation choice, it follows the analysis design: `PLAN.md` fixes
the three modelled DVs as `largest_drop_within`, `largest_drop_inflow` and
`largest_increase_outflow`, and states that recovery time is **not** a DV. Two facts drive it —
local recovery has almost no variance to model (within IQR ~1.4 d, Helene 4.4 [3.7, 5.1] vs Milton
4.5 [4.1, 5.4], P = 0.294), and there are no per-category local units at all. An earlier draft led
Fig 1 with local recovery histograms, which showcased a quantity the study never models; those
histograms now sit in SI as the justification for that exclusion.

Figures built here
------------------
- `figureBC1_recovery_bar_{within,inflow}` — the right-hand half of **Fig 1**. Horizontal grouped
  recovery bars, row-aligned to the day x category heatmap panels from `02_regional_heatmap.ipynb`
  that form the left-hand half. The bars carry no y tick labels; the heatmap alongside supplies
  the category names.
- `figureSI_local_recovery` — SI. Unit-level recovery distributions, the evidence that local
  recovery is too tightly concentrated to serve as a regression outcome.

Fig 1 covers **within and inflow only**. Outflow surges rather than drops, so it has no recovery
time, and including its heatmap row would leave a panel with no bar beside it; the Fig 2 maps
carry outflow instead. An earlier `figureBC1_regional_category` (paired-dot form) is superseded by
this heatmap + bars layout and has been removed.

Not built here
--------------
Every Figure 2 panel belongs to `_phase4_fig2_panels.py`. Keep one owner per output file: an
earlier version of this script also wrote `figureBC2c_gam_collapse`, so whichever script ran last
won and rebuilding Fig 1 silently reverted the GAM panel to a superseded design.

Output: `results/npj_100mi/bc_figures/` — vector PDF + PNG at 450 dpi.
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

#: Type sizes held IDENTICAL to `_phase4_fig2_panels.py` — the two display items print in the same
#: paper, and a 1 pt mismatch between them reads as a production error.
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 450, "savefig.bbox": "tight",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})
#: Nature widths are 88 mm (single) or 180 mm (double).
FIG_W = 7.09

#: Storm colours are PURPLE/GREEN, not blue/red. The heatmaps (02) and flow maps (05) use a RdBu
#: diverging scale where blue means increase and red means decrease; colouring the storms blue and
#: red as well made the same two colours carry two unrelated meanings in one display. Storm
#: identity is arbitrary whereas red-decrease/blue-increase is semantically load-bearing, so the
#: storms move. PRGn endpoints are colourblind-safe and maximally distinct from RdBu.
HURR_COLOR = {"helene": "#762a83", "milton": "#1b7837"}
HURR_DIR = {"helene": "helene_100mi", "milton": "milton_100mi"}
VOL_FLOOR = 20_000.0
UTILITIES = "Utilities"

#: flow -> (marker, y-offset, display label). Within/inflow are drops, outflow is a surge.
#: Outflow is excluded from Fig 1 entirely: it surges rather than drops, so it has no recovery
#: time and would leave a heatmap row with no bar panel beside it. The Fig 2 maps carry it.
FLOW_LABEL = {"within": "Within-area", "inflow": "Inflow"}


def save(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=450, bbox_inches="tight")
    plt.close(fig)
    log.info("saved %s", stem)


def load_regional() -> pd.DataFrame:
    """Regional per-category metrics, six categories (Utilities excluded per the live scope)."""
    d = pd.read_csv(NPJ / "regional_data/regional_metrics_summary_100mi.csv")
    d = d[d.category != UTILITIES].copy()
    assert d.category.nunique() == 6, "expected 6 categories"
    return d


def load_local_recovery() -> pd.DataFrame:
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
# Fig 1 recovery bars — horizontal, sized to sit beside the 02 heatmap panels
# ======================================================================================
#: Category order and panel geometry are taken from `02_regional_heatmap.ipynb` so the bar rows
#: line up with the heatmap rows when the two are placed side by side.
HEATMAP_CATEGORIES = ["Travel", "Work & Professional", "Health", "Education",
                      "Retail & Leisure", "Urban Government"]
HEATMAP_FIG_H = 1.8   #: heatmap panels are plt.subplots(figsize=(3.5, 1.8)), default margins
#: Shared across BOTH recovery panels on purpose. Drawn on separate scales (within 0-6, inflow
#: 0-15, as in the old regional_recovery.png) the 2x inflow difference is recoverable only by
#: reading axis numbers; on one scale the within bars are visibly short and Helene's inflow bars
#: run to the right edge.
RECOVERY_XMAX = 15.0   #: 15 not 14 so the 13.3 value label clears the right spine


def recovery_bars(reg: pd.DataFrame, flow: str) -> None:
    """Horizontal grouped recovery bars for one flow, row-aligned to the heatmap panels.

    No y tick labels: the category labels are supplied by the heatmap immediately to the left.
    Figure height and margins match the heatmap construction exactly, so six rows occupy the same
    vertical span and the pitch matches without rescaling in Illustrator.
    """
    d = reg[reg.flow_type == flow]
    piv = d.pivot_table(index="category", columns="hurricane", values="recovery_days")
    piv = piv.reindex(HEATMAP_CATEGORIES)          # Travel at top, matching the heatmap

    # same construction as the heatmap panels (no tight_layout) so the axes box matches
    fig, ax = plt.subplots(figsize=(2.6, HEATMAP_FIG_H))
    n = len(HEATMAP_CATEGORIES)
    h, off = 0.36, 0.19
    for storm, dy in (("helene", +off), ("milton", -off)):
        ys = [n - 1 - i + dy for i in range(n)]
        vals = [piv.loc[c, storm] for c in HEATMAP_CATEGORIES]
        ax.barh(ys, vals, height=h, color=HURR_COLOR[storm], label=storm.title(), zorder=2)
        for y, v in zip(ys, vals):
            ax.text(v + 0.25, y, f"{v:.1f}", va="center", ha="left", fontsize=5.8, zorder=3)

    ax.set_yticks(range(n))
    ax.set_yticklabels([])                          # labels come from the heatmap alongside
    ax.tick_params(axis="y", length=2)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(0, RECOVERY_XMAX)
    ax.set_xlabel("Recovery time (days from landfall)")
    ax.set_title(f"{FLOW_LABEL[flow]} recovery", loc="left", fontsize=8, pad=3)
    ax.grid(axis="x", ls=":", lw=0.4, alpha=0.6, zorder=0)
    # Legend only on the within panel: its bars top out at 6.1 d on a 0-15 axis, so the right half
    # is empty. On the inflow panel the 11-13 d bars run under any in-axes legend.
    if flow == "within":
        ax.legend(frameon=False, loc="lower right", handlelength=0.9, labelspacing=0.25)
    save(fig, f"figureBC1_recovery_bar_{flow}")
    log.info("  %s: axes height %.3f in over %d rows (pitch %.3f in)",
             flow, HEATMAP_FIG_H * 0.77, n, HEATMAP_FIG_H * 0.77 / n)


# ======================================================================================
# SI — local recovery distributions (why recovery is not a regression outcome)
# ======================================================================================
def figure_si_local_recovery(rec: pd.DataFrame) -> None:
    """Unit-level recovery distributions: the evidence that local recovery has little to model."""
    xmax = 25.0
    bins = np.arange(0, xmax + 1, 1.0)
    panels = [("within", "Within-area recovery", "a"), ("inflow", "Inflow recovery", "b")]

    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 2.5), sharex=True, sharey=False)
    for ax, (flow, title, letter) in zip(axes, panels):
        stats_txt = []
        for storm in ("helene", "milton"):
            s = rec.loc[(rec.storm == storm) & (rec.flow == flow), "recovery_days"]
            ax.hist(s, bins=bins, weights=np.full(len(s), 1 / len(s)),
                    alpha=0.55, color=HURR_COLOR[storm], edgecolor="white", linewidth=0.4,
                    label=f"{storm.title()} (n = {len(s)})", zorder=2)
            ax.axvline(s.median(), color=HURR_COLOR[storm], lw=1.1, ls="--", zorder=3)
            stats_txt.append(
                f"{storm.title()}  {s.median():.1f} [{s.quantile(.25):.1f}, {s.quantile(.75):.1f}]")
        a = rec.loc[(rec.storm == "helene") & (rec.flow == flow), "recovery_days"]
        b = rec.loc[(rec.storm == "milton") & (rec.flow == flow), "recovery_days"]
        p = stats.mannwhitneyu(a, b, alternative="two-sided")[1]
        ptxt = "P < 0.001" if p < 0.001 else f"P = {p:.3f}"
        ax.set_title(title, pad=4)
        ax.text(-0.10, 1.10, letter, transform=ax.transAxes, va="top", ha="left",
                fontweight="bold", fontsize=9)
        ax.set_xlabel("Days from landfall to baseline")
        ax.text(0.97, 0.95, "\n".join(stats_txt) + f"\n{ptxt}", transform=ax.transAxes,
                ha="right", va="top", fontsize=6.2, linespacing=1.35)
        ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.62), frameon=False, handlelength=1.1)
        ax.set_xlim(0, xmax)
    axes[0].set_ylabel("Fraction of units")
    fig.tight_layout(w_pad=1.2)
    save(fig, "figureSI_local_recovery")


if __name__ == "__main__":
    reg = load_regional()
    # Fig 1 = 02 heatmap panels (existing) + these two horizontal recovery bar panels
    for _flow in ("within", "inflow"):
        recovery_bars(reg, _flow)
    rec = load_local_recovery()
    log.info("local recovery units: %s", rec.groupby(["storm", "flow"]).size().to_dict())
    figure_si_local_recovery(rec)
    log.info("done -> %s", OUT.relative_to(ROOT))
