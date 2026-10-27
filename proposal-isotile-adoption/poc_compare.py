"""Proof of concept for the isotile adoption: the 19 named carto-flow tilings, old classes against isotile.

For each case, carto-flow's current ``generate`` (tactile-based classes) is compared with a tiling built from
``isotile.IsohedralTiling`` and a frame, which is the wrapper design of the page. Compared: tile polygons (as vertex
sets, per matched tile), edge and vertex-only adjacency over the matched tiles, tile counts, tile areas, rotation
and flip of the transforms. Then ``fill_region`` (the lattice anchored at the region center, one selection rule) is
checked for coverage, overlap and area, and the same is done for regions far from the origin.

Run (scratch venv with carto-flow and isotile installed, see the page):
    python poc_compare.py > poc_compare.txt
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import shapely
from carto_flow.symbol_cartogram.tiling import HexagonTiling, QuadrilateralTiling, SquareTiling, TriangleTiling
from isotile import IsohedralTiling as IT
from scipy.spatial import cKDTree
from shapely import STRtree
from shapely.geometry import Polygon, box

BOUNDS = (-1.0, -1.0, 1.0, 1.0)
MARGIN = 0.1
REGION = (-1.2, -1.2, 1.2, 1.2)  # BOUNDS with the margin, as in carto-flow's _apply_margin
HEX_AREA = 3.0 * math.sqrt(3.0) / 2.0  # area of the regular hexagon with circumradius 1


def rotation_flip(m: np.ndarray) -> tuple[float, bool]:
    """Rotation (degrees, mod 360) and flip of a 2x3 affine map with carto-flow's convention."""
    det = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
    flipped = bool(det < 0)
    ang = math.degrees(math.atan2(-m[1, 0], -m[0, 0]) if flipped else math.atan2(m[1, 0], m[0, 0]))
    return ang % 360.0, flipped


def vertex_gap(a: np.ndarray, b: np.ndarray) -> float:
    """Largest distance from a vertex of one polygon to the vertex set of the other (symmetric)."""
    d = np.linalg.norm(a[:, None] - b[None], axis=2)
    return float(max(d.min(axis=1).max(), d.min(axis=0).max()))


def coverage(polys: list[Polygon], n: int = 40000) -> tuple[float, float]:
    """Fraction of random points of the region in at least one / in more than one polygon."""
    pts = shapely.points(np.random.default_rng(5).uniform(REGION[0], REGION[2], (n, 2)))
    hit = STRtree(polys).query(pts, predicate="within")
    count = np.bincount(hit[0], minlength=n)
    return float((count >= 1).mean()), float((count >= 2).mean())


# -- the wrapper design: an isotile tiling with a frame (scale, orientation, anchor) --------------------------


def with_anchor(t: IT, scale: float, anchor: tuple[float, float] | None = None) -> IT:
    """Scale the frame of ``t`` by ``scale`` about the origin and (optionally) move the native origin."""
    f = t.frame
    f[:, :2] *= scale
    f[:, 2] = f[:, 2] * scale if anchor is None else anchor
    return t.with_frame(f)


def new_square(s: float, anchor):
    return with_anchor(IT.square(), s, anchor)  # tile (0, 0) is [0, 1]^2: lower-left corner at the anchor


def new_hexagon(r: float, anchor, pointy_top: bool = True):
    return with_anchor(IT.hexagon(pointy_top), r, anchor)  # circumradius r, tile (0, 0) centered at the anchor


def new_polygon_tiling(unit_vertices: np.ndarray, s: float):
    make = IT.triangle if len(unit_vertices) == 3 else IT.quadrilateral
    return make(unit_vertices * s)  # the prototile is the requested polygon; its centroid is the origin


def compare(name: str, old, new: IT, s: float, area_unit: float) -> dict:
    res = old.generate(bounds=BOUNDS, tile_size=s, margin=MARGIN)
    cp = res.polygons
    c_old = np.array([[p.centroid.x, p.centroid.y] for p in cp])
    tiles = new.cover((REGION[0] - 2 * s, REGION[1] - 2 * s, REGION[2] + 2 * s, REGION[3] + 2 * s))
    verts = tiles.vertices()
    tol = 1e-6 * s
    dist, j = cKDTree(tiles.centroids).query(c_old)
    matched = dist < tol
    ci = np.flatnonzero(matched)
    li = j[ci]
    gap = max(vertex_gap(np.array(cp[i].exterior.coords[:-1]), verts[k]) for i, k in zip(ci, li, strict=True)) / s
    area_dev = max(abs(cp[i].area - Polygon(verts[k]).area) for i, k in zip(ci, li, strict=True)) / (s * s)
    area_ratio = Polygon(verts[0]).area / (s * s * area_unit)
    e_new = tiles.adjacency("edge")[li][:, li].toarray()
    v_new = tiles.adjacency("vertex-only")[li][:, li].toarray()
    e_old = np.asarray(res.adjacency)[np.ix_(ci, ci)]
    v_old = np.asarray(res.vertex_adjacency)[np.ix_(ci, ci)]
    rot_bad = 0
    for i, k in zip(ci, li, strict=True):
        r_new, f_new = rotation_flip(tiles.transforms[k])
        t = res.transforms[i]
        if abs(((r_new - t.rotation) + 180) % 360 - 180) > 1e-6 or f_new != t.flipped:
            rot_bad += 1
    # tiles of the new set that meet the padded region and that the old class does not have
    eps = 1e-6 * s
    region = box(REGION[0] + eps, REGION[1] + eps, REGION[2] - eps, REGION[3] - eps)
    meets = np.array([Polygon(v).intersection(region).area > 1e-9 * s * s for v in verts])
    in_old = np.zeros(len(verts), dtype=bool)
    in_old[li] = True
    old_meets = np.array([p.intersection(region).area > 1e-9 * s * s for p in cp])
    fr = new.fill_region(BOUNDS, tile_size=s * math.sqrt(area_unit), margin=MARGIN)
    fp = fr.polygons()
    cov_fr, ov_fr = coverage(fp)
    cov_old, ov_old = coverage(cp)
    return {
        "case": name,
        "old": len(cp),
        "old_meeting": int(old_meets.sum()),
        "cover": int(meets.sum()),
        "fill_region": len(fr),
        "matched": int(matched.sum()),
        "old_unmatched": int((~matched).sum()),
        "cover_missing_in_old": int((meets & ~in_old).sum()),
        "vertex_gap": gap,
        "area_dev": area_dev,
        "edge_diff": int((e_new != e_old).sum() // 2),
        "vertex_diff": int((v_new != v_old).sum() // 2),
        "rot_flip_diff": rot_bad,
        "area_ratio": area_ratio,
        "cov_old": cov_old,
        "cov_fill_region": cov_fr,
        "overlap_fill_region": ov_fr,
        "area_spread_fill_region": float(np.ptp([p.area for p in fp]) / np.mean([p.area for p in fp])),
    }


def main() -> None:
    rows = []
    s = 0.2
    old = SquareTiling()
    c0 = old.generate(bounds=BOUNDS, tile_size=s, margin=MARGIN).polygons[0].bounds[:2]
    rows.append(compare("SquareTiling()", old, new_square(s, c0), s, 1.0))
    # carto-flow's hexagon tiles are pointy-top for both values of the flag (the flag is read only by the symbol)
    r = 0.12
    for flag in (True, False):
        old = HexagonTiling(pointy_top=flag)
        c0 = old.generate(bounds=BOUNDS, tile_size=r, margin=MARGIN).polygons[0].centroid
        rows.append(
            compare(
                f"HexagonTiling(pointy_top={flag}) vs pointy-top",
                old,
                new_hexagon(r, (c0.x, c0.y), True),
                r,
                HEX_AREA,
            )
        )
    cases = [
        ("TriangleTiling.equilateral()", TriangleTiling.equilateral()),
        ("TriangleTiling.right_isosceles()", TriangleTiling.right_isosceles()),
        ("TriangleTiling.right(2.0)", TriangleTiling.right(2.0)),
        ("TriangleTiling.right(0.3)", TriangleTiling.right(0.3)),
        ("TriangleTiling.isosceles(30)", TriangleTiling.isosceles(30.0)),
        ("TriangleTiling.isosceles(120)", TriangleTiling.isosceles(120.0)),
        ("TriangleTiling.from_polygon(clockwise scalene)", TriangleTiling.from_polygon(Polygon([(0, 0), (0.3, 1.0), (1.7, 0.2)]))),
        ("QuadrilateralTiling.parallelogram(60, 1)", QuadrilateralTiling.parallelogram()),
        ("QuadrilateralTiling.parallelogram(75, 1.7)", QuadrilateralTiling.parallelogram(75.0, 1.7)),
        ("QuadrilateralTiling.rectangle(1)", QuadrilateralTiling.rectangle()),
        ("QuadrilateralTiling.rectangle(2.5)", QuadrilateralTiling.rectangle(2.5)),
        ("QuadrilateralTiling.rhombus(45)", QuadrilateralTiling.rhombus(45.0)),
        ("QuadrilateralTiling.trapezoid(0.5, 1)", QuadrilateralTiling.trapezoid()),
        ("QuadrilateralTiling.trapezoid(0.2, 0.6)", QuadrilateralTiling.trapezoid(0.2, 0.6)),
        ("QuadrilateralTiling.from_polygon(convex)", QuadrilateralTiling.from_polygon(Polygon([(0, 0), (1.2, 0.1), (1.0, 0.9), (0.1, 0.7)]))),
        ("QuadrilateralTiling.from_polygon(non-convex)", QuadrilateralTiling.from_polygon(Polygon([(0, 0), (1.5, 0.0), (0.6, 0.5), (0.0, 1.2)]))),
    ]
    for name, old in cases:
        unit = np.array(old.canonical_tile.exterior.coords[:-1])
        rows.append(compare(name, old, new_polygon_tiling(unit, s), s, 1.0))

    short = {
        "old": "old",
        "old_meeting": "old_in",
        "cover": "cover",
        "fill_region": "fill",
        "matched": "match",
        "old_unmatched": "unmatch",
        "cover_missing_in_old": "old_lack",
        "vertex_gap": "v_gap",
        "area_dev": "a_dev",
        "edge_diff": "e_diff",
        "vertex_diff": "v_diff",
        "rot_flip_diff": "rot_diff",
        "area_ratio": "a_ratio",
        "cov_old": "cov_old",
        "cov_fill_region": "cov_fill",
        "overlap_fill_region": "ov_fill",
        "area_spread_fill_region": "a_spread",
    }
    cols = [k for k in rows[0] if k != "case"]
    print("Columns: " + "; ".join(f"{v} = {k}" for k, v in short.items()))
    print("(old_in: old tiles that overlap the padded region; old_lack: tiles overlapping the region that the old class lacks;")
    print(" fill: tiles of isotile fill_region, lattice anchored at the region center; cov_*: sampled coverage of the region)\n")
    print(f"{'case':<46}" + "".join(f"{short[k]:>9}" for k in cols))
    for rw in rows:
        print(f"{rw['case']:<46}" + "".join(f"{rw[k]:>9.2g}" if isinstance(rw[k], float) else f"{rw[k]:>9}" for k in cols))
    n = len(rows)
    print(f"\n{n} cases: old tiles without isotile match {sum(rw['old_unmatched'] for rw in rows)}, "
          f"edge adjacency differences {sum(rw['edge_diff'] for rw in rows)}, "
          f"vertex-only differences {sum(rw['vertex_diff'] for rw in rows)}, "
          f"rotation or flip differences {sum(rw['rot_flip_diff'] for rw in rows)}, "
          f"largest vertex gap {max(rw['vertex_gap'] for rw in rows):.1e} of the tile size, "
          f"largest area deviation {max(rw['area_dev'] for rw in rows):.1e} of the tile size squared")
    print(f"old tiles that do not overlap the padded region: {sum(rw['old'] - rw['old_meeting'] for rw in rows)} of {sum(rw['old'] for rw in rows)}")
    print(f"tiles that overlap the region and that the old class lacks: {sum(rw['cover_missing_in_old'] for rw in rows)}")

    # regions away from the origin: tile counts of the old classes and of fill_region
    print("\nRegion far from the origin, tile_size 0.2, margin 0.1, region 2 x 2 centered at (c, c):")
    print(f"{'class':<44}" + "".join(f"{'c=' + str(c):>12}" for c in (0, 1, 3, 10, 1e3, 1e6)))
    for name, old in (
        ("SquareTiling", SquareTiling()),
        ("HexagonTiling (tile_size 0.12)", HexagonTiling()),
        ("TriangleTiling.equilateral", TriangleTiling.equilateral()),
        ("QuadrilateralTiling.parallelogram", QuadrilateralTiling.parallelogram()),
    ):
        ts = 0.12 if "Hexagon" in name else 0.2
        counts = []
        for c in (0, 1, 3, 10, 1e3, 1e6):
            b = (c - 1, c - 1, c + 1, c + 1)
            counts.append(old.generate(bounds=b, tile_size=ts, margin=MARGIN, compute_adjacency=False).n_tiles)
        print(f"{name + ' (old)':<44}" + "".join(f"{x:>12}" for x in counts))
    for name, t, ts in (
        ("square", IT.square(), 0.2),
        ("hexagon", IT.hexagon(), 0.12 * math.sqrt(HEX_AREA)),
        ("triangle", IT.triangle(), 0.2),
        ("quadrilateral", IT.quadrilateral(), 0.2),
    ):
        counts = []
        for c in (0, 1, 3, 10, 1e3, 1e6):
            b = (c - 1, c - 1, c + 1, c + 1)
            counts.append(len(t.fill_region(b, tile_size=ts, margin=MARGIN)))
        print(f"{name + ' (isotile fill_region)':<44}" + "".join(f"{x:>12}" for x in counts))

    # calibration pattern of the mosaic layout: the tiling of the bounds, then the tiling of the bounds expanded by 1.5
    # tile sizes on every side; are the tiles of the first also tiles of the second?
    print("\nLattice stability when the bounds are expanded symmetrically (mosaic calibration: trial build, then final build):")
    print(f"{'class':<44}{'tiles of the first build found in the second':>46}")
    for name, old, size, new in (
        ("SquareTiling", SquareTiling(), 0.2, IT.square()),
        ("HexagonTiling", HexagonTiling(), 0.12, IT.hexagon()),
        ("TriangleTiling.equilateral", TriangleTiling.equilateral(), 0.2, IT.triangle()),
        ("QuadrilateralTiling.parallelogram", QuadrilateralTiling.parallelogram(), 0.2, None),
    ):
        buf = 1.5 * size
        b1, b2 = (-1.0, -1.0, 1.0, 1.0), (-1.0 - buf, -1.0 - buf, 1.0 + buf, 1.0 + buf)
        r1 = old.generate(bounds=b1, tile_size=size, margin=0.0, compute_adjacency=False)
        r2 = old.generate(bounds=b2, tile_size=size, margin=0.0, compute_adjacency=False)
        c1 = np.array([[p.centroid.x, p.centroid.y] for p in r1.polygons])
        c2 = np.array([[p.centroid.x, p.centroid.y] for p in r2.polygons])
        found_old = int((cKDTree(c2).query(c1)[0] < 1e-6 * size).sum())
        line = f"{name + ' (current)':<44}{found_old:>20} of {len(c1)}"
        if new is not None:
            side = size * (math.sqrt(HEX_AREA) if "Hexagon" in name else 1.0)
            n1 = new.fill_region(b1, tile_size=side)
            n2 = new.fill_region(b2, tile_size=side)
            found_new = int((cKDTree(n2.centroids).query(n1.centroids)[0] < 1e-6 * size).sum())
            line += f"   isotile: {found_new:>4} of {len(n1)}"
        print(line)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
