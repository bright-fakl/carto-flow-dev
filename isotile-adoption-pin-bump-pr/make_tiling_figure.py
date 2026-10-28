"""Tiles of fill_region((0, 0, 10, 6), n_tiles=100, margin=0.1) for four curved presets: straight outline (the former
selection) and curved outline (the new default). Tiles that only the curved outline selects are orange; the red rectangle
is the region with margin. Usage: python make_tiling_figure.py <output.png>"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as P

from carto_flow.symbol_cartogram.tiling import IsohedralTiling

names = ["puzzle_piece", "arrow_quad", "wavy_triangle", "flowers"]
fig, axes = plt.subplots(len(names), 2, figsize=(11, 3.4 * len(names)))
for row, name in enumerate(names):
    res = IsohedralTiling.from_preset(name).generate((0.0, 0.0, 10.0, 6.0), n_tiles=100, margin=0.1)
    iso = res.tile_set.tiling
    region = (-1.0, -0.6, 11.0, 6.6)
    straight = iso.cover(region, outline="straight")
    keys = {tuple(k) for k in np.column_stack([straight.cell, straight.aspect]).tolist()}
    for col, (title, ts) in enumerate((("straight outline (before)", straight), ("curved outline (default now)", res.tile_set))):
        ax = axes[row, col]
        polys = ts.polygons()
        k = [tuple(x) for x in np.column_stack([ts.cell, ts.aspect]).tolist()]
        colors = ["#9ecae1" if x in keys else "#fd8d3c" for x in k]
        ax.add_collection(PatchCollection([P(np.array(p.exterior.coords)) for p in polys], facecolors=colors, edgecolors="k", linewidths=0.4))
        ax.add_patch(plt.Rectangle(region[:2], region[2] - region[0], region[3] - region[1], fill=False, ec="red", lw=1.2))
        ax.set_xlim(-2.5, 12.5)
        ax.set_ylim(-2.0, 8.0)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"{name}, {title}: {len(ts)} tiles", fontsize=9)
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=100)
