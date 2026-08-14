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
- `figureBC1_regional_category` — **Fig 1**. (a) flow change per category, three flows, both
  storms; (b) recovery per category, within and inflow (outflow surges rather than drops, so it
  has no recovery time). Milton takes the deeper shock in (a); Helene stays disrupted far longer
  on inflow in (b) — sharper-but-shorter against milder-but-protracted, in one display.
- `figureSI_local_recovery` — SI. Unit-level recovery distributions, the evidence that local
  recovery is too tightly concentrated to serve as a regression outcome.

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

HURR_COLOR = {"helene": "#1f77b4", "milton": "#d62728"}
HURR_DIR = {"helene": "helene_100mi", "milton": "milton_100mi"}
VOL_FLOOR = 20_000.0
UTILITIES = "Utilities"

#: flow -> (marker, y-offset, display label). Within/inflow are drops, outflow is a surge.
FLOW_STYLE = {
    "within": ("o", +0.25, "Within-area"),
    "inflow": ("s", 0.00, "Inflow"),
    "outflow": ("^", -0.25, "Outflow"),
}


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


def _paired_rows(ax, piv, cats, flows, value_of) -> None:
    """Draw one grey connector per (category, flow) with a storm-coloured marker at each end.

    The connector length *is* the between-storm gap for that cell, so the reader compares gaps by
    length rather than by reading two axis positions.
    """
    for i, cat in enumerate(cats):
        y = len(cats) - 1 - i
        for flow in flows:
            mk, off, _ = FLOW_STYLE[flow]
            h, m = value_of(piv, cat, flow, "helene"), value_of(piv, cat, flow, "milton")
            if np.isnan(h) or np.isnan(m):
                continue
            ax.plot([h, m], [y + off, y + off], color="0.55", lw=0.9, zorder=1,
                    solid_capstyle="round")
            for val, storm in ((h, "helene"), (m, "milton")):
                ax.plot(val, y + off, mk, ms=4.2, color=HURR_COLOR[storm],
                        mec="white", mew=0.6, zorder=3)


# ======================================================================================
# Figure 1 — regional, by activity category
# ======================================================================================
def figure1_regional(reg: pd.DataFrame) -> None:
    """(a) flow change per category; (b) recovery per category. Both storms, six categories."""
    # magnitude: drops for within/inflow, surge for outflow — one signed axis, zero marked
    mag = reg.copy()
    mag["value"] = np.where(mag.flow_type == "outflow",
                            mag.largest_increase, mag.largest_drop)
    piv_mag = mag.pivot_table(index="category", columns=["flow_type", "hurricane"], values="value")
    piv_rec = reg.pivot_table(index="category", columns=["flow_type", "hurricane"],
                              values="recovery_days")

    # order by Helene inflow recovery: the series that separates, so (b) reads as a gradient
    cats = piv_rec[("inflow", "helene")].sort_values().index.tolist()

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(FIG_W, 2.75), sharey=True)

    _paired_rows(ax_a, piv_mag, cats, ("within", "inflow", "outflow"),
                 lambda p, c, f, h: p.loc[c, (f, h)])
    ax_a.axvline(0, color="0.3", lw=0.7, ls="--", zorder=0)
    ax_a.set_xlabel("Change from baseline (%)")
    ax_a.set_title("Flow change", pad=4)

    # outflow surges rather than drops, so it has no recovery time — within and inflow only
    _paired_rows(ax_b, piv_rec, cats, ("within", "inflow"),
                 lambda p, c, f, h: p.loc[c, (f, h)])
    ax_b.set_xlabel("Days from landfall to baseline")
    ax_b.set_title("Recovery time", pad=4)
    ax_b.set_xlim(0, None)

    for ax, letter in ((ax_a, "a"), (ax_b, "b")):
        ax.set_yticks(range(len(cats)))
        ax.set_ylim(-0.6, len(cats) - 0.4)
        ax.grid(axis="x", ls=":", lw=0.4, alpha=0.6, zorder=0)
        ax.text(-0.02, 1.12, letter, transform=ax.transAxes, va="top", ha="right",
                fontweight="bold", fontsize=9)
    ax_a.set_yticklabels(list(reversed(cats)))

    handles = [plt.Line2D([], [], marker=FLOW_STYLE[f][0], ls="", color="#555", ms=4.2,
                          label=FLOW_STYLE[f][2]) for f in ("within", "inflow", "outflow")]
    handles += [plt.Line2D([], [], marker="o", ls="", color=HURR_COLOR[s], ms=4.2,
                           label=s.title()) for s in ("helene", "milton")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
               bbox_to_anchor=(0.5, -0.10), handlelength=1.0, columnspacing=1.4)
    fig.tight_layout(w_pad=1.0)
    save(fig, "figureBC1_regional_category")


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
    figure1_regional(reg)
    rec = load_local_recovery()
    log.info("local recovery units: %s", rec.groupby(["storm", "flow"]).size().to_dict())
    figure_si_local_recovery(rec)
    log.info("done -> %s", OUT.relative_to(ROOT))
