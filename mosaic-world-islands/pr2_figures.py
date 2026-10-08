"""Before/after figures for the cross-component overwrite fix."""
from __future__ import annotations
import pickle, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd

HERE = Path(__file__).resolve().parent
B = pickle.load(open(HERE / "placements_before.pkl", "rb"))
A = pickle.load(open(HERE / "placements_after.pkl", "rb"))

TITLES = {
    ("world", 384, True): "world, 384 nominal / 460 actual tiles, morph=True",
    ("world", 384, False): "world, 384 nominal / 460 actual tiles, morph=False",
    ("world", 800, True): "world, 800 nominal / 848 actual tiles, morph=True",
}


def draw(ax, rec, title):
    geom = rec["geom"]; names = rec["names"]; want = rec["want"]; got = rec["got"]
    base = gpd.GeoSeries(geom)
    base.plot(ax=ax, color="#eef0f3", edgecolor="white", linewidth=0.25)
    tiles = gpd.GeoSeries([p for p, _ in rec["tiles"]])
    tiles.plot(ax=ax, color="#9fc0dd", edgecolor="white", linewidth=0.25)
    drop = [i for i in range(len(want)) if got[i] == 0]
    shrt = [i for i in range(len(want)) if 0 < got[i] < want[i]]
    if shrt:
        gpd.GeoSeries([geom[i] for i in shrt]).plot(ax=ax, color="#f6c453", edgecolor="#8a6d1f", linewidth=0.7)
    if drop:
        gpd.GeoSeries([geom[i] for i in drop]).plot(ax=ax, color="#d94a3d", edgecolor="#7a1f16", linewidth=0.9)
    for i in drop + shrt:
        c = geom[i].centroid
        ax.plot([c.x], [c.y], marker="o", markersize=4,
                color="#d94a3d" if i in drop else "#c99a1e", zorder=5)
        ax.annotate(f"{names[i]} {got[i]}/{want[i]}", (c.x, c.y), fontsize=6,
                    color="#7a1f16" if i in drop else "#6b5310",
                    xytext=(5, 4), textcoords="offset points", zorder=6)
    ax.set_title(f"{title}\n{len(drop)} region(s) with 0 tiles, {len(shrt)} short, "
                 f"{len(rec['tiles'])} of {int(want.sum())} tiles placed, {rec['elapsed']:.1f}s", fontsize=9)
    ax.set_axis_off()


for key in B:
    fig, axes = plt.subplots(2, 1, figsize=(15, 13))
    draw(axes[0], B[key], "BEFORE (overlapping component pools) - " + TITLES[key])
    draw(axes[1], A[key], "AFTER (disjoint component pools) - " + TITLES[key])
    fig.tight_layout()
    out = HERE / f"m2_{key[0]}_b{key[1]}_morph{int(key[2])}.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print("wrote", out)
