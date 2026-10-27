"""Do custom edge curves or carto-flow's tile validity repair change which tiles are neighbors?

For each of the 81 types, carto-flow's ``IsohedralTiling`` is built with random edge curves (every J, U and S
shape gets a random polyline; carto-flow enforces the U and S symmetry and spline-interpolates), tiles are
generated with ``generate`` and the adjacency matrices of the result are compared with the straight-edge lattice
table of the prototype. Tiles are identified by recording the ``(t1, t2, aspect)`` of tactile's fill and
replaying carto-flow's tile filter (invalid-polygon repair, area filter, center deduplication).

Three regimes: ``valid`` curves (the prototile polygon is simple, no repair happens), ``repair`` curves (the
prototile self-intersects and carto-flow applies ``make_valid`` and keeps the largest part) and ``extreme`` curves
(amplitude 1.5 times the edge length).
Two geometric tolerances: carto-flow's (0.01 * tile_size) and a tight one (1e-7 * tile_size).

Run: ``PYTHONPATH=prototype uv run --project /home/fakl/carto-flow python curve_adjacency.py``
"""

from __future__ import annotations

import math
import time
import warnings

import numpy as np
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as CartoIH
from isotile_proto import IsohedralTiling, geometric_adjacency, get_type, tiling_types
from shapely.geometry import Polygon
from shapely.validation import make_valid

BOUNDS = (-1.0, -1.0, 1.0, 1.0)
N_TILES = 40
TRIALS = 3


def random_curves(carto: CartoIH, rng, amplitude: float) -> dict[int, list[tuple[float, float]]]:
    curves = {}
    for shape_id, shape in enumerate(carto._ih.ttd.edge_shapes):
        if shape.name == "I":
            continue
        k = int(rng.integers(1, 5))
        x = np.sort(rng.uniform(0.05, 0.95, k))
        y = rng.uniform(-amplitude, amplitude, k)
        curves[shape_id] = [(0.0, 0.0), *zip(x.tolist(), y.tolist(), strict=True), (1.0, 0.0)]
    return curves


def replay(carto: CartoIH, captured, tile_size: float):
    """Lattice triples of the tiles carto-flow kept, and the number of repaired tiles."""
    native = np.array(carto._build_prototile(carto._edge_curve_modes).exterior.coords[:-1])
    area = abs(Polygon([(v.x, v.y) for v in carto._ih.vertices]).area)
    sf = tile_size / math.sqrt(area)
    kept, centers, repaired = [], [], 0
    for ti in captured:
        m = np.array(ti.T, dtype=float).reshape(2, 3)
        poly = Polygon(native @ m[:, :2].T * sf + m[:, 2] * sf)
        if not poly.is_valid:
            poly = make_valid(poly)
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda g: g.area)
            elif poly.geom_type != "Polygon":
                continue
            repaired += 1
        if poly.area < 1e-12:
            continue
        kept.append((ti.t1, ti.t2, ti.aspect))
        centers.append((poly.centroid.x, poly.centroid.y))
    centers_arr = np.array(centers)
    keep = np.ones(len(kept), dtype=bool)
    for i in range(len(kept)):
        if keep[i]:
            d = np.linalg.norm(centers_arr[i + 1 :] - centers_arr[i], axis=1)
            keep[i + 1 :] &= ~(d < tile_size * 0.01)
    return np.array(kept)[keep], centers_arr[keep], repaired


def diff(a, b) -> tuple[int, int]:
    """(pairs only in a, pairs only in b) of two symmetric boolean sparse matrices."""
    a, b = a.astype(bool), b.astype(bool)
    return int((a > b).nnz // 2), int((b > a).nnz // 2)


def trial(number: int, rng, regime: str) -> dict | None:
    base = IsohedralTiling(number)
    params = base.parameters
    for _ in range(20):
        try:
            p = params + rng.uniform(-0.08, 0.08, len(params))
            IsohedralTiling(number, p)
            break
        except ValueError:
            p = params
    amplitude = 1.5 if regime == "extreme" else 0.25
    for _ in range(12):
        carto0 = CartoIH(number, list(p))
        curves = random_curves(carto0, rng, amplitude)
        carto = CartoIH(number, list(p), edge_curves=curves)
        valid = carto._build_prototile(carto._edge_curve_modes).is_valid
        if regime == "extreme" or (regime == "valid") == valid:
            break
        amplitude = amplitude * 0.6 if regime == "valid" else amplitude * 1.5
    else:
        return None
    captured = []
    orig = carto._ih.fill_region_bounds

    def recording(*args):
        for x in orig(*args):
            captured.append(x)
            yield x

    carto._ih.fill_region_bounds = recording
    res = carto.generate(bounds=BOUNDS, n_tiles=N_TILES, margin=0.0)
    lattice, centers, repaired = replay(carto, captured, res.tile_size)
    ours = np.array([[p_.centroid.x, p_.centroid.y] for p_ in res.polygons])
    # Same tile order and count. make_valid can pick the other of two equal lobes of a repaired tile (floating-point
    # tie), which moves that tile's centroid; its slot (lattice triple) is unchanged.
    close = np.linalg.norm(centers - ours, axis=1) < 1e-9 if len(lattice) == len(ours) else np.zeros(1, dtype=bool)
    if len(lattice) != len(res.polygons) or close.mean() < 0.5:
        return {"aligned": False}
    tiles = IsohedralTiling(number, list(p)).tiles(lattice)
    table_edge, table_vertex = tiles.adjacency("edge"), tiles.adjacency("vertex-only")
    # carto-flow's result (its tolerance)
    c_edge, c_vertex = res.adjacency, res.vertex_adjacency
    from scipy.sparse import csr_array

    c_edge, c_vertex = csr_array(np.asarray(c_edge)), csr_array(np.asarray(c_vertex))
    # tight tolerance on the same polygons
    verts = [np.array(q.exterior.coords[:-1]) for q in res.polygons]
    t_edge, t_vertex = geometric_adjacency(verts, tol=1e-7 * res.tile_size)
    out = {
        "aligned": True,
        "tiles": len(lattice),
        "repaired": repaired,
        "ties": int((~close).sum()),
        "amplitude": amplitude,
        "points": int(np.mean([len(v) for v in verts])),
        "carto_edge": diff(table_edge, c_edge),  # (lost, spurious) relative to the lattice table
        "carto_vertex": diff(table_vertex, c_vertex),
        "tight_edge": diff(table_edge, t_edge),
        "tight_vertex": diff(table_vertex, t_vertex),
    }
    return out


REGIMES = ("valid", "repair", "extreme")


def run_type(number: int) -> dict:
    """All regimes of one type: summed (carto edge lost/spurious, carto vertex, tight edge, tight vertex) counts."""
    warnings.simplefilter("ignore")
    rng = np.random.default_rng(2026 + number)
    n_curves = sum(s != "I" for s in get_type(number).edge_shapes)
    out = {"n_curves": n_curves}
    for regime in REGIMES:
        agg = np.zeros(8, dtype=int)
        rec = {
            "agg": agg,
            "tiles": 0,
            "repaired": 0,
            "trials": 0,
            "bad_carto": 0,
            "bad_tight": 0,
            "unaligned": 0,
            "none": 0,
            "ties": 0,
        }
        if n_curves == 0 and regime != "valid":
            out[regime] = None
            continue
        for _ in range(TRIALS):
            r = trial(number, rng, regime) if n_curves else trial_straight(number, rng)
            if r is None:
                rec["none"] += 1
                continue
            if not r["aligned"]:
                rec["unaligned"] += 1
                continue
            rec["trials"] += 1
            rec["tiles"] += r["tiles"]
            rec["repaired"] += r["repaired"]
            rec["ties"] += r["ties"]
            agg += np.array([*r["carto_edge"], *r["carto_vertex"], *r["tight_edge"], *r["tight_vertex"]])
            rec["bad_carto"] += bool(any(r["carto_edge"]) or any(r["carto_vertex"]))
            rec["bad_tight"] += bool(any(r["tight_edge"]) or any(r["tight_vertex"]))
        out[regime] = rec
    return out


def main() -> None:
    from concurrent.futures import ProcessPoolExecutor

    t0 = time.perf_counter()
    numbers = tiling_types()
    only_i = [n for n in numbers if set(get_type(n).edge_shapes) <= {"I"}]
    print(f"types with only I edges (no curve possible, straight-edge control): {only_i}")
    print(
        "Cell: pairs only in the lattice table / pairs only in the geometric result (edge | vertex-only), "
        "for carto-flow's tolerance, then for the tight tolerance; then tiles, repaired tiles"
    )
    with ProcessPoolExecutor(max_workers=12) as pool:
        results = dict(zip(numbers, pool.map(run_type, numbers), strict=True))
    head = f"{'type':>5} {'J/U/S':>5} | " + " | ".join(f"{r:^40}" for r in REGIMES)
    print(head)
    for number in numbers:
        res = results[number]
        cells = []
        for regime in REGIMES:
            rec = res[regime]
            if rec is None or rec["trials"] == 0:
                cells.append(f"{'n/a':^40}")
                continue
            a = rec["agg"]
            cells.append(
                f"{a[0]}/{a[1]}|{a[2]}/{a[3]}  {a[4]}/{a[5]}|{a[6]}/{a[7]}  {rec['tiles']:>5} {rec['repaired']:>5}".center(
                    40
                )
            )
        print(f"IH{number:<3} {res['n_curves']:>5} | " + " | ".join(cells))
    print()
    for regime in REGIMES:
        recs = [(n, results[n][regime]) for n in numbers if results[n][regime] is not None]
        trials = sum(r["trials"] for _, r in recs)
        print(
            f"{regime}: {len(recs)} types, {trials} trials, tiles {sum(r['tiles'] for _, r in recs)}, repaired tiles "
            f"{sum(r['repaired'] for _, r in recs)} (equal-lobe ties {sum(r['ties'] for _, r in recs)}); trials differing from the lattice table: carto-flow tolerance "
            f"{sum(r['bad_carto'] for _, r in recs)}, tight tolerance {sum(r['bad_tight'] for _, r in recs)}; "
            f"not aligned {sum(r['unaligned'] for _, r in recs)}; no curve found {sum(r['none'] for _, r in recs)}"
        )
        print(f"  types differing, carto-flow tolerance: {[n for n, r in recs if r['bad_carto']]}")
        print(f"  types differing, tight tolerance: {[n for n, r in recs if r['bad_tight']]}")
    print(f"elapsed {time.perf_counter() - t0:.0f} s")


def trial_straight(number: int, rng) -> dict | None:
    """Control for types without curve shapes: same pipeline, no curves."""
    base = IsohedralTiling(number)
    carto = CartoIH(number, list(base.parameters))
    captured = []
    orig = carto._ih.fill_region_bounds

    def recording(*args):
        for x in orig(*args):
            captured.append(x)
            yield x

    carto._ih.fill_region_bounds = recording
    res = carto.generate(bounds=BOUNDS, n_tiles=N_TILES, margin=0.0)
    lattice, _, repaired = replay(carto, captured, res.tile_size)
    tiles = base.tiles(lattice)
    from scipy.sparse import csr_array

    verts = [np.array(q.exterior.coords[:-1]) for q in res.polygons]
    t_edge, t_vertex = geometric_adjacency(verts, tol=1e-7 * res.tile_size)
    return {
        "aligned": len(lattice) == len(res.polygons),
        "tiles": len(lattice),
        "repaired": repaired,
        "ties": 0,
        "carto_edge": diff(tiles.adjacency("edge"), csr_array(np.asarray(res.adjacency))),
        "carto_vertex": diff(tiles.adjacency("vertex-only"), csr_array(np.asarray(res.vertex_adjacency))),
        "tight_edge": diff(tiles.adjacency("edge"), t_edge),
        "tight_vertex": diff(tiles.adjacency("vertex-only"), t_vertex),
    }


if __name__ == "__main__":
    main()
