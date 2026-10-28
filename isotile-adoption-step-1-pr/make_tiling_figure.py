"""Tilings of the region (-1, -1, 1, 1), margin 0.1, before and after, in one figure.

    python make_tiling_figure.py dump <label> <output.pkl>      # run once with each code version on PYTHONPATH
    python make_tiling_figure.py draw before.pkl after.pkl <output.png>

Tilings: hexagon, a skewed right triangle, an elongated quadrilateral, and the presets wavy_square and flowers (curved
edges). The red rectangle is the region with its margin; tiles are colored by index in the list of tiles.
"""

from __future__ import annotations

import pickle
import sys
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.collections import PolyCollection
from shapely.geometry import Polygon

CASES = [
    ("hexagon", lambda m: m.HexagonTiling(), {"tile_size": 0.16}),
    ("right triangle (aspect 0.3)", lambda m: m.TriangleTiling.right(0.3), {"tile_size": 0.25}),
    ("scalene triangle, region at (3, 3)", lambda m: m.TriangleTiling(Polygon([(0, 0), (3, 0), (1, 1.5)])), {"tile_size": 0.25, "shift": 3.0}),
    ("elongated quadrilateral", lambda m: m.QuadrilateralTiling.trapezoid(0.2, 0.6), {"tile_size": 0.25}),
    ("wavy_square (curved)", lambda m: m.IsohedralTiling.from_preset("wavy_square"), {"n_tiles": 100}),
    ("flowers (curved)", lambda m: m.IsohedralTiling.from_preset("flowers"), {"n_tiles": 100}),
]


def dump(label: str, out: str) -> None:
    from carto_flow.symbol_cartogram import tiling as m

    result = {}
    for name, factory, kw in CASES:
        shift = kw.get("shift", 0.0)
        bounds = (-1 + shift, -1 + shift, 1 + shift, 1 + shift)
        args = {k: v for k, v in kw.items() if k != "shift"}
        r = factory(m).generate(bounds=bounds, margin=0.1, compute_adjacency=False, **args)
        result[name] = {"bounds": bounds, "wkb": [shapely.to_wkb(p) for p in r.polygons]}
    pickle.dump(result, open(out, "wb"))


def draw(before: str, after: str, out: str) -> None:
    b, a = pickle.load(open(before, "rb")), pickle.load(open(after, "rb"))
    fig, axes = plt.subplots(len(CASES), 2, figsize=(8, 3.6 * len(CASES)))
    for row, (name, _, _) in enumerate(CASES):
        for col, (label, data) in enumerate((("before", b), ("after", a))):
            ax = axes[row, col]
            polys = [shapely.from_wkb(w) for w in data[name]["wkb"]]
            colors = plt.get_cmap("tab20")(np.arange(len(polys)) % 20)
            ax.add_collection(
                PolyCollection([np.array(p.exterior.coords) for p in polys], facecolors=colors, edgecolors="white", linewidths=0.4, alpha=0.9)
            )
            x0, y0, x1, y1 = data[name]["bounds"]
            w, h = x1 - x0, y1 - y0
            ax.plot([x0 - 0.1 * w, x1 + 0.1 * w, x1 + 0.1 * w, x0 - 0.1 * w, x0 - 0.1 * w], [y0 - 0.1 * h, y0 - 0.1 * h, y1 + 0.1 * h, y1 + 0.1 * h, y0 - 0.1 * h], color="red", lw=1.2)
            ax.set_xlim(x0 - 0.6, x1 + 0.6)
            ax.set_ylim(y0 - 0.6, y1 + 0.6)
            ax.set_aspect("equal")
            ax.axis("off")
            ax.set_title(f"{name}, {label}: {len(polys)} tiles", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=100)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    if sys.argv[1] == "dump":
        dump(sys.argv[2], sys.argv[3])
    else:
        draw(*sys.argv[2:5])
