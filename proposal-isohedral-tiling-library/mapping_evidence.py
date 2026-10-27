"""Do isohedral types reproduce carto-flow's square, hexagon, triangle and quadrilateral tilings?

For each convenience class and constructor, carto-flow's ``generate`` output is compared with the tiling of the
prototype's named constructor (``isotile_proto.families``): tile polygons, adjacency matrices, tile transforms and
coverage of the region. Then random triangles and simple quadrilaterals test that every shape is expressible.

Run: ``PYTHONPATH=/home/fakl/isotile uv run --project /home/fakl/carto-flow python mapping_evidence.py``
"""

from __future__ import annotations

import warnings

import numpy as np
import shapely
from carto_flow.symbol_cartogram.tiling import (
    HexagonTiling,
    QuadrilateralTiling,
    SquareTiling,
    TriangleTiling,
)
from isotile_proto import IsohedralTiling, geometric_adjacency, hexagon, quadrilateral, square, triangle
from scipy.sparse import csr_array
from scipy.spatial import cKDTree
from shapely import STRtree
from shapely.geometry import Polygon, box


def center_rule(tile_size: float):
    """Triangle, quadrilateral: centroid within one tile size of the padded region (carto-flow's filter).

    All rules take ``e``: the region is widened by ``e`` (negative: shrunk) to bracket floating-point ties.
    """
    lo, hi = REGION[0] - tile_size, REGION[2] + tile_size
    return lambda c, e: np.all((c >= lo - e) & (c <= hi + e), axis=1)


def square_rule(tile_size: float):
    """Square: lower-left corner in [min, max) of the padded region."""
    return lambda c, e: np.all((c - tile_size / 2 >= REGION[0] - e) & (c - tile_size / 2 < REGION[2] + e), axis=1)


def hexagon_rule(size: float):
    """Hexagon: center in [min, max + step) of the padded region (steps sqrt(3) * size and 1.5 * size)."""
    step = np.array([np.sqrt(3) * size, 1.5 * size])
    return lambda c, e: np.all((c >= REGION[0] - e) & (c < REGION[2] + step + e), axis=1)


BOUNDS = (-1.0, -1.0, 1.0, 1.0)
MARGIN = 0.1
REGION = (-1.2, -1.2, 1.2, 1.2)  # BOUNDS expanded by MARGIN, as in carto-flow's _apply_margin


def rotation_flip(m: np.ndarray) -> tuple[float, bool]:
    """Rotation (degrees, mod 360) and flip of a 2x3 affine map, with carto-flow's convention."""
    det = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
    flipped = bool(det < 0)
    ang = np.degrees(np.arctan2(-m[1, 0], -m[0, 0])) if flipped else np.degrees(np.arctan2(m[1, 0], m[0, 0]))
    return float(ang % 360.0), flipped


def vertex_gap(a: np.ndarray, b: np.ndarray) -> float:
    d = np.linalg.norm(a[:, None] - b[None], axis=2)
    return float(max(d.min(axis=1).max(), d.min(axis=0).max()))


def coverage(polys: list[Polygon], n: int = 40000) -> tuple[float, float]:
    """Fraction of random points of the region in at least one / in more than one polygon."""
    pts = shapely.points(np.random.default_rng(5).uniform(REGION[0], REGION[2], (n, 2)))
    hit = STRtree(polys).query(pts, predicate="within")
    count = np.bincount(hit[0], minlength=n)
    return float((count >= 1).mean()), float((count >= 2).mean())


def compare(name: str, carto, library: IsohedralTiling, tile_size: float, area_factor: float = 1.0, rule=None) -> dict:
    res = carto.generate(bounds=BOUNDS, tile_size=tile_size, margin=MARGIN)
    cp = res.polygons
    c_cent = np.array([[p.centroid.x, p.centroid.y] for p in cp])
    tiles = library.cover((
        REGION[0] - 2 * tile_size,
        REGION[1] - 2 * tile_size,
        REGION[2] + 2 * tile_size,
        REGION[3] + 2 * tile_size,
    ))
    lib_poly = [Polygon(v) for v in tiles.vertices()]
    l_cent = tiles.centroids
    tol = 1e-6 * tile_size
    dist, j = cKDTree(l_cent).query(c_cent)
    matched = dist < tol  # carto tile i <-> library tile j[i]
    # polygon agreement of matched pairs: largest distance from a vertex of one polygon to the vertex set of the
    # other, relative to the tile size (overlay operations are avoided: GEOS 3.13 returns wrong areas for polygons
    # whose shared vertices differ by 1e-17)
    sym = [
        vertex_gap(np.array(cp[i].exterior.coords[:-1]), tiles.vertices()[j[i]]) / tile_size
        for i in np.flatnonzero(matched)
    ]
    # adjacency over the matched tiles
    ci = np.flatnonzero(matched)
    li = j[ci]
    e_lib = tiles.adjacency("edge")[li][:, li]
    v_lib = tiles.adjacency("vertex-only")[li][:, li]
    e_car = np.asarray(res.adjacency)[np.ix_(ci, ci)]
    v_car = np.asarray(res.vertex_adjacency)[np.ix_(ci, ci)]
    d_edge = int((e_lib.toarray() != e_car).sum() // 2)
    d_vert = int((v_lib.toarray() != v_car).sum() // 2)
    # rotation / flip of matched tiles
    rot_bad = 0
    for i, jj in zip(ci, li, strict=True):
        r_lib, f_lib = rotation_flip(tiles.transforms[jj])
        t = res.transforms[i]
        if abs(((r_lib - t.rotation) + 180) % 360 - 180) > 1e-6 or f_lib != t.flipped:
            rot_bad += 1
    # tiles of the library meeting the region that carto-flow lacks
    eps = 1e-6 * tile_size  # tiles that only touch the region boundary are not needed
    region = box(REGION[0] + eps, REGION[1] + eps, REGION[2] - eps, REGION[3] - eps)
    needed = np.array([p.intersects(region) for p in lib_poly])
    carto_set = set(li.tolist())
    missing = [k for k in np.flatnonzero(needed) if k not in carto_set]
    covered_carto = coverage(cp)
    covered_lib = coverage([lib_poly[k] for k in np.flatnonzero(needed)])
    area_ratio = lib_poly[0].area / (tile_size**2 * area_factor)
    # does a selection rule on the library's centroids (carto-flow's own rule, written on centers) give carto's set?
    rule_exact = None
    if rule is not None:
        inner, outer = (set(np.flatnonzero(rule(l_cent, e)).tolist()) for e in (-1e-9, 1e-9))
        rule_exact = inner <= set(li.tolist()) <= outer and bool(matched.all())
    return {
        "case": name,
        "rule exact": rule_exact,
        "carto": len(cp),
        "lib needed": int(needed.sum()),
        "matched": int(matched.sum()),
        "carto only": int((~matched).sum()),
        "region tiles missing in carto": len(missing),
        "max vertex gap": max(sym) if sym else float("nan"),
        "edge adj diff": d_edge,
        "vertex adj diff": d_vert,
        "rot/flip diff": rot_bad,
        "area ratio": area_ratio,
        "carto covered": covered_carto[0],
        "carto overlap": covered_carto[1],
        "lib covered": covered_lib[0],
        "lib overlap": covered_lib[1],
        "type": library.type.number,
    }


def random_triangle(rng) -> np.ndarray:
    while True:
        p = rng.uniform(-1, 1, (3, 2))
        a = 0.5 * abs(np.cross(p[1] - p[0], p[2] - p[0]))
        if a > 0.02:
            return p


def random_simple_quad(rng) -> np.ndarray:
    while True:
        p = rng.uniform(-1, 1, (4, 2))
        poly = Polygon(p)
        if poly.is_valid and poly.area > 0.05:
            return p


def scaled(poly: Polygon, area: float) -> Polygon:
    from shapely import affinity

    return affinity.scale(poly, np.sqrt(area / poly.area), np.sqrt(area / poly.area), origin=poly.centroid)


def isohedral_all_types() -> None:
    """carto-flow's IsohedralTiling.generate against the library's fill, same type, defaults, straight edges."""
    from carto_flow.symbol_cartogram.tiling import IsohedralTiling as CartoIH
    from isotile_proto import tiling_types

    n_tiles, bad = 100, []
    stats = {"types": 0, "same order": 0, "same count": 0, "adjacency equal": 0}
    for number in tiling_types():
        carto = CartoIH(number)
        res = carto.generate(bounds=BOUNDS, n_tiles=n_tiles, margin=MARGIN)
        lib = IsohedralTiling(number)
        width = height = 2 * (1 + 2 * MARGIN)
        tile_size = np.sqrt(width * height / n_tiles)
        sf = tile_size / np.sqrt(lib.area)
        lat_max = max(np.abs(lib.t1).max(), np.abs(lib.t2).max(), 1e-6)
        pad, eps = 0.5 * lat_max, 0.01 * lat_max
        hw, hh = width / 2 / sf, height / 2 / sf
        native = (-hw - pad - eps, -hh - pad - 0.7 * eps, hw + pad + eps, hh + pad + 0.7 * eps)
        tiles = IsohedralTiling(number).fill(native)
        verts = tiles.vertices() * sf
        stats["types"] += 1
        cent = np.array([[p.centroid.x, p.centroid.y] for p in res.polygons])
        lib_cent = np.array([Polygon(v).centroid.coords[0] for v in verts])
        same_count = len(cent) == len(lib_cent)
        stats["same count"] += same_count
        if not same_count:
            bad.append(number)
            continue
        stats["same order"] += bool(np.abs(cent - lib_cent).max() < 1e-9 * tile_size)
        e, v = geometric_adjacency(list(verts), tol=1e-6 * tile_size)
        stats["adjacency equal"] += bool(
            (e != csr_array(np.asarray(res.adjacency))).nnz == 0
            and (v != csr_array(np.asarray(res.vertex_adjacency))).nnz == 0
        )
    print()
    print(
        f"IsohedralTiling.generate vs the library's fill with carto-flow's native bounds, all {stats['types']} types, "
        f"defaults, n_tiles {n_tiles}:"
    )
    print(
        f"  same tile count {stats['same count']}, same tiles in the same order {stats['same order']}, "
        f"edge and vertex-only adjacency equal {stats['adjacency equal']}; count mismatches: {bad}"
    )


def main() -> None:
    rows = []
    # square
    s = 0.2
    carto = SquareTiling()
    c0 = carto.generate(bounds=BOUNDS, tile_size=s, margin=MARGIN).polygons[0].centroid
    rows.append(compare("SquareTiling()", carto, square(s, (c0.x, c0.y)), s, rule=square_rule(s)))
    # hexagon, pointy and flat
    s = 0.12
    for pt in (True, False):
        carto = HexagonTiling(pointy_top=pt)
        c0 = carto.generate(bounds=BOUNDS, tile_size=s, margin=MARGIN).polygons[0].centroid
        # carto-flow's generate ignores pointy_top (see the last lines of the output), so both flags are compared
        # with the library's pointy-top tiling
        rows.append(
            compare(
                f"HexagonTiling(pointy_top={pt}) vs hexagon(True)",
                carto,
                hexagon(True, s, (c0.x, c0.y)),
                s,
                area_factor=3 * np.sqrt(3) / 2,
                rule=hexagon_rule(s),
            )
        )
    # triangles and quadrilaterals: the library prototile is carto-flow's canonical tile at the generated size
    cases: list[tuple[str, object]] = [
        ("TriangleTiling.equilateral()", TriangleTiling.equilateral()),
        ("TriangleTiling.right_isosceles()", TriangleTiling.right_isosceles()),
        ("TriangleTiling.right(2.0)", TriangleTiling.right(2.0)),
        ("TriangleTiling.right(0.3)", TriangleTiling.right(0.3)),
        ("TriangleTiling.isosceles(30)", TriangleTiling.isosceles(30.0)),
        ("TriangleTiling.isosceles(120)", TriangleTiling.isosceles(120.0)),
        (
            "TriangleTiling.from_polygon(clockwise scalene)",
            TriangleTiling.from_polygon(Polygon([(0, 0), (0.3, 1.0), (1.7, 0.2)])),
        ),
        ("QuadrilateralTiling.parallelogram(60, 1)", QuadrilateralTiling.parallelogram()),
        ("QuadrilateralTiling.parallelogram(75, 1.7)", QuadrilateralTiling.parallelogram(75.0, 1.7)),
        ("QuadrilateralTiling.rectangle(1)", QuadrilateralTiling.rectangle()),
        ("QuadrilateralTiling.rectangle(2.5)", QuadrilateralTiling.rectangle(2.5)),
        ("QuadrilateralTiling.rhombus(45)", QuadrilateralTiling.rhombus(45.0)),
        ("QuadrilateralTiling.trapezoid(0.5, 1)", QuadrilateralTiling.trapezoid()),
        ("QuadrilateralTiling.trapezoid(0.2, 0.6)", QuadrilateralTiling.trapezoid(0.2, 0.6)),
        (
            "QuadrilateralTiling.from_polygon(convex)",
            QuadrilateralTiling.from_polygon(Polygon([(0, 0), (1.2, 0.1), (1.0, 0.9), (0.1, 0.7)])),
        ),
        (
            "QuadrilateralTiling.from_polygon(non-convex)",
            QuadrilateralTiling.from_polygon(Polygon([(0, 0), (1.5, 0.0), (0.6, 0.5), (0.0, 1.2)])),
        ),
    ]
    s = 0.2
    for name, carto in cases:
        res = carto.generate(bounds=BOUNDS, tile_size=s, margin=MARGIN)
        verts = np.array(res.canonical_tile.exterior.coords[:-1])
        lib = triangle(verts) if len(verts) == 3 else quadrilateral(verts)
        rows.append(compare(name, carto, lib, s, rule=center_rule(s)))

    keys = [k for k in rows[0] if k != "case"]
    print(f"{'case':<48}" + "".join(f"{k:>14}" for k in keys))
    for r in rows:
        print(
            f"{r['case']:<48}" + "".join(f"{r[k]:>14.4g}" if isinstance(r[k], float) else f"{r[k]:>14}" for k in keys)
        )

    # expressibility: random triangles and simple quadrilaterals
    rng = np.random.default_rng(0)
    n = 300
    fails = {"triangle": 0, "quadrilateral": 0}
    worst = {"triangle": 0.0, "quadrilateral": 0.0}
    adj_bad = {"triangle": 0, "quadrilateral": 0}
    pmax = {"triangle": 0.0, "quadrilateral": 0.0}
    for kind, gen, make in (
        ("triangle", random_triangle, triangle),
        ("quadrilateral", random_simple_quad, quadrilateral),
    ):
        for _ in range(n):
            pts = gen(rng)
            try:
                t = make(pts)
            except ValueError:
                fails[kind] += 1
                continue
            worst[kind] = max(worst[kind], vertex_gap(t.vertices, pts) / np.sqrt(Polygon(pts).area))
            pmax[kind] = max(pmax[kind], float(np.abs(t.parameters).max()))
            ts = t.cover((-3, -3, 3, 3))
            e, v = geometric_adjacency(ts.vertices(), tol=1e-7)
            if (ts.adjacency("edge") != e).nnz or (ts.adjacency("vertex-only") != v).nnz:
                adj_bad[kind] += 1
    print()
    print(
        f"expressibility over {n} random shapes each (uniform vertices in [-1, 1]^2; quadrilaterals simple, convex or not):"
    )
    for kind in fails:
        print(
            f"  {kind}: construction failures {fails[kind]}, largest distance of a prototile vertex to the requested vertices (relative to sqrt(area)) {worst[kind]:.2e}, "
            f"largest |parameter| {pmax[kind]:.1f}, lattice vs geometric adjacency mismatches {adj_bad[kind]}"
        )
    # carto-flow against the library on random shapes
    m = 60
    print(
        f"\ncarto-flow against the library on {m} random triangles and {m} random simple quadrilaterals (tile_size 0.25):"
    )
    for kind, gen, cls, make in (
        ("triangle", random_triangle, TriangleTiling, triangle),
        ("quadrilateral", random_simple_quad, QuadrilateralTiling, quadrilateral),
    ):
        tot = {
            "rule": 0,
            "unmatched": 0,
            "edge": 0,
            "vertex": 0,
            "rot/flip": 0,
            "missing": 0,
            "gap": 0.0,
            "holes": 0,
            "big": 0,
            "worst": 0.0,
        }
        for _ in range(m):
            carto = cls.from_polygon(Polygon(gen(rng)))
            res = carto.generate(bounds=BOUNDS, tile_size=0.25, margin=MARGIN)
            r = compare(
                "random", carto, make(np.array(res.canonical_tile.exterior.coords[:-1])), 0.25, rule=center_rule(0.25)
            )
            tot["rule"] += bool(r["rule exact"])
            tot["unmatched"] += r["carto only"]
            tot["edge"] += r["edge adj diff"]
            tot["vertex"] += r["vertex adj diff"]
            tot["rot/flip"] += r["rot/flip diff"]
            tot["missing"] += r["region tiles missing in carto"]
            tot["gap"] = max(tot["gap"], r["max vertex gap"])
            tot["holes"] += r["carto covered"] < 1.0
            tot["big"] += r["carto covered"] < 0.99
            tot["worst"] = max(tot["worst"], 1.0 - r["carto covered"])
        print(
            f"  {kind}: shapes whose carto-flow tile set equals the library's cover plus the centroid rule {tot['rule']} of {m}; "
            f"carto tiles without library match {tot['unmatched']}, edge adjacency differences {tot['edge']}, "
            f"vertex-only differences {tot['vertex']}, rotation/flip differences {tot['rot/flip']}, "
            f"region tiles missing in carto {tot['missing']}, shapes with a sampled hole in the carto-flow tiling {tot['holes']} "
            f"(more than 1% of the region uncovered: {tot['big']}, worst uncovered fraction {tot['worst']:.2f}), "
            f"largest vertex gap {tot['gap']:.1e}"
        )
    isohedral_all_types()
    # self-intersecting quadrilateral with non-zero net area (a bow tie)
    bow = [(0, 0), (2, 1), (1, 0), (0, 3)]
    res = QuadrilateralTiling.from_polygon(Polygon(bow)).generate(bounds=BOUNDS, tile_size=0.3, margin=MARGIN)
    invalid = sum(not p.is_valid for p in res.polygons)
    print(
        f"  self-intersecting quadrilateral {bow}: carto-flow accepts it and returns {len(res.polygons)} tiles, "
        f"{invalid} of them invalid polygons"
    )
    try:
        quadrilateral(bow)
        print("  the library accepts it")
    except ValueError as e:
        print(f"  the library rejects it: {e}")
    # does HexagonTiling.generate read pointy_top?
    a = HexagonTiling(pointy_top=True).generate(bounds=BOUNDS, tile_size=0.12).polygons[0].bounds
    b = HexagonTiling(pointy_top=False).generate(bounds=BOUNDS, tile_size=0.12).polygons[0].bounds
    print(
        f"  HexagonTiling.generate first-tile bounds, pointy_top=True {np.round(a, 4).tolist()}, pointy_top=False {np.round(b, 4).tolist()}"
    )
    for pt in (True, False):
        v = hexagon(pt, 0.12).vertices
        print(f"  library hexagon(pointy_top={pt}): width {np.ptp(v[:, 0]):.4f}, height {np.ptp(v[:, 1]):.4f}")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main()
