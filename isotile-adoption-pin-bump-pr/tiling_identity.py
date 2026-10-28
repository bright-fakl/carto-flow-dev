"""Tilings of carto-flow, generated with many bounds, sizes, margins, rotations and offsets; stored for exact comparison.

    python tiling_identity.py run <out.pkl>          # whichever carto-flow is first on PYTHONPATH
    python tiling_identity.py compare <a.pkl> <b.pkl>

Per case: polygon coordinates, transforms, edge and vertex-only adjacency (CSR arrays), tile size and inscribed radius.
"""

from __future__ import annotations

import itertools
import pickle
import sys
import time
import warnings

import numpy as np
import shapely

BOUNDS = [(0.0, 0.0, 10.0, 6.0), (8.0e6 + 3.3, -2.0e6, 8.0e6 + 4000.0, -2.0e6 + 2500.0)]
SIZES = [("n_tiles", 100), ("n_tiles", 37), ("tile_size", 0.12)]  # tile_size as a fraction of sqrt(region area)
MARGINS = [0.0, 0.1]
ROTATIONS = [0.0, 25.0]
OFFSETS = [(0.0, 0.0), (0.3, 0.7), (-0.4, 1.6), (0.5, 0.5), (1.0, 0.0), (0.123456789, 0.987654321)]


def tilings() -> dict:
    from carto_flow.symbol_cartogram.tiling import (
        HexagonTiling,
        IsohedralTiling,
        QuadrilateralTiling,
        SquareTiling,
        TriangleTiling,
    )

    out = {
        "square": SquareTiling(),
        "hexagon": HexagonTiling(),
        "hexagon flat": HexagonTiling(pointy_top=False),
        "triangle": TriangleTiling.equilateral(),
        "triangle right": TriangleTiling.right(0.3),
        "quadrilateral": QuadrilateralTiling.parallelogram(60.0, 1.5),
        "trapezoid": QuadrilateralTiling.trapezoid(),
    }
    for name in IsohedralTiling.list_presets():
        out[f"preset {name}"] = IsohedralTiling.from_preset(name)
    for t in (1, 7, 41, 93):
        out[f"type {t}"] = IsohedralTiling(t)
    return out


def run(out: str) -> None:
    results = {}
    t0 = time.perf_counter()
    for name, tiling in tilings().items():
        for bounds, (kind, value), margin, rot, off in itertools.product(BOUNDS, SIZES, MARGINS, ROTATIONS, OFFSETS):
            t = tiling.rotated(rot) if rot else tiling
            t = t.with_offset(off) if off != (0.0, 0.0) else t
            if kind == "tile_size":
                value = value * float(np.sqrt((bounds[2] - bounds[0]) * (bounds[3] - bounds[1])))
            res = t.generate(bounds, margin=margin, **{kind: value})
            polys = np.asarray(res.polygons, dtype=object)
            adj, vadj = res.adjacency.tocsr(), res.vertex_adjacency.tocsr()
            results[(name, bounds, kind, round(value, 6), margin, rot, off)] = {
                "n": len(polys),
                "wkb": shapely.to_wkb(polys),
                "transforms": np.array([(*tr.center, tr.rotation, tr.flipped) for tr in res.transforms]),
                "adj": (adj.indptr, adj.indices),
                "vadj": (vadj.indptr, vadj.indices),
                "tile_size": res.tile_size,
                "inscribed": res.inscribed_radius,
            }
    print(f"{len(results)} cases in {time.perf_counter() - t0:.1f} s")
    with open(out, "wb") as f:
        pickle.dump(results, f)


def same(x: dict, y: dict) -> bool:
    return (
        x["n"] == y["n"]
        and bool(np.all(x["wkb"] == y["wkb"]))
        and np.array_equal(x["transforms"], y["transforms"])
        and all(np.array_equal(a, b) for a, b in zip(x["adj"] + x["vadj"], y["adj"] + y["vadj"], strict=True))
        and x["tile_size"] == y["tile_size"]
        and x["inscribed"] == y["inscribed"]
    )


def compare(a: str, b: str) -> int:
    with open(a, "rb") as f:
        ra = pickle.load(f)
    with open(b, "rb") as f:
        rb = pickle.load(f)
    names = list(dict.fromkeys(k[0] for k in ra))
    bad = 0
    print(f"{'tiling':28s} {'cases':>6s} {'identical':>10s} {'different':>10s} {'tiles a -> b (total)':>24s}")
    for name in names:
        keys = [k for k in ra if k[0] == name]
        diff = [k for k in keys if not same(ra[k], rb[k])]
        na, nb = sum(ra[k]["n"] for k in keys), sum(rb[k]["n"] for k in keys)
        bad += len(diff)
        print(f"{name:28s} {len(keys):6d} {len(keys) - len(diff):10d} {len(diff):10d} {na:>11d} -> {nb:<10d}")
    print(f"{len(ra)} cases, {bad} differ")
    return bad


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    if sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        sys.exit(1 if compare(sys.argv[2], sys.argv[3]) else 0)
