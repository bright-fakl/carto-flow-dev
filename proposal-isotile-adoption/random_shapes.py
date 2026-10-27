"""Do isotile tilings of random triangles and quadrilaterals cover a region without holes or overlaps?

The proposal page measured holes in carto-flow's TriangleTiling and QuadrilateralTiling (45 of 60 random triangles)
and left the library's ``cover`` untested on random shapes. Here 300 random triangles and 300 random simple
quadrilaterals (vertices uniform in [-1, 1]^2) are tiled with ``fill_region`` over a region of 2 x 2 at tile_size 0.25
and at a region 1e6 away from the origin; the sampled coverage (40,000 random points per shape) and overlap are
reported, and the old classes are run on the same shapes for comparison (60 shapes each, as before).

Run: python random_shapes.py > random_shapes.txt
"""

from __future__ import annotations

import warnings

import numpy as np
import shapely
from carto_flow.symbol_cartogram.tiling import QuadrilateralTiling, TriangleTiling
from isotile import IsohedralTiling as IT
from shapely import STRtree
from shapely.geometry import Polygon


def random_triangle(rng):
    while True:
        p = rng.uniform(-1, 1, (3, 2))
        if Polygon(p).area > 0.02:
            return p


def random_quad(rng):
    while True:
        p = rng.uniform(-1, 1, (4, 2))
        poly = Polygon(p)
        if poly.is_valid and poly.area > 0.05:
            return p


def sampled(polys, region, n=40000, seed=5):
    pts = shapely.points(np.random.default_rng(seed).uniform(region[:2], region[2:], (n, 2)))
    hit = STRtree(polys).query(pts, predicate="within")
    count = np.bincount(hit[0], minlength=n)
    return float((count >= 1).mean()), float((count >= 2).mean())


def main() -> None:
    rng = np.random.default_rng(0)
    size, offsets = 0.25, (0.0, 1e6)
    for kind, gen, make, cls in (
        ("triangle", random_triangle, IT.triangle, TriangleTiling),
        ("quadrilateral", random_quad, IT.quadrilateral, QuadrilateralTiling),
    ):
        shapes = [gen(rng) for _ in range(300)]
        for off in offsets:
            region = (off - 1.0, off - 1.0, off + 1.0, off + 1.0)
            worst_cov, worst_ov, holes, overlaps, counts = 1.0, 0.0, 0, 0, []
            for pts in shapes:
                unit = pts - Polygon(pts).centroid.coords[0]
                unit = unit / np.sqrt(Polygon(unit).area)
                tiles = make(unit).fill_region(region, tile_size=size)
                cov, ov = sampled(tiles.polygons(), region)
                worst_cov, worst_ov = min(worst_cov, cov), max(worst_ov, ov)
                holes += cov < 1.0
                overlaps += ov > 0.0
                counts.append(len(tiles))
            print(
                f"isotile {kind}, region centered at {off:g}: 300 shapes, shapes with a sampled hole {holes}, "
                f"with a sampled overlap {overlaps}, lowest covered fraction {worst_cov:.4f}, "
                f"largest overlap fraction {worst_ov:.4f}, tiles per region {min(counts)} to {max(counts)}"
            )
        for off in offsets:
            region = (off - 1.0, off - 1.0, off + 1.0, off + 1.0)
            holes, worst, empty, got = 0, 1.0, 0, 0
            for pts in shapes[:60]:
                res = cls(Polygon(pts)).generate(bounds=region, tile_size=size, margin=0.0, compute_adjacency=False)
                if res.n_tiles == 0:
                    empty += 1
                    worst = 0.0
                    continue
                got += 1
                cov, _ = sampled(res.polygons, region)
                holes += cov < 1.0
                worst = min(worst, cov)
            print(
                f"carto-flow {kind} (60 shapes), region centered at {off:g}: shapes with no tile at all {empty}, "
                f"of the others with a sampled hole {holes} of {got}, lowest covered fraction {worst:.4f}"
            )


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
