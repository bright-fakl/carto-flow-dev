"""Small checks behind the gap list (section 4): hit testing, rotation and offset of the preview, number of colors, frame
and mutability, repr.

Run: python editor_needs.py > editor_needs.txt
"""
import time
import warnings

import numpy as np
import shapely

warnings.simplefilter("ignore")
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT, get_type, tiling_types  # noqa: E402

W = (-1, -0.3, 1, 0.3)

# --- rotation and offset of the preview ---------------------------------------------------------------------------
t = IT.from_preset("cairo")
a = t.fill_region(W, n_tiles=100, margin=0.25)
r = t.rotated(30).fill_region(W, n_tiles=100, margin=0.25)
print(f"fill_region of the rotated tiling (30 degrees): {len(r)} tiles against {len(a)}; first tile centroid {r.centroids[0].round(3).tolist()}")
o1 = t.fill_region(W, n_tiles=100, margin=0.25, offset=(1.0, -2.0))
o2 = t.fill_region(W, n_tiles=100, margin=0.25, offset=(0.25, 0.5))
same = {tuple(c) for c in map(tuple, np.round(a.centroids, 9))} == {tuple(c) for c in map(tuple, np.round(o1.centroids, 9))}
print(f"offset by whole translations gives the same tile set: {same}; offset (0.25, 0.5) gives {len(o2)} tiles with {len({tuple(c) for c in np.round(o2.centroids, 6)} & {tuple(c) for c in np.round(a.centroids, 6)})} shared centroids")

# --- hit testing: which tile is under a point -----------------------------------------------------------------------
ts = IT.from_preset("puzzle_piece").fill_region(W, n_tiles=100, margin=0.25)
polys = ts.polygons()
t0 = time.perf_counter()
tree = shapely.STRtree(polys)
build = (time.perf_counter() - t0) * 1000
pts = shapely.points(np.random.default_rng(0).uniform([-1, -0.3], [1, 0.3], (1000, 2)))
t0 = time.perf_counter()
hit = tree.query(pts, predicate="within")
q = (time.perf_counter() - t0) * 1000
counts = np.bincount(hit[0], minlength=1000)
print(f"hit test with shapely STRtree on {len(polys)} curved tiles: build {build:.2f} ms, 1000 point queries {q:.2f} ms, points in exactly one tile {int((counts == 1).sum())} of 1000 (the others lie on a boundary)")
print("tile fields available for a highlight: cell", ts.cell[hit[1][0]].tolist(), "aspect", int(ts.aspect[hit[1][0]]), "color", int(ts.colors()[hit[1][0]]))

# --- number of colors of a type ------------------------------------------------------------------------------------
diff = 0
counts = []
for n in tiling_types():
    big = IT(n).fill_region((0, 0, 20, 20), n_tiles=2000)
    small = IT(n).fill_region(W, n_tiles=100, margin=0.25)
    cb, cs = len(set(big.colors().tolist())), len(set(small.colors().tolist()))
    counts.append(cb)
    diff += cb != cs
print(f"number of colors of the coloring: types with 1, 2, 3, 4, more colors: {[sum(1 for c in counts if c == k) for k in (1, 2, 3, 4)]}, {sum(1 for c in counts if c > 4)}")
print(f"types where the 100-tile preview shows fewer colors than the type has: {diff} of 81 (so a colormap normalized by the colors present changes with the window)")

# --- frame, mutability, repr -----------------------------------------------------------------------------------------
t = IT(41)
print("repr:", repr(t)[:80])
print("frame is the identity at construction:", np.array_equal(t.frame, np.eye(3)[:2]))
shared = IT(41)
view = shared
shared.parameters = [0.4, 0.4]
print("setting .parameters changes the object in place (every holder of the object sees it):", np.allclose(view.parameters, [0.4, 0.4]))
print("== TileSet.polygons, outlines point counts ==")
ts = IT.from_preset("puzzle_piece").fill_region(W, n_tiles=100, margin=0.25)
print("outlines shape", ts.outlines().shape, "; with n_points=20:", ts.outlines(n_points=20).shape)
