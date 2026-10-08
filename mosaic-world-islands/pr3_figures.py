"""Before/after figures for min_one_tile_per_region."""
from __future__ import annotations
import pickle, sys
from pathlib import Path
import numpy as np, geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = Path(__file__).resolve().parent
P = pickle.load(open(HERE / "placements_pr3.pkl", "rb"))

def draw(ax, rec, title):
    geom, names, want, got = rec["geom"], rec["names"], rec["want"], rec["got"]
    gpd.GeoSeries(geom).plot(ax=ax, color="#eef0f3", edgecolor="white", linewidth=0.25)
    gpd.GeoSeries([p for p, _ in rec["tiles"]]).plot(ax=ax, color="#9fc0dd", edgecolor="white", linewidth=0.25)
    drop = [i for i in range(len(want)) if got[i] == 0]
    if drop:
        gpd.GeoSeries([geom[i] for i in drop]).plot(ax=ax, color="#d94a3d", edgecolor="#7a1f16", linewidth=0.9)
    for i in drop:
        c = geom[i].centroid
        ax.plot([c.x], [c.y], marker="o", markersize=4, color="#d94a3d", zorder=5)
        ax.annotate(names[i], (c.x, c.y), fontsize=6, color="#7a1f16",
                    xytext=(5, 4), textcoords="offset points", zorder=6)
    ax.set_title(f"{title}\n{len(drop)} region(s) with no symbol, "
                 f"{len(rec['tiles'])} of {int(want.sum())} tiles placed", fontsize=9)
    ax.set_axis_off()

for case, budget, morph in sorted({k[:3] for k in P}):
    fig, axes = plt.subplots(2, 1, figsize=(15, 13))
    lab = f"world, {budget} nominal / {int(P[(case,budget,morph,False)]['want'].sum())} actual tiles, morph={morph}"
    draw(axes[0], P[(case, budget, morph, False)], f"min_one_tile_per_region=False (default) - {lab}")
    draw(axes[1], P[(case, budget, morph, True)], f"min_one_tile_per_region=True - {lab}")
    fig.tight_layout()
    out = HERE / f"m1_{case}_b{budget}_morph{int(morph)}.png"
    fig.savefig(out, dpi=110); plt.close(fig); print("wrote", out)
