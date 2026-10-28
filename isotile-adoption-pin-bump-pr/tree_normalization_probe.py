"""states grid, preset tree, offset (0.9, 0.1), straight tile set (158 tiles, new isotile): origin_weight scaled by
203.67 / 212.35 (the ratio of the largest squared region-to-tile distances of the two tile sets) emulates the change of the
origin cost normalization that the 17 extra tiles cause. Prints the mean distance for several scale factors."""
import functools
import warnings

import isotile
import numpy as np

warnings.simplefilter("ignore")
orig = isotile.IsohedralTiling.fill_region
isotile.IsohedralTiling.fill_region = functools.wraps(orig)(lambda self, *a, **kw: orig(self, *a, outline="straight", **kw))
from carto_flow.data import load_us_census
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
from carto_flow.symbol_cartogram.tiling import IsohedralTiling

gdf = load_us_census(population=True).reset_index(drop=True)
cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
for f in (1.0, 203.67 / 212.35, 0.9, 0.8, 1.1):
    t = IsohedralTiling.from_preset("tree").with_offset((0.9, 0.1))
    res = create_layout(gdf, layout=GridBasedLayout(tiling=t, origin_weight=0.5 * f), show_progress=False)
    tr = res.tiling_result
    d = np.hypot(*(tr.centers[np.asarray(res.assignments)] - cent).T) / tr.tile_size
    print(f"origin_weight factor {f:.4f}: tiles {tr.n_tiles}, mean {d.mean():.3f}")
