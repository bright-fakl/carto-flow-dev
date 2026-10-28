"""Probe of the states grid layout with an isotile preset at one offset.

    python tree_probe.py <out.pkl> [preset] [u v]
"""

import pickle
import sys
import warnings

import numpy as np
import shapely

warnings.simplefilter("ignore")
from carto_flow.data import load_us_census
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
from carto_flow.symbol_cartogram.tiling import IsohedralTiling

name = sys.argv[2] if len(sys.argv) > 2 else "tree"
off = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.9, 0.1)
gdf = load_us_census(population=True).reset_index(drop=True)
cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
res = create_layout(
    gdf, layout=GridBasedLayout(tiling=IsohedralTiling.from_preset(name).with_offset(off)), show_progress=False
)
tr = res.tiling_result
a = np.asarray(res.assignments)
d = np.hypot(*(tr.centers[a] - cent).T) / tr.tile_size
ts = getattr(tr, "tile_set", None)
out = {
    "n_tiles": tr.n_tiles,
    "tile_size": tr.tile_size,
    "mean": float(d.mean()),
    "dists": d,
    "centers": tr.centers,
    "assigned": a,
    "wkb": shapely.to_wkb(np.asarray(tr.polygons, dtype=object)),
    "cell": None if ts is None else np.column_stack([ts.cell, ts.aspect]),
}
print(name, off, "tiles", tr.n_tiles, "tile_size", tr.tile_size, "mean", out["mean"])
pickle.dump(out, open(sys.argv[1], "wb"))
