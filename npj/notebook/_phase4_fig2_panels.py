"""Phase 4 — regenerate the Figure 2 panels at BC-composite sizes.

Produces the four elements of the agreed Figure 2 layout, sized to assemble without gaps:

    row 1   [ Helene  within | inflow | outflow ]                 <- figureBC2a_maps_helene
    row 2   [ Milton  within | inflow | outflow ]  [ GAM ]        <- figureBC2a_maps_milton + BC2c
    row 3   [ Bayesian forest — within | inflow | outflow ]       <- figureBC2b_forest

Two changes from the existing exports, both deliberate:

1. **Column order is now within | inflow | outflow** (was outflow | within | inflow in
   `05_local_flow_maps.ipynb`). The forest reads within | inflow | outflow, so stacked in one
   display the old map order put the outflow map directly above a forest panel about *within* —
   implying a correspondence that is wrong. Aligning them makes column == flow all the way down.
   It also puts the two headline flows (restart, reconnection) first, mirroring Figure 1.

2. **The storm rows are separate files at a shared panel height.** Helene's footprint is a broad
   arc, Milton's a narrow peninsula, so at equal panel height Helene's row is much wider. Emitting
   one 2x3 grid buries that difference as dead space inside the figure; emitting two rows lets the
   GAM panel occupy the gap beside Milton during assembly.

Colour scales remain **shared per flow across both storms** (symmetric 98th-percentile cap on kept
values), exactly as the notebook computes them — so the two row files remain directly comparable.
Colourbars are drawn under the Milton row only, since it sits at the bottom of the map block.

Units below the 20k per-flow baseline-volume floor are masked (hatched grey), as in the notebook.

Requires **geopandas** -> run with the `mobility_forecast` env, not `extreme`:
    /opt/homebrew/Caskroom/miniforge/base/envs/mobility_forecast/bin/python npj/notebook/_phase4_fig2_panels.py

Outputs to `results/npj_100mi/bc_figures/` (PDF + PNG @ 450 dpi).
"""

import logging
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import LineString

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("fig2")

ROOT = Path("/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter"
            "/4_hurricane_category")
HO = Path("/Users/qing/Library/CloudStorage/OneDrive-ColumbiaUniversityIrvingMedicalCenter"
          "/hurricane_oct")
COUNTY_SHP = HO / "data/county_geo/tl_2023_us_county/tl_2023_us_county.shp"
TRACK_SHP = {"Helene": HO / "data/storm_track/helene_storm_track.shp",
             "Milton": HO / "data/storm_track/milton_storm_track.shp"}
LL = ROOT / "results/local_level"
DRIVERS = ROOT / "results/npj_100mi/drivers"
GAM_TMP = ROOT / "results/npj_100mi/spatial/_gam_tmp"
OUT = ROOT / "results/npj_100mi/bc_figures"
OUT.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 450, "savefig.bbox": "tight", "pdf.fonttype": 42, "ps.fonttype": 42,
})

HURR = {"Helene": dict(dir="helene_100mi", level="cluster", landfall="2024-09-26"),
        "Milton": dict(dir="milton_100mi", level="county", landfall="2024-10-09")}
#: within -> inflow -> outflow, matching the forest panel order (see module docstring).
FLOWS = [("within", "largest_drop", "Within: largest drop (%)"),
         ("inflow", "largest_drop", "Inflow: largest drop (%)"),
         ("outflow", "largest_increase", "Outflow: largest increase (%)")]
VOL_FLOOR = 20_000.0
CMAP = "RdBu"
ROW_W = 7.1          #: full journal figure width (inches)
#: Map panel height is fixed, NOT derived from ROW_W. Measured footprint aspects are near-identical
#: (Helene 0.76, Milton 0.78), so three panels filling 7.1 in would stand 3.11 in tall — two such
#: rows plus the forest give a 9.8 in figure, past the ~9.4 in page limit. Constraining height
#: instead leaves free width to the right of BOTH map rows, which is where the GAM panel goes.
#: 2.0 rather than 2.15 so that free column reaches ~2.4 in — at 1.9 in the GAM's y-labels
#: squeezed the axes hard enough to push its x-label off the canvas.
PANEL_H = 2.0
#: Boundary simplification tolerance, metres (EPSG:5070). At print scale 1 mm ~ 20 km, so 500 m is
#: invisible, but it takes the Helene export from ~90 MB of raw TIGER vertices to a few MB —
#: unsimplified county geometry is what makes the PDF unusable in Illustrator.
SIMPLIFY_M = 500.0
#: PURPLE/GREEN, not blue/red — must match `_phase4_bc_figures.py`. The choropleths on this very
#: figure use a RdBu scale where blue is a surge and red a drop, so coding the storms blue and red
#: made one colour pair carry two unrelated meanings within a single display. Storm identity is
#: arbitrary; red-drop/blue-surge is not, so the storms move. PRGn is colourblind-safe.
HURR_COLOR = {"helene": "#762a83", "milton": "#1b7837"}


def save(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=450, bbox_inches="tight")
    plt.close(fig)
    log.info("saved %s", stem)


# ======================================================================================
# Geometry + layers (mirrors 05_local_flow_maps.ipynb)
# ======================================================================================
log.info("loading geometry")
counties = gpd.read_file(COUNTY_SHP)[["GEOID", "STATEFP", "geometry"]].copy()
counties["GEOID"] = counties["GEOID"].astype(int)
counties = counties.to_crs(epsg=5070)
states = counties.dissolve(by="STATEFP")[["geometry"]]
counties["geometry"] = counties.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
states["geometry"] = states.geometry.simplify(SIMPLIFY_M, preserve_topology=True)


def load_track(p: Path) -> gpd.GeoDataFrame:
    t = gpd.read_file(p)
    if (t.geom_type == "Point").all():
        line = LineString(t.geometry.tolist())
    else:
        line = t.union_all() if hasattr(t, "union_all") else t.unary_union
    return gpd.GeoDataFrame(geometry=[line], crs=t.crs).to_crs(epsg=5070)


tracks = {h: load_track(p) for h, p in TRACK_SHP.items()}

_v = []
for hk, cfg in HURR.items():
    bs = pd.read_csv(LL / cfg["dir"] / "baseline_summary.csv")
    bs["storm"] = hk
    _v.append(bs[["storm", "unit_id", "flow_type", "true_mean"]])
VOL = pd.concat(_v, ignore_index=True)
VOL["unit_id"] = VOL["unit_id"].astype(str)
VOL["keep"] = (VOL["true_mean"] >= VOL_FLOOR).astype(int)


def keep_set(storm: str, flow: str) -> set:
    s = VOL[(VOL.storm == storm) & (VOL.flow_type == flow)]
    return set(s.loc[s.keep == 1, "unit_id"])


def build_layer(hur: str, flow: str, col: str) -> gpd.GeoDataFrame:
    """Metrics joined to geometry, with sub-20k units set NaN so they render hatched."""
    cfg = HURR[hur]
    ks = keep_set(hur, flow)
    m = pd.read_csv(LL / cfg["dir"] / f"metrics_{flow}.csv")[["unit_id", col]].copy()
    m.columns = ["unit_id", "value"]
    m["unit_id"] = m["unit_id"].astype(str)
    m.loc[~m["unit_id"].isin(ks), "value"] = np.nan
    if cfg["level"] == "county":
        m["GEOID"] = m["unit_id"].astype(int)
        return counties.merge(m[["GEOID", "value"]], on="GEOID", how="right")
    ca = pd.read_csv(LL / cfg["dir"] / "county_cluster_assignments.csv")[["GEOID", "cluster"]]
    ca["GEOID"] = ca["GEOID"].astype(int)
    m["cluster"] = m["unit_id"].astype(int)
    d = ca.merge(m[["cluster", "value"]], on="cluster", how="left")
    return counties.merge(d[["GEOID", "cluster", "value"]], on="GEOID", how="right")


layers = {(h, f): build_layer(h, f, c) for h in HURR for f, c, _ in FLOWS}

#: shared per-flow colour scale across BOTH storms — symmetric 98th-pct cap on kept values
norms = {}
for flow, _, _ in FLOWS:
    vals = pd.concat([layers[(h, flow)]["value"] for h in HURR]).dropna()
    vlim = float(np.nanpercentile(np.abs(vals), 98))
    norms[flow] = TwoSlopeNorm(vmin=-vlim, vcenter=0.0, vmax=vlim)
    log.info("%-8s cap +/-%.0f%% (kept max |v|=%.0f%%)", flow, vlim, np.nanmax(np.abs(vals)))


def extent(h: str) -> tuple:
    """Padded common extent for a storm, taken across its three flow layers."""
    b = np.array([layers[(h, f)].total_bounds for f, _, _ in FLOWS])
    minx, miny = b[:, 0].min(), b[:, 1].min()
    maxx, maxy = b[:, 2].max(), b[:, 3].max()
    pad = 0.05 * max(maxx - minx, maxy - miny)
    return minx - pad, miny - pad, maxx + pad, maxy + pad


EXT = {h: extent(h) for h in HURR}
ASPECT = {h: (EXT[h][2] - EXT[h][0]) / (EXT[h][3] - EXT[h][1]) for h in HURR}
log.info("aspect Helene %.2f  Milton %.2f  (near-identical: no gap beside Milton specifically)",
         ASPECT["Helene"], ASPECT["Milton"])


def map_row(storm: str, colorbars: bool) -> None:
    """One storm's three flow maps at the shared panel height.

    No per-panel letters: Figure 2 is lettered at the composite level (maps / forest / GAM)
    during assembly, so a-f here would collide with that scheme.
    """
    cfg = HURR[storm]
    is_cluster = cfg["level"] == "cluster"
    edge_c, edge_w = ("#cfcfcf", 0.1) if is_cluster else ("#666", 0.15)
    x0, y0, x1, y1 = EXT[storm]

    row_w = 3 * PANEL_H * ASPECT[storm]
    fig_h = PANEL_H + (0.62 if colorbars else 0.16)
    fig, axes = plt.subplots(1, 3, figsize=(row_w, fig_h), constrained_layout=True)

    for ax, (flow, _, _) in zip(axes, FLOWS):
        g = layers[(storm, flow)]
        counties.cx[x0:x1, y0:y1].plot(ax=ax, facecolor="#f2f2f2", edgecolor="white", linewidth=0.25)
        states.cx[x0:x1, y0:y1].boundary.plot(ax=ax, color="#9a9a9a", linewidth=0.4)
        g.plot(ax=ax, column="value", cmap=CMAP, norm=norms[flow],
               edgecolor=edge_c, linewidth=edge_w,
               missing_kwds={"color": "#dddddd", "edgecolor": "#999",
                             "linewidth": 0.15, "hatch": "///"})
        if is_cluster:
            g.dissolve(by="cluster").boundary.plot(ax=ax, color="#222", linewidth=0.45)
        tracks[storm].plot(ax=ax, color="black", linewidth=1.0)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        ax.set_axis_off()
        if colorbars is False:  # flow headings only on the top (Helene) row
            ax.set_title(flow.capitalize(), fontweight="bold", fontsize=8.5, pad=2)

    axes[0].text(-0.04, 0.5, f"{storm}\n({cfg['landfall']})", transform=axes[0].transAxes,
                 rotation=90, va="center", ha="center", fontweight="bold", fontsize=8)

    if colorbars:
        for ax, (flow, _, label) in zip(axes, FLOWS):
            sm = mpl.cm.ScalarMappable(norm=norms[flow], cmap=CMAP)
            sm.set_array([])
            cb = fig.colorbar(sm, ax=ax, location="bottom", shrink=0.92, aspect=22, pad=0.01)
            cb.set_label(label, fontsize=6.5)
            cb.ax.tick_params(labelsize=6)

    save(fig, f"figureBC2a_maps_{storm.lower()}")
    log.info("  %s row: %.2f x %.2f in", storm, row_w, fig_h)


# ======================================================================================
# Forest (overlay: both storms per DV) — full-width row 3
# ======================================================================================
GROUPS = [("Hazard", ["precip_total_7day"], "#7b3294", "#e7d4e8"),
          ("Exposure", ["dist_to_track_mi", "is_coastal"], "#1b7837", "#d9f0d3"),
          ("Vulnerability", ["median_household_income", "pct_white",
                             "insurance_coverage_pct", "pct_no_vehicle"], "#d94801", "#fdd0a2"),
          ("Structural", ["nchs_code", "pop_density"], "#525252", "#d9d9d9")]
LABEL = {"dist_to_track_mi": "Distance to track", "precip_total_7day": "Precip (7-day)",
         "median_household_income": "Median income", "insurance_coverage_pct": "Insurance %",
         "pct_white": "% White", "pct_no_vehicle": "% No vehicle", "nchs_code": "NCHS code",
         "pop_density": "Pop density", "is_coastal": "Coastal"}
DV_ORDER = ["Largest drop (within)", "Largest drop (inflow)", "Outflow surge"]


def forest() -> None:
    """Both storms overlaid per DV, compressed to a full-width strip."""
    PRED = [p for _, ps, _, _ in GROUPS for p in ps]
    GCOL = {p: c for _, ps, c, _ in GROUPS for p in ps}
    N = len(PRED)
    yp = np.arange(N)[::-1]

    POST = pd.read_csv(DRIVERS / "bayes_posterior_summary_100mi.csv").set_index(
        ["hurricane", "dv", "predictor"])
    R2 = pd.read_csv(DRIVERS / "bayes_r2_100mi.csv").set_index(["hurricane", "dv"])

    spans, idx = [], 0
    for g, ps, _, band in GROUPS:
        ys = [yp[k] for k in range(idx, idx + len(ps))]
        spans.append((band, min(ys) - 0.5, max(ys) + 0.5))
        idx += len(ps)

    off = {"helene": 0.18, "milton": -0.18}
    fig, axes = plt.subplots(1, 3, figsize=(ROW_W, 2.75))
    for j, (ax, dv) in enumerate(zip(axes, DV_ORDER)):
        for band, lo, hi in spans:
            ax.axhspan(lo, hi, color=band, alpha=0.55, zorder=0, lw=0)
        for hk in ("helene", "milton"):
            col = HURR_COLOR[hk]
            for k, p in enumerate(PRED):
                r = POST.loc[(hk, dv, p)]
                lo, hi = r["hdi_2_5"], r["hdi_97_5"]
                sig = (lo > 0) or (hi < 0)
                y = yp[k] + off[hk]
                ax.hlines(y, lo, hi, colors=col, lw=1.0, zorder=2)
                ax.plot(r["mean"], y, "o", ms=3.2, mfc=col if sig else "white",
                        mec=col, mew=0.85, zorder=3)
        ax.axvline(0, color="#666", lw=0.6, ls="--", zorder=1)
        ax.set_yticks(yp)
        if j == 0:
            labs = ax.set_yticklabels([LABEL[p] for p in PRED])
            for t, p in zip(labs, PRED):
                t.set_color(GCOL[p])
        else:
            ax.set_yticklabels([""] * N)
            ax.tick_params(axis="y", length=0)
        ax.set_ylim(-0.7, N - 0.3)
        ax.set_xlabel("Posterior β (95% HDI)")
        ax.set_title(dv, loc="left", fontsize=7.5, pad=3)
        ax.grid(axis="x", ls=":", lw=0.4, alpha=0.6, zorder=1)
        # R² moved to the caption at this size — the inline boxes collide with the CI bars
        for hk in ("helene", "milton"):
            n = int(R2.loc[(hk, dv), "n"])
            log.debug("%s %s n=%d", hk, dv, n)

    handles = [Line2D([0], [0], marker="o", color=HURR_COLOR["helene"], label="Helene"),
               Line2D([0], [0], marker="o", color=HURR_COLOR["milton"], label="Milton")]
    handles += [Patch(facecolor=band, edgecolor="none", label=g) for g, _, _, band in GROUPS]
    handles += [Line2D([0], [0], marker="o", ls="none", mfc="white", mec="#333",
                       label="HDI includes 0")]
    fig.legend(handles=handles, loc="lower center", ncol=7, frameon=False, fontsize=6.5,
               bbox_to_anchor=(0.5, -0.10))
    fig.tight_layout()
    save(fig, "figureBC2b_forest")


# ======================================================================================
# GAM collapse — resized to sit beside the Milton row
# ======================================================================================
def gam_collapse(width: float, height: float) -> None:
    """Effect on Helene inflow before vs after a spatial smooth, one offset row per model.

    The two models sit on **separate offset rows** rather than sharing one. Three of the five
    terms barely move (income -3.08 -> -2.70, insurance 1.14 -> 1.86, distance 0.90 -> 0.43), so a
    single-row dumbbell buried the grey marker under the blue one and hid the connector entirely.
    Offsetting keeps every marker visible; a diagonal connector preserves the before/after reading
    that makes this panel worth a slot.
    """
    d = pd.read_csv(GAM_TMP / "helene_inflow_coefs.csv")
    d = d[d.term != "(Intercept)"].copy()
    L = {"income": "Median income", "insurance": "Insurance %", "white": "% White",
         "dist": "Distance to track", "coastal": "Coastal"}
    m0 = d[d.model == "M0_nospace"].set_index("term")
    m1 = d[d.model == "M1_space"].set_index("term")
    order = m0.index.tolist()
    HIGHLIGHT = {"white", "coastal"}
    OFF = 0.20

    fig, ax = plt.subplots(figsize=(width, height))
    for i, term in enumerate(order):
        y = len(order) - 1 - i
        if term in HIGHLIGHT:
            ax.axhspan(y - 0.5, y + 0.5, color="#f2f2f2", zorder=0)
        e0, e1 = m0.loc[term, "estimate"], m1.loc[term, "estimate"]
        ax.annotate("", xy=(e1, y - OFF), xytext=(e0, y + OFF), zorder=1,
                    arrowprops=dict(arrowstyle="-|>", color="0.55", lw=0.7,
                                    shrinkA=2.5, shrinkB=2.5))
        for est, se, pv, col, mk, dy in [
            (e0, m0.loc[term, "se"], m0.loc[term, "p"], "#7f7f7f", "o", +OFF),
            (e1, m1.loc[term, "se"], m1.loc[term, "p"], "#1f77b4", "s", -OFF),
        ]:
            ax.plot([est - 1.96 * se, est + 1.96 * se], [y + dy, y + dy], color=col,
                    lw=0.8, alpha=0.55, zorder=2)
            ax.plot(est, y + dy, mk, ms=3.6, color=col, mfc=col if pv < 0.05 else "white",
                    mew=0.85, zorder=3)
    ax.axvline(0, color="0.3", lw=0.7, ls="--", zorder=0)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([L[t] for t in reversed(order)])
    ax.set_ylim(-0.65, len(order) - 0.35)
    ax.set_xlabel("Effect on inflow decline (pp)")
    handles = [
        Line2D([], [], marker="o", ls="", color="#7f7f7f", ms=3.6, label="without $s(x,y)$"),
        Line2D([], [], marker="s", ls="", color="#1f77b4", ms=3.6, label="with $s(x,y)$"),
        Line2D([], [], marker="o", ls="", color="0.3", ms=3.6, mfc="white", label="P ≥ 0.05"),
    ]
    leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.22),
                    frameon=False, handlelength=0.9, ncol=1, labelspacing=0.3)
    # no tight_layout: it re-fits the axes to the canvas and then clips the outside legend and the
    # x-label. bbox_inches="tight" plus an explicit extra artist is what actually keeps both.
    fig.savefig(OUT / "figureBC2c_gam_collapse.pdf", bbox_inches="tight",
                bbox_extra_artists=[leg])
    fig.savefig(OUT / "figureBC2c_gam_collapse.png", dpi=450, bbox_inches="tight",
                bbox_extra_artists=[leg])
    plt.close(fig)
    log.info("saved figureBC2c_gam_collapse")


if __name__ == "__main__":
    map_row("Helene", colorbars=False)
    map_row("Milton", colorbars=True)
    forest()
    # free column to the RIGHT OF BOTH map rows (they are height-constrained, see PANEL_H note)
    gap = ROW_W - 3 * PANEL_H * max(ASPECT.values())
    # figsize sets the AXES box; bbox_inches="tight" then adds the y-label column and the legend,
    # which measured ~0.45 in here. Request that much under the gap so the saved file fits it.
    BBOX_OVERHEAD = 0.55
    gam_w = gap - BBOX_OVERHEAD - 0.20
    log.info("free column right of the map block = %.2f in -> GAM axes %.2f in "
             "(expect ~%.2f in saved)", gap, gam_w, gam_w + BBOX_OVERHEAD)
    gam_collapse(gam_w, 3.1)
    log.info("done -> %s", OUT.relative_to(ROOT))
