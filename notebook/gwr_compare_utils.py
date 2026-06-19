"""
gwr_compare_utils.py
====================
Shared pipeline for a *directly comparable* spatial analysis of Hurricanes
Helene and Milton. Both hurricanes are driven through the IDENTICAL sequence —
global OLS  →  Moran's I diagnostics  →  GWR  →  matched figures — reading from
the single pooled dataset so the same features, DVs, colour scales and figure
layouts are used for each storm.

Spatial unit differs by storm (this is the only branch in the data loader):
  * Helene  -> 38 income x NCHS spatially-constrained clusters
  * Milton  -> 21 Florida counties (50-mi cut)

Designed to be imported from a notebook whose cwd is the `notebook/` folder, but
all paths are resolved relative to THIS file so it also runs from the repo root.

Author: generated for the Helene/Milton npj comparison.
"""
from __future__ import annotations

import os
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString

import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from libpysal.weights import Queen, KNN
from esda.moran import Moran
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────
# Paths — resolved relative to this file, so cwd does not matter
# ──────────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))          # .../notebook
_REPO = os.path.dirname(_HERE)                              # repo root
_SIB = os.path.join(os.path.dirname(_REPO), "hurricane_oct")  # sibling repo

POOLED      = os.path.join(_REPO, "results/local_level/regression/pooled_dataset.csv")
COUNTY_SHP  = os.path.join(_SIB, "data/county_geo/tl_2023_us_county/tl_2023_us_county.shp")
CLUSTER_CSV = os.path.join(_REPO, "results/helene_clustering/county_cluster_assignments.csv")
MILTON_CUT  = os.path.join(_REPO, "results/milton/counties_geoid_cut_50.txt")
GEOID_NAMES = os.path.join(_HERE, "geoid_idx_names.csv")

def track_path(hurricane: str) -> str:
    return os.path.join(_SIB, f"data/storm_track/{hurricane}_storm_track.shp")

def results_dir(hurricane: str) -> str:
    d = os.path.join(_REPO, "results/gwr_compare", hurricane)
    os.makedirs(os.path.join(d, "figures"), exist_ok=True)
    return d

# ──────────────────────────────────────────────────────────────────────────
# Analysis spec — IDENTICAL for both storms
# ──────────────────────────────────────────────────────────────────────────
FEATURES = ["median_household_income", "pct_white", "nchs_code", "dist_to_track_mi"]
FEATURE_LABELS = {
    "median_household_income": "Median HH income",
    "pct_white": "% White",
    "nchs_code": "NCHS urban–rural",
    "dist_to_track_mi": "Dist. to track (mi)",
}
DVS = [
    ("largest_drop_within",  "Largest Drop — Within (%)"),
    ("recovery_days_within", "Recovery Time — Within (days)"),
]
HURR = {
    "helene": {"title": "Helene", "unit": "cluster", "n_expected": 38},
    "milton": {"title": "Milton", "unit": "county",  "n_expected": 21},
}

# ──────────────────────────────────────────────────────────────────────────
# 1. Data loader (the only storm-specific branch)
# ──────────────────────────────────────────────────────────────────────────
def load_units(hurricane: str):
    """Return (gdf, track_gdf) in EPSG:5070 with DVs, FEATURES and centroids.

    gdf rows are the analysis units (Helene clusters / Milton counties).
    """
    pooled = pd.read_csv(POOLED)
    df = pooled[pooled["hurricane"] == hurricane].copy().reset_index(drop=True)

    counties = gpd.read_file(COUNTY_SHP)
    counties["GEOID"] = counties["GEOID"].astype(int)

    if hurricane == "helene":
        df["cluster"] = df["NAME"].str.replace("Cluster_", "").astype(int)
        ca = pd.read_csv(CLUSTER_CSV)
        ca["GEOID"] = ca["GEOID"].astype(int)
        gc = counties[counties["GEOID"].isin(ca["GEOID"])].merge(
            ca[["GEOID", "cluster"]], on="GEOID", how="left").to_crs(epsg=5070)
        units = gc.dissolve(by="cluster")[["geometry"]].reset_index()
        gdf = units.merge(df, on="cluster", how="left")
        key = "cluster"
    elif hurricane == "milton":
        cut = set(int(x) for x in open(MILTON_CUT).read().split())
        gidx = pd.read_csv(GEOID_NAMES)
        # restrict national name list to the 21 Milton GEOIDs -> names unique
        sub = gidx[gidx["GEOID"].isin(cut)]
        name2geoid = dict(zip(sub["NAME"], sub["GEOID"]))
        df["GEOID"] = df["NAME"].map(name2geoid).astype(int)
        gc = counties[counties["GEOID"].isin(cut)].to_crs(epsg=5070)
        gdf = gc[["GEOID", "geometry"]].merge(df, on="GEOID", how="left")
        key = "GEOID"
    else:
        raise ValueError(f"unknown hurricane: {hurricane}")

    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:5070")
    gdf = gdf.sort_values(key).reset_index(drop=True)
    c = gdf.geometry.centroid
    gdf["centroid_x"], gdf["centroid_y"] = c.x, c.y

    track = gpd.read_file(track_path(hurricane)).to_crs(epsg=5070)
    if track.geometry.geom_type.iloc[0] == "Point":
        line = LineString(track.geometry.tolist())
    else:
        line = track.geometry.union_all()
    track_gdf = gpd.GeoDataFrame(geometry=[line], crs="EPSG:5070")
    return gdf, track_gdf


def prep_model(gdf, dvs=DVS, features=FEATURES):
    """Drop NaN rows, z-score features. Returns (gdf_model, X_z DataFrame)."""
    mask = gdf[features + [d[0] for d in dvs]].notna().all(axis=1)
    g = gdf[mask].copy().reset_index(drop=True)
    X_z = pd.DataFrame(StandardScaler().fit_transform(g[features]),
                       columns=features, index=g.index)
    for f in features:
        g[f + "_z"] = X_z[f]
    return g, X_z

# ──────────────────────────────────────────────────────────────────────────
# 2. Global OLS baseline
# ──────────────────────────────────────────────────────────────────────────
def run_ols(g, X_z, dvs=DVS):
    out = {}
    X = sm.add_constant(X_z.values)
    for dv, lab in dvs:
        out[dv] = sm.OLS(g[dv].values, X).fit()
    return out


def ols_table(ols, dvs=DVS, features=FEATURES):
    rows = []
    names = ["const"] + features
    for dv, lab in dvs:
        m = ols[dv]
        for n, b, p in zip(names, m.params, m.pvalues):
            rows.append({"dv": lab, "term": n, "beta": round(b, 3),
                         "p": round(p, 4), "R2": round(m.rsquared, 3),
                         "adjR2": round(m.rsquared_adj, 3)})
    return pd.DataFrame(rows)

# ──────────────────────────────────────────────────────────────────────────
# 3. Spatial diagnostics — the "should we GWR" gate (Moran's I)
# ──────────────────────────────────────────────────────────────────────────
def spatial_diagnostics(g, ols, dvs=DVS):
    w_queen = Queen.from_dataframe(g, use_index=False)
    w_knn = KNN.from_dataframe(g, k=4, use_index=False)
    rows = []
    for dv, lab in dvs:
        resid = ols[dv].resid
        for w, wl in [(w_queen, "Queen"), (w_knn, "KNN4")]:
            mi = Moran(resid, w, permutations=999)
            rows.append({"dv": lab, "test": f"Moran_{wl}",
                         "I": round(mi.I, 4), "p": round(mi.p_sim, 4)})
    diag = pd.DataFrame(rows)
    diag["proceed_gwr"] = bool((diag["p"] < 0.10).any())
    return diag, (w_queen, w_knn)

# ──────────────────────────────────────────────────────────────────────────
# 4. GWR
# ──────────────────────────────────────────────────────────────────────────
def fit_gwr(g, X_z, dvs=DVS):
    coords = list(zip(g["centroid_x"].values, g["centroid_y"].values))
    X_mat = X_z.values
    n_var = X_mat.shape[1] + 1                      # +1 intercept
    bw_min = max(n_var + 3, 8)
    bw_max = len(g) - 1
    out = {}
    for dv, lab in dvs:
        y = g[[dv]].values
        try:
            sel = Sel_BW(coords, y, X_mat, fixed=False, kernel="bisquare")
            bw = sel.search(criterion="AICc", bw_min=bw_min, bw_max=bw_max)
            mod = GWR(coords, y, X_mat, bw, fixed=False, kernel="bisquare").fit()
            out[dv] = {"model": mod, "bw": bw, "ok": True}
        except Exception as e:                       # pragma: no cover
            out[dv] = {"model": None, "bw": None, "ok": False, "err": str(e)}
    return out, (bw_min, bw_max)


def model_comparison(g, ols, gwr, dvs=DVS):
    """OLS vs GWR AICc / R² table.

    OLS AICc uses statsmodels' full Gaussian ``m.aic`` (which includes the
    n·log(2π)+n constant) plus the small-sample correction, so it sits on the
    SAME scale as mgwr's GWR ``aicc`` and the two are directly comparable.
    """
    def ols_aicc(m, n):
        k = m.df_model + 1
        return m.aic + (2 * k * (k + 1)) / max(n - k - 1, 1)
    rows = []
    n = len(g)
    for dv, lab in dvs:
        m = ols[dv]
        row = {"dv": lab, "N": n,
               "OLS_AICc": round(ols_aicc(m, n), 2),
               "OLS_R2": round(m.rsquared, 3),
               "OLS_adjR2": round(m.rsquared_adj, 3)}
        gr = gwr.get(dv)
        if gr and gr["ok"]:
            mod = gr["model"]
            row.update({"GWR_AICc": round(mod.aicc, 2),
                        "GWR_R2": round(mod.R2, 3),
                        "GWR_adjR2": round(mod.adj_R2, 3),
                        "GWR_bw": gr["bw"],
                        "dAICc": round(mod.aicc - row["OLS_AICc"], 2)})
        rows.append(row)
    return pd.DataFrame(rows)

# ──────────────────────────────────────────────────────────────────────────
# 5. Figures — IDENTICAL code/scales for both storms
# ──────────────────────────────────────────────────────────────────────────
def _suptitle(fig, hurricane, text):
    meta = HURR[hurricane]
    fig.suptitle(f"Hurricane {meta['title']} ({meta['unit']}-level)  —  {text}",
                 fontsize=14, fontweight="bold")


def plot_residual_maps(g, ols, track, hurricane, dvs=DVS, save=True):
    """OLS residual choropleth per DV (red=over-, blue=under-predicted)."""
    n = len(dvs)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 6))
    axes = np.atleast_1d(axes)
    for ax, (dv, lab) in zip(axes, dvs):
        gg = g.copy()
        gg["resid"] = ols[dv].resid
        v = np.abs(gg["resid"]).max()
        gg.plot(column="resid", cmap="RdBu_r", vmin=-v, vmax=v, legend=True,
                edgecolor="black", linewidth=0.3, ax=ax,
                legend_kwds={"label": "OLS residual", "shrink": 0.55})
        track.plot(ax=ax, color="black", linewidth=1.6)
        ax.set_title(lab, fontsize=12)
        ax.set_axis_off()
    _suptitle(fig, hurricane, "OLS residual maps")
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(results_dir(hurricane), "figures",
                                 "fig1_ols_residual_maps.png"),
                    dpi=150, bbox_inches="tight")
    return fig


def plot_morans(diag, hurricane, ylim=(-0.4, 0.55), save=True):
    """Grouped bar chart of Moran's I (Queen vs KNN4) per DV with sig stars."""
    dvs = diag["dv"].unique().tolist()
    tests = ["Moran_Queen", "Moran_KNN4"]
    colors = {"Moran_Queen": "#4C72B0", "Moran_KNN4": "#DD8452"}
    width = 0.36
    x = np.arange(len(dvs))
    fig, ax = plt.subplots(figsize=(2.6 * len(dvs) + 3, 5))
    for i, t in enumerate(tests):
        vals, ps = [], []
        for dv in dvs:
            r = diag[(diag.dv == dv) & (diag.test == t)].iloc[0]
            vals.append(r["I"]); ps.append(r["p"])
        bars = ax.bar(x + (i - 0.5) * width, vals, width,
                      label=t.replace("Moran_", "").replace("KNN4", "KNN (k=4)"),
                      color=colors[t], edgecolor="black", linewidth=0.6)
        for b, val, p in zip(bars, vals, ps):
            star = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
            off = 0.012 if val >= 0 else -0.04
            ax.text(b.get_x() + b.get_width() / 2, val + off,
                    f"{val:+.2f}{star}", ha="center",
                    va="bottom" if val >= 0 else "top", fontsize=9)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" — ", "\n") for d in dvs], fontsize=10)
    ax.set_ylabel("Moran's I  (OLS residuals)")
    ax.set_ylim(*ylim)
    ax.legend(title="Spatial weights", fontsize=9)
    proceed = bool(diag["proceed_gwr"].iloc[0]) if "proceed_gwr" in diag else None
    gate = "" if proceed is None else f"   |   GWR gate (any p<0.10): {proceed}"
    _suptitle(plt.gcf(), hurricane, "Spatial autocorrelation of OLS residuals" + gate)
    ax.text(0.99, 0.02, "stars: * p<0.10  ** p<0.05  *** p<0.01",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            color="grey")
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(results_dir(hurricane), "figures",
                                 "fig2_morans_I.png"), dpi=150, bbox_inches="tight")
    return fig


def plot_local_r2(g, gwr, track, hurricane, dvs=DVS, save=True):
    """GWR local R² choropleth per DV (shared 0–1 scale)."""
    n = len(dvs)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 6))
    axes = np.atleast_1d(axes)
    for ax, (dv, lab) in zip(axes, dvs):
        gr = gwr.get(dv)
        if not (gr and gr["ok"]):
            ax.text(0.5, 0.5, f"GWR n/a\n{lab}", ha="center", va="center")
            ax.set_axis_off(); continue
        gg = g.copy()
        gg["local_R2"] = gr["model"].localR2.flatten()
        gg.plot(column="local_R2", cmap="viridis", vmin=0, vmax=1, legend=True,
                edgecolor="black", linewidth=0.3, ax=ax,
                legend_kwds={"label": "Local R²", "shrink": 0.55})
        track.plot(ax=ax, color="red", linewidth=1.6)
        ax.set_title(f"{lab}\n(bw={gr['bw']} neighbours)", fontsize=12)
        ax.set_axis_off()
    _suptitle(fig, hurricane, "GWR local R²")
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(results_dir(hurricane), "figures",
                                 "fig3_gwr_local_R2.png"), dpi=150, bbox_inches="tight")
    return fig


def plot_coef_tmaps(g, gwr, track, hurricane, dv, dv_label,
                    features=FEATURES, tcap=4.0, save=True):
    """Per-predictor GWR t-stat maps for one DV (|t|>1.96 highlighted)."""
    gr = gwr.get(dv)
    if not (gr and gr["ok"]):
        return None
    mod = gr["model"]
    gg = g.copy()
    for i, fn in enumerate(["intercept"] + features):
        gg[f"t_{fn}"] = mod.tvalues[:, i]
    fig, axes = plt.subplots(1, len(features), figsize=(4.6 * len(features), 5))
    axes = np.atleast_1d(axes)
    for ax, fn in zip(axes, features):
        gg["_sig"] = np.where(np.abs(gg[f"t_{fn}"]) > 1.96, gg[f"t_{fn}"], np.nan)
        gg.plot(column="_sig", cmap="RdBu_r", vmin=-tcap, vmax=tcap,
                missing_kwds={"color": "lightgrey"}, legend=True,
                edgecolor="black", linewidth=0.3, ax=ax,
                legend_kwds={"label": "t  (|t|>1.96)", "shrink": 0.5})
        track.plot(ax=ax, color="black", linewidth=1.2)
        ax.set_title(FEATURE_LABELS.get(fn, fn), fontsize=11)
        ax.set_axis_off()
    _suptitle(fig, hurricane, f"GWR local t-stats — {dv_label}")
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(results_dir(hurricane), "figures",
                                 f"fig4_gwr_tstats_{dv}.png"),
                    dpi=150, bbox_inches="tight")
    return fig


def plot_model_comparison(cmp_df, hurricane, save=True):
    """OLS vs GWR: AICc (lower=better) and adj-R² side-by-side bars per DV."""
    dvs = cmp_df["dv"].tolist()
    x = np.arange(len(dvs))
    w = 0.36
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.bar(x - w / 2, cmp_df["OLS_AICc"], w, label="OLS",
            color="#B0B0B0", edgecolor="black")
    if "GWR_AICc" in cmp_df:
        ax1.bar(x + w / 2, cmp_df["GWR_AICc"], w, label="GWR",
                color="#55A868", edgecolor="black")
    ax1.set_xticks(x); ax1.set_xticklabels([d.replace(" — ", "\n") for d in dvs])
    ax1.set_ylabel("AICc  (lower = better)"); ax1.set_title("Model fit — AICc")
    ax1.legend()

    ax2.bar(x - w / 2, cmp_df["OLS_adjR2"], w, label="OLS adj-R²",
            color="#B0B0B0", edgecolor="black")
    if "GWR_adjR2" in cmp_df:
        ax2.bar(x + w / 2, cmp_df["GWR_adjR2"], w, label="GWR adj-R²",
                color="#55A868", edgecolor="black")
    ax2.set_xticks(x); ax2.set_xticklabels([d.replace(" — ", "\n") for d in dvs])
    ax2.set_ylabel("Adjusted R²"); ax2.set_title("Explained variance — adj-R²")
    ax2.legend()

    _suptitle(fig, hurricane, "OLS vs GWR")
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(results_dir(hurricane), "figures",
                                 "fig5_model_comparison.png"),
                    dpi=150, bbox_inches="tight")
    return fig

# ──────────────────────────────────────────────────────────────────────────
# 6. One-call driver (used by the test harness; notebooks call steps directly)
# ──────────────────────────────────────────────────────────────────────────
def run_all(hurricane, dvs=DVS, save=True, show=False):
    gdf, track = load_units(hurricane)
    g, X_z = prep_model(gdf, dvs)
    ols = run_ols(g, X_z, dvs)
    diag, _ = spatial_diagnostics(g, ols, dvs)
    gwr, bw_bounds = fit_gwr(g, X_z, dvs)
    cmp_df = model_comparison(g, ols, gwr, dvs)

    if save:
        d = results_dir(hurricane)
        ols_table(ols, dvs).to_csv(os.path.join(d, "ols_coefficients.csv"), index=False)
        diag.to_csv(os.path.join(d, "spatial_diagnostics.csv"), index=False)
        cmp_df.to_csv(os.path.join(d, "model_comparison.csv"), index=False)

    plot_residual_maps(g, ols, track, hurricane, dvs, save)
    plot_morans(diag, hurricane, save=save)
    plot_local_r2(g, gwr, track, hurricane, dvs, save)
    for dv, lab in dvs:
        plot_coef_tmaps(g, gwr, track, hurricane, dv, lab, save=save)
    plot_model_comparison(cmp_df, hurricane, save)
    if show:
        plt.show()
    plt.close("all")
    return {"gdf": g, "ols": ols, "diag": diag, "gwr": gwr,
            "cmp": cmp_df, "track": track, "bw_bounds": bw_bounds}
