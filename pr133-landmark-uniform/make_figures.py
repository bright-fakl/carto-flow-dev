"""Figures and table of the uniform landmarks (PR 133): Cartogram.get_landmarks(uniform=True) on the states with dots.

    NUMBA_NUM_THREADS=8 uv run python make_figures.py

Writes fig_map.png, fig_profile.png and data/tables.md next to itself.
"""
import json
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

import carto_flow.flow_cartogram as flow
import carto_flow.proportional_cartogram as prop
from carto_flow import data

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
BLUE, ORANGE, GRAY, INK, GRID = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b", "#dcdbd6"
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
EDGES = np.array([0, 0.01, 0.02, 0.04, 0.06, 0.1, 0.2, 0.4, 0.6])
g = data.load_us_census(population=True, poverty=True)
col = "Below Poverty Level"


def band_z(geoms, P, owner, frac=0.06):
    obs = exp = var = 0.0
    for r in range(len(geoms)):
        sel = owner == r
        if sel.sum() < 8:
            continue
        poly = geoms[r].buffer(0)
        inner = poly.buffer(-frac * np.sqrt(poly.area))
        p = 1 - inner.area / poly.area
        obs += (~shapely.contains(inner, shapely.points(P[sel]))).sum()
        exp += sel.sum() * p
        var += sel.sum() * p * (1 - p)
    return (obs - exp) / np.sqrt(var)


def profile(geoms, P, owner):
    obs = np.zeros(len(EDGES) - 1)
    exp = np.zeros(len(EDGES) - 1)
    for r in np.unique(owner):
        poly = geoms[r].buffer(0)
        sc = np.sqrt(poly.area)
        sel = owner == r
        pts = shapely.points(P[sel])
        d = shapely.distance(pts, poly.boundary) / sc
        obs += np.histogram(d[shapely.contains(poly, pts)], EDGES)[0]
        A = np.array([poly.buffer(-e * sc).area if e > 0 else poly.area for e in EDGES])
        exp += sel.sum() * (A[:-1] - A[1:]) / poly.area
    return obs / exp


rows, prof, maps = [], {"original": [], "carried": [], "uniform": []}, None
for seed in range(8):
    d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
    owner = np.array([list(g.index).index(o) for o in d["original_index"]])
    c = flow.create_flow_cartogram(g, "Population", landmarks=gpd.GeoSeries(list(d.geometry), crs=g.crs), options=flow.MorphOptions(area_scale=1e-6, show_progress=False))
    geoms = list(c.get_geometry())
    P0 = shapely.get_coordinates(np.asarray(d.geometry, dtype=object))
    P = shapely.get_coordinates(np.asarray(c.get_landmarks(), dtype=object))
    Q = shapely.get_coordinates(np.asarray(c.get_landmarks(uniform=True), dtype=object))
    sc = np.array([np.sqrt(geoms[o].area) for o in owner])
    s = np.linalg.norm(Q - P, axis=1) / sc
    rows.append({"seed": seed, "original": round(band_z(list(g.geometry), P0, owner), 2), "carried": round(band_z(geoms, P, owner), 2), "uniform": round(band_z(geoms, Q, owner), 2),
                 "shift_median": round(float(np.median(s)), 4), "shift_p95": round(float(np.percentile(s, 95)), 4)})
    prof["original"].append(profile(list(g.geometry), P0, owner))
    prof["carried"].append(profile(geoms, P, owner))
    prof["uniform"].append(profile(geoms, Q, owner))
    print(rows[-1], flush=True)
    if seed == 7:
        maps = (owner, P0, P, Q, geoms, c)
mean = {k: round(float(np.mean([r[k] for r in rows])), 4 if k.startswith("shift") else 2) for k in ("original", "carried", "uniform", "shift_median", "shift_p95")}
(HERE / "data" / "results.json").write_text(json.dumps({"rows": rows, "mean": mean, "profile": {k: np.mean(v, axis=0).round(3).tolist() for k, v in prof.items()}}))

# table
lines = ["| seed | original map | carried by the flow | get_landmarks(uniform=True) | shift: median / 95th pct (x sqrt(area)) |", "|---|---|---|---|---|"]
lines += [f"| {r['seed']} | {r['original']} | {r['carried']} | {r['uniform']} | {r['shift_median']} / {r['shift_p95']} |" for r in rows]
lines.append(f"| mean | {mean['original']} | {mean['carried']} | {mean['uniform']} | {mean['shift_median']} / {mean['shift_p95']} |")
lh = " | ".join(f"{a:g}-{b:g}" for a, b in zip(EDGES[:-1], EDGES[1:]))
lines += ["", f"| dots (observed / expected, mean over 8 seeds) | {lh} |", "|---|" + "---|" * (len(EDGES) - 1)]
lines += [f"| {k} | " + " | ".join(f"{x:.2f}" for x in np.mean(v, axis=0)) + " |" for k, v in prof.items()]
(HERE / "data" / "tables.md").write_text("\n".join(lines) + "\n")

# figures
owner, P0, P, Q, geoms, c = maps
names = list(g["State Name"])
pick = [names.index("California"), names.index("Nevada")]
fig, axes = plt.subplots(1, 3, figsize=(13, 5))
orig = list(g.geometry)
for ax, polys, pts, title in ((axes[0], orig, P0, "Original map"), (axes[1], geoms, P, "Carried by the flow"), (axes[2], geoms, Q, "get_landmarks(uniform=True)")):
    for i in pick:
        poly = polys[i]
        inner = poly.buffer(-0.06 * np.sqrt(poly.area))
        for pp in getattr(poly, "geoms", [poly]):
            ax.fill(*pp.exterior.xy, color="#f1f0ec", zorder=1)
        for pp in getattr(inner, "geoms", [inner]):
            if not pp.is_empty:
                ax.fill(*pp.exterior.xy, color="white", zorder=2)
        for pp in getattr(poly, "geoms", [poly]):
            ax.plot(*pp.exterior.xy, color=GRAY, linewidth=1, zorder=3)
        sel = owner == i
        ax.scatter(pts[sel, 0], pts[sel, 1], s=7, color=BLUE if i == pick[0] else ORANGE, zorder=4)
    b = shapely.union_all([polys[i] for i in pick]).bounds
    ax.set_xlim(b[0], b[2]); ax.set_ylim(b[1], b[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    z = band_z(polys, pts, owner)
    ax.set_title(f"{title}\nborder band z = {z:.1f} (49 states)", fontsize=10)
fig.savefig(HERE / "fig_map.png", dpi=150, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 3.8))
x = np.arange(len(EDGES) - 1)
for k, col_, ls in (("original", GRAY, "--"), ("carried", ORANGE, "-"), ("uniform", BLUE, "-")):
    ax.plot(x, np.mean(prof[k], axis=0), color=col_, linestyle=ls, marker="o", markersize=4, linewidth=1.8, label={"original": "original map", "carried": "carried by the flow", "uniform": "uniform=True"}[k])
ax.axhline(1, color=INK, linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels([f"{a:g}-{b:g}" for a, b in zip(EDGES[:-1], EDGES[1:])], rotation=30, ha="right", fontsize=8)
ax.set_xlabel("distance to the border of the region (x sqrt(area))")
ax.set_ylabel("observed / expected dots (8 seeds)")
ax.legend(frameon=False)
fig.savefig(HERE / "fig_profile.png", dpi=150, bbox_inches="tight")
plt.close(fig)
