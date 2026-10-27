"""Does isotile's ``cover`` lose precision far from the origin?

``cover`` clips each candidate tile against the region and compares the overlap area with 1e-9 times the tile area. The
areas are computed from absolute coordinates, so their rounding error grows with the square of the distance from the
origin. This script measures (a) holes in the tilings of 100 random triangles in a region 2 x 2 at tile_size 0.25,
centered at distance c from the origin, and (b) the tile count of a square tiling whose region boundary coincides with
tile edges (144 tiles expected), with ``isotile.tiling._overlap_area`` as it is and with a variant that computes the
areas relative to the region center (patched in this process only; nothing is written to the library).

Run: python cover_precision.py > cover_precision.txt
"""

from __future__ import annotations

import warnings

import isotile.tiling as T
import numpy as np
import shapely
from isotile import IsohedralTiling as IT
from shapely.geometry import Polygon

original = T._overlap_area


def recentered(polygons, bounds):
    c = np.array([(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2])
    return original(polygons - c, (bounds[0] - c[0], bounds[1] - c[1], bounds[2] - c[0], bounds[3] - c[1]))


def uncovered(polys, region, n=40000):
    pts = shapely.points(np.random.default_rng(5).uniform(region[:2], region[2:], (n, 2)))
    hit = shapely.STRtree(polys).query(pts, predicate="within")
    return 1.0 - len(np.unique(hit[0])) / n


def main() -> None:
    rng = np.random.default_rng(0)
    shapes = []
    while len(shapes) < 100:
        p = rng.uniform(-1, 1, (3, 2))
        if Polygon(p).area > 0.02:
            shapes.append(p)
    print("(a) 100 random triangles, region 2 x 2 at (c, c), tile_size 0.25: shapes with a sampled hole / largest uncovered fraction")
    for c in (0.0, 1e3, 1e5, 1e6):
        region = (c - 1, c - 1, c + 1, c + 1)
        cells = []
        for label, fn in (("as is", original), ("recentered", recentered)):
            T._overlap_area = fn
            holes, worst = 0, 0.0
            for pts in shapes:
                unit = pts - Polygon(pts).centroid.coords[0]
                unit /= np.sqrt(Polygon(unit).area)
                u = uncovered(IT.triangle(unit).fill_region(region, tile_size=0.25).polygons(), region)
                holes += u > 0
                worst = max(worst, u)
            cells.append(f"{label}: {holes} / {worst:.1e}")
        print(f"  c = {c:>9g}   " + "   ".join(cells))
    print("\n(b) square tiling, tile_size 0.2, region 2.4 x 2.4 (12 x 12 tiles, boundary on tile edges), tiles returned:")
    for c in (0.0, 1e3, 1e5, 1e6):
        region = (c - 1.2, c - 1.2, c + 1.2, c + 1.2)
        counts = []
        for fn in (original, recentered):
            T._overlap_area = fn
            counts.append(len(IT.square().fill_region(region, tile_size=0.2)))
        print(f"  c = {c:>9g}   as is {counts[0]}, recentered {counts[1]}")
    T._overlap_area = original


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
