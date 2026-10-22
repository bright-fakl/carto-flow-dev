"""Counties with validity="none" and "windows" (1 km input, auto ladder, n_iter 1000): where the invalid polygons are."""
import warnings, sys; warnings.filterwarnings("ignore")
import numpy as np, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
out = sys.argv[1]
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v)
res = {}
for mode in ("none", "windows"):
    w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False, validity=mode))
    o = np.array(w[-1].get_geometry(), dtype=object); res[mode] = (o, shapely.is_valid(o))
INK = "#1f2933"
fig, axs = plt.subplots(1, 2, figsize=(14, 4.8))
for ax, mode, title in zip(axs, ("none", "windows"), ("validity=\"none\"", "validity=\"windows\"")):
    o, val = res[mode]; ax.axis("off"); gs = gpd.GeoSeries(list(o), crs=g.crs)
    gs[val].plot(ax=ax, color="#d5dae0", edgecolor="white", linewidth=0.1)
    gs[~val].plot(ax=ax, color=INK, edgecolor=INK, linewidth=0.4)
    ax.set_title(f"{title}: {int((~val).sum())} invalid polygons (black)", loc="left", fontsize=10, color=INK)
fig.tight_layout(); fig.savefig(f"{out}/fig1_invalid_regions.png", dpi=150)
# zoom on a cluster of the baseline's invalid polygons: Virginia area
o0, v0 = res["none"]; o1, v1 = res["windows"]
bad = np.flatnonzero(~v0)
cx = np.array([shapely.centroid(o0[i]).x for i in bad]); cy = np.array([shapely.centroid(o0[i]).y for i in bad])
k = np.argmax([(np.hypot(cx - x, cy - y) < 150000).sum() for x, y in zip(cx, cy)])
x0, y0 = cx[k], cy[k]; r = 220000
fig, axs = plt.subplots(1, 2, figsize=(12, 5.5))
for ax, (o, val), title in zip(axs, (res["none"], res["windows"]), ("validity=\"none\"", "validity=\"windows\"")):
    gs = gpd.GeoSeries(list(o), crs=g.crs); ax.set_aspect("equal")
    gs[val].plot(ax=ax, color="#d5dae0", edgecolor="white", linewidth=0.3)
    gs[~val].plot(ax=ax, color=INK, edgecolor=INK, linewidth=0.5)
    ax.set_xlim(x0 - r, x0 + r); ax.set_ylim(y0 - r, y0 + r); ax.axis("off")
    ax.set_title(f"{title} (zoom on the densest cluster of invalid polygons)", loc="left", fontsize=9.5, color=INK)
fig.tight_layout(); fig.savefig(f"{out}/fig2_zoom.png", dpi=150)
print({m: int((~res[m][1]).sum()) for m in res})
