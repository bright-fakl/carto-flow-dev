"""Relation between original area, target area and area error of the county flow cartogram (1 km input, auto ladder)."""
import warnings; warnings.filterwarnings("ignore")
import sys, numpy as np, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
out = sys.argv[1]
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v)
w = CartogramWorkflow(gdf, "v", validate=False)
w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False))
c = w[-1]; o = np.array(c.get_geometry(), dtype=object); a = shapely.area(o)
A0 = shapely.area(g.geometry.values); T = v / v.sum() * a.sum(); cell2 = c.grid.dx * c.grid.dy
e = np.maximum(abs(a - T) / T * 100, 0.01); s = T / A0; tc = T / cell2
INK, MUTED, GRID, RED = "#1f2933", "#6b7785", "#e4e7eb", "#c0392b"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})
BLUES = ["#143a6e", "#2a62a3", "#4f8fc7", "#a9c8e6"]

def scatter(x, xlabel, classes, labels, fname, title, xlog=True, vline=None):
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for m, col, lab in zip(classes, BLUES, labels):
        ax.scatter(x[m], e[m], s=14, color=col, alpha=0.85, edgecolor="white", linewidth=0.3, label=f"{lab} ({int(m.sum())})")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.axhline(10, color=RED, lw=1); ax.text(ax.get_xlim()[0], 10.6, " 10 % (convergence limit)", color=RED, fontsize=8.5, va="bottom")
    if vline is not None:
        ax.axvline(vline, color=MUTED, lw=1, ls=(0, (4, 3)))
    ax.set_xlabel(xlabel); ax.set_ylabel("absolute area error (%)")
    ax.legend(frameon=False, title=title, loc="lower left", fontsize=9, title_fontsize=9, markerscale=1.4)
    fig.tight_layout(); fig.savefig(f"{out}/{fname}", dpi=150); plt.close(fig)

tclass = [tc < 1, (tc >= 1) & (tc < 4), (tc >= 4) & (tc < 16), tc >= 16]
scatter(s, "shrink factor: target area / original area  (left = shrinks more)", tclass,
        ["target < 1 cell²", "1 to 4", "4 to 16", "16 or more"], "fig1_error_vs_shrink.png", "target area (n counties)")
sclass = [s < 0.03, (s >= 0.03) & (s < 0.1), (s >= 0.1) & (s < 0.3), s >= 0.3]
scatter(tc, "target area in grid cells² (finest level, 4.26 km cells)", sclass,
        ["shrink < 0.03", "0.03 to 0.1", "0.1 to 0.3", "0.3 or more"], "fig2_error_vs_target.png", "shrink factor (n counties)", vline=1)

sb = [0, 0.01, 0.03, 0.1, 0.3, 1, 3, 100]; tb = [0, 1, 4, 16, 64, 1e9]
share = np.full((len(sb) - 1, len(tb) - 1), np.nan); cnt = np.zeros_like(share, int)
for i in range(len(sb) - 1):
    for j in range(len(tb) - 1):
        m = (s >= sb[i]) & (s < sb[i + 1]) & (tc >= tb[j]) & (tc < tb[j + 1]); cnt[i, j] = m.sum()
        if m.sum(): share[i, j] = 100 * (e[m] > 10).mean()
fig, ax = plt.subplots(figsize=(7.5, 4.6)); ax.grid(False)
im = ax.imshow(share, cmap="Blues", vmin=0, vmax=80, aspect="auto", origin="lower")
for i in range(share.shape[0]):
    for j in range(share.shape[1]):
        if cnt[i, j]:
            ax.text(j, i, f"{share[i, j]:.0f} %\nn={cnt[i, j]}", ha="center", va="center", fontsize=8.5,
                    color="white" if share[i, j] > 40 else INK)
ax.set_xticks(range(len(tb) - 1)); ax.set_xticklabels(["< 1", "1 to 4", "4 to 16", "16 to 64", "64 +"])
ax.set_yticks(range(len(sb) - 1)); ax.set_yticklabels(["< 0.01", "0.01 to 0.03", "0.03 to 0.1", "0.1 to 0.3", "0.3 to 1", "1 to 3", "3 +"])
ax.set_xlabel("target area in grid cells²"); ax.set_ylabel("shrink factor (target / original)")
ax.set_title("share of counties with error above 10 %", loc="left", fontsize=10)
for sp in ax.spines.values(): sp.set_visible(False)
fig.tight_layout(); fig.savefig(f"{out}/fig3_share_over_10pct.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.5, 5.2)); ax.axis("off")
gs = gpd.GeoSeries(list(o), crs=g.crs)
bad = e > 10
gs[~bad].plot(ax=ax, color="#d5dae0", edgecolor="white", linewidth=0.1)
gs[bad].plot(ax=ax, color=RED, edgecolor=RED, linewidth=0.3)
ax.set_title(f"cartogram output: {int(bad.sum())} counties with error above 10 % (red); 61 of them in TX, NE, MT, ND and VA", loc="left", fontsize=10)
fig.tight_layout(); fig.savefig(f"{out}/fig4_where.png", dpi=150); plt.close(fig)
np.savez(f"{out}/counties.npz", A0=A0, T=T, out=a, cell2=cell2)
print("over 10%:", int(bad.sum()), "states of failing counties:", dict(zip(*np.unique(g.loc[bad, "State Abbreviation"], return_counts=True))))
