"""The preview window of the 'tree' preset (IH4): coverage by the old call and by fill_region.

Run: python tree_window.py > tree_window.txt
"""
import warnings

import shapely
from shapely.ops import unary_union

warnings.simplefilter("ignore")
from isotile import IsohedralTiling as IT  # noqa: E402
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old  # noqa: E402

W = shapely.box(-1, -0.3, 1, 0.3)
res = Old.from_preset("tree").generate(bounds=(-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25, compute_adjacency=False)
ts = IT.from_preset("tree").fill_region((-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25)
for label, polys in (("old generate", res.polygons), ("fill_region ", ts.polygons())):
    u = unary_union(polys)
    uncovered = W.difference(u).area / W.area
    overlap = sum(p.intersection(W).area for p in polys) / W.area - u.intersection(W).area / W.area
    print(f"{label}: {len(polys)} tiles; share of the window not covered {uncovered:.3e}; overlap beyond 1x {overlap:.3e}")
ts2 = IT.from_preset("tree").fill_region((-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25, outline="straight")
u = unary_union(ts2.polygons())
print(f"fill_region outline='straight': {len(ts2)} tiles; share of the window not covered {W.difference(u).area / W.area:.3e}")
