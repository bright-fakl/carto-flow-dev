"""Baseline against density-field repair: error against shrink and target size, where, and the continuation past the stall."""
import warnings, sys, json; warnings.filterwarnings("ignore")
import numpy as np, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
sys.path.insert(0, ".")
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import carto_flow.flow_cartogram.algorithm as alg
import inv
out = sys.argv[1]
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v); A0 = shapely.area(g.geometry.values)

def evaluate(o, cell2):
    a = shapely.area(o); val = shapely.is_valid(o)
    T = v / v[val].sum() * a[val].sum(); e = np.maximum(abs(a - T) / T * 100, 0.01)
    return dict(o=o, a=a, val=val, T=T, e=e, s=T / A0, tc=T / cell2)

R = {}; CONT = {}
for mode in ("base", "repair"):
    alg.INV_HOOK = inv.InvHook(repair=True, exclude=False) if mode == "repair" else None
    w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False))
    c = w[-1]; cell2 = c.grid.dx * c.grid.dy
    R[mode] = evaluate(np.array(c.get_geometry(), dtype=object), cell2)
    # continuation past the stall on the finest grid
    c2 = w.morph(options=MorphOptions(area_scale=1e-6, grid=2048, n_iter=1500, stall_patience=None, snapshot_every=50, show_progress=False))
    rows = []; lag = None
    for sn in c2.snapshots.snapshots:
        r = evaluate(np.array(sn.geometry, dtype=object), cell2); val = r["val"]; e = r["e"]
        if lag is None: lag = val & (e > 10)
        rows.append(dict(it=sn.iteration, n_inv=int((~val).sum()), mean=float(e[val].mean()), median=float(np.median(e[val])), p95=float(np.percentile(e[val], 95)),
                         n10=int((e[val] > 10).sum()), lag_median=float(np.median(e[lag & val])), inv_mean=float(e[~val].mean()) if (~val).any() else 0.0))
    CONT[mode] = rows
json.dump(CONT, open(f"{out}/continue_base_repair.json", "w"))

INK, MUTED, GRID, RED, BLUE = "#1f2933", "#6b7785", "#e4e7eb", "#c0392b", "#2a62a3"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})
BL = ["#143a6e", "#2a62a3", "#4f8fc7", "#a9c8e6"]
NAMES = {"base": "baseline", "repair": "density field repaired"}

def scatter_fig(fname, xkey, xlabel, classkey, edges, labels, title):
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)
    for ax, mode in zip(axs, ("base", "repair")):
        r = R[mode]; x = r[xkey]; k = r[classkey]; val = r["val"]
        cls = [(k >= lo) & (k < hi) for lo, hi in zip(edges[:-1], edges[1:])]
        for m, col, lab in zip(cls, BL, labels):
            mm = m & val
            ax.scatter(x[mm], r["e"][mm], s=12, color=col, alpha=0.85, edgecolor="white", linewidth=0.3, label=f"{lab} ({int(mm.sum())})")
        ax.scatter(x[~val], r["e"][~val], s=26, marker="x", color=RED, linewidth=1.1, label=f"invalid polygon ({int((~val).sum())})")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.axhline(10, color=RED, lw=0.8, alpha=0.6)
        ax.set_xlabel(xlabel); ax.set_title(NAMES[mode], loc="left", fontsize=10)
        if mode == "base": ax.set_ylabel("absolute area error (%), valid targets")
        ax.legend(frameon=False, title=title, loc="lower left", fontsize=8, title_fontsize=8, markerscale=1.3)
    fig.tight_layout(); fig.savefig(f"{out}/{fname}", dpi=150); plt.close(fig)

scatter_fig("fig1_error_vs_shrink.png", "s", "shrink factor: target area / original area", "tc", [0, 1, 4, 16, 1e12],
            ["target < 1 cell²", "1 to 4", "4 to 16", "16 or more"], "target area")
scatter_fig("fig2_error_vs_target.png", "tc", "target area in grid cells² (4.26 km cells)", "s", [0, 0.03, 0.1, 0.3, 1e9],
            ["shrink < 0.03", "0.03 to 0.1", "0.1 to 0.3", "0.3 or more"], "shrink factor")

sb = [0, 0.01, 0.03, 0.1, 0.3, 1, 3, 100]; tb = [0, 1, 4, 16, 64, 1e12]
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.6), sharey=True)
for ax, mode in zip(axs, ("base", "repair")):
    r = R[mode]; e = r["e"]; s = r["s"]; tc = r["tc"]; val = r["val"]
    share = np.full((len(sb) - 1, len(tb) - 1), np.nan); cnt = np.zeros_like(share, int)
    for i in range(len(sb) - 1):
        for j in range(len(tb) - 1):
            m = val & (s >= sb[i]) & (s < sb[i + 1]) & (tc >= tb[j]) & (tc < tb[j + 1]); cnt[i, j] = m.sum()
            if m.sum(): share[i, j] = 100 * (e[m] > 10).mean()
    ax.grid(False); ax.imshow(share, cmap="Blues", vmin=0, vmax=80, aspect="auto", origin="lower")
    for i in range(share.shape[0]):
        for j in range(share.shape[1]):
            if cnt[i, j]: ax.text(j, i, f"{share[i, j]:.0f} %\nn={cnt[i, j]}", ha="center", va="center", fontsize=8, color="white" if share[i, j] > 40 else INK)
    ax.set_xticks(range(len(tb) - 1)); ax.set_xticklabels(["< 1", "1 to 4", "4 to 16", "16 to 64", "64 +"])
    ax.set_yticks(range(len(sb) - 1)); ax.set_yticklabels(["< 0.01", "0.01 to 0.03", "0.03 to 0.1", "0.1 to 0.3", "0.3 to 1", "1 to 3", "3 +"])
    ax.set_xlabel("target area in grid cells²"); ax.set_title(f"{NAMES[mode]}: share of valid counties above 10 %", loc="left", fontsize=10)
    if mode == "base": ax.set_ylabel("shrink factor (target / original)")
    for sp in ax.spines.values(): sp.set_visible(False)
fig.tight_layout(); fig.savefig(f"{out}/fig3_share_over_10pct.png", dpi=150); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(14, 4.8))
for ax, mode in zip(axs, ("base", "repair")):
    r = R[mode]; ax.axis("off"); gs = gpd.GeoSeries(list(r["o"]), crs=g.crs)
    good = r["val"] & (r["e"] <= 10); lagging = r["val"] & (r["e"] > 10); invalid = ~r["val"]
    gs[good].plot(ax=ax, color="#d5dae0", edgecolor="white", linewidth=0.1)
    gs[lagging].plot(ax=ax, color=RED, edgecolor=RED, linewidth=0.3)
    gs[invalid].plot(ax=ax, color="#1f2933", edgecolor="#1f2933", linewidth=0.3)
    ax.set_title(f"{NAMES[mode]}: {int(lagging.sum())} valid counties above 10 % (red), {int(invalid.sum())} invalid (black)", loc="left", fontsize=10)
fig.tight_layout(); fig.savefig(f"{out}/fig4_where.png", dpi=150); plt.close(fig)

fig, axs = plt.subplots(1, 3, figsize=(14, 4.0))
col = {"base": MUTED, "repair": BLUE}
for mode in ("base", "repair"):
    rows = CONT[mode]; it = [r["it"] for r in rows]
    axs[0].plot(it, [r["lag_median"] for r in rows], color=col[mode], lw=2, label=NAMES[mode])
    axs[1].plot(it, [max(r["median"], 1e-4) for r in rows], color=col[mode], lw=2, ls="-", label=f"median, {NAMES[mode]}")
    axs[1].plot(it, [r["mean"] for r in rows], color=col[mode], lw=1.4, ls="--", label=f"mean, {NAMES[mode]}")
    axs[2].plot(it, [r["n_inv"] for r in rows], color=col[mode], lw=2, label=NAMES[mode])
axs[0].set_yscale("log"); axs[0].set_title("lagging valid counties (median error)", loc="left", fontsize=10); axs[0].legend(frameon=False)
axs[1].set_yscale("log"); axs[1].set_title("valid counties (median solid, mean dashed)", loc="left", fontsize=8.5); axs[1].legend(frameon=False, fontsize=7.5)
axs[2].set_title("invalid polygons", loc="left", fontsize=10); axs[2].set_ylim(0, None)
for ax in axs: ax.set_xlabel("iterations after the stall (finest level)")
axs[0].set_ylabel("error (%), valid targets"); fig.tight_layout(); fig.savefig(f"{out}/fig5_past_stall.png", dpi=150); plt.close(fig)
for mode in ("base", "repair"):
    r = R[mode]; e = r["e"]; val = r["val"]
    print(mode, "invalid", int((~val).sum()), "valid >10%", int((e[val] > 10).sum()), "median", float(np.median(e[val])))
    print("  continuation last:", CONT[mode][-1])
