"""Neighbor preservation of the states grid layout, preset tree, offset (0.9, 0.1), straight against curved tile set:
fraction of touching state pairs whose tiles share an edge, share an edge or a vertex, and the states with no touching
state on an adjacent tile (islands). python tree_contiguity.py <straight|curved>"""
import functools
import sys
import warnings

import isotile
import numpy as np

warnings.simplefilter("ignore")
if sys.argv[1] == "straight":
    orig = isotile.IsohedralTiling.fill_region
    isotile.IsohedralTiling.fill_region = functools.wraps(orig)(lambda self, *a, **kw: orig(self, *a, outline="straight", **kw))
from carto_flow.data import load_us_census
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
from carto_flow.symbol_cartogram.tiling import IsohedralTiling

gdf = load_us_census(population=True).reset_index(drop=True)
n = len(gdf)
geo = gdf.geometry
pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if geo.iloc[i].intersection(geo.iloc[j]).length > 0]
for off in ((0.9, 0.1), (0.0, 0.0)):
    res = create_layout(gdf, layout=GridBasedLayout(tiling=IsohedralTiling.from_preset("tree").with_offset(off)), show_progress=False)
    tr = res.tiling_result
    a = np.asarray(res.assignments)
    edge = tr.adjacency.tocsr()
    vert = (tr.adjacency + tr.vertex_adjacency).tocsr()
    e = sum(bool(edge[a[i], a[j]]) for i, j in pairs)
    v = sum(bool(vert[a[i], a[j]]) for i, j in pairs)
    deg = np.zeros(n, int)
    for i, j in pairs:
        if edge[a[i], a[j]]:
            deg[i] += 1
            deg[j] += 1
    has_nb = np.zeros(n, int)
    for i, j in pairs:
        has_nb[i] += 1
        has_nb[j] += 1
    isolated = int(((deg == 0) & (has_nb > 0)).sum())
    print(f"{sys.argv[1]} offset {off}: {len(pairs)} touching pairs, edge-adjacent tiles {e}, edge or vertex {v}, states with no touching state on an edge-adjacent tile {isolated}, tiles {tr.n_tiles}")
