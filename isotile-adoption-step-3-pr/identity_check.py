"""Layouts of step 1 (dense tile adjacency) against step 2 (sparse), assignments compared exactly.

    python identity_check.py run <label> <output.pkl> [--repeat N] [case name, ...]
    python identity_check.py compare <old.pkl> <new.pkl>

``run`` uses whichever carto-flow is first on PYTHONPATH. Per case it stores the assignment (tile index of every item),
the region of every item and the wall time of each repeat. Mosaic runs use ``morph=False`` (the flow morph is not
bit-deterministic). ``compare`` checks the assignments with ``np.array_equal`` and prints best-of-N times.
"""

from __future__ import annotations

import pickle
import sys
import time
import warnings

import numpy as np

# name, input, tiling, layout, tile_count column, group_by
CASES = [
    ("states grid hexagon", "states", "hexagon", "grid", None, None),
    ("states grid square", "states", "square", "grid", None, None),
    ("states grid triangle", "states", "triangle", "grid", None, None),
    ("states grid quadrilateral", "states", "quadrilateral", "grid", None, None),
    ("states grid scalloped_hexagon", "states", "scalloped_hexagon", "grid", None, None),
    ("states grid hexagon tile_count", "states", "hexagon", "grid", "tiles", None),
    ("states grid square tile_count", "states", "square", "grid", "tiles", None),
    ("states mosaic hexagon", "states", "hexagon", "mosaic", "tiles", None),
    ("states mosaic square", "states", "square", "mosaic", "tiles", None),
    ("states mosaic triangle", "states", "triangle", "mosaic", "tiles", None),
    ("states mosaic scalloped_hexagon", "states", "scalloped_hexagon", "mosaic", "tiles", None),
    ("districts grid hexagon", "districts", "hexagon", "grid", None, None),
    ("districts grid square", "districts", "square", "grid", None, None),
    ("districts mosaic hexagon", "districts", "hexagon", "mosaic", None, "State Name"),
    ("districts mosaic square", "districts", "square", "mosaic", None, "State Name"),
    ("districts mosaic triangle", "districts", "triangle", "mosaic", None, "State Name"),
    ("districts mosaic scalloped_hexagon", "districts", "scalloped_hexagon", "mosaic", None, "State Name"),
]


def load_inputs() -> dict:
    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 150)).astype(int)
    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    return {"states": states, "districts": districts}


def make_layout(tiling: str, layout: str):
    from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

    return GridBasedLayout(tiling=tiling) if layout == "grid" else MosaicLayout(tiling=tiling, morph=False)


def run(label: str, out: str, repeat: int, only: list[str]) -> None:
    from carto_flow.symbol_cartogram import create_layout

    data = load_inputs()
    results = {}
    for name, inp, tiling, layout, tile_count, group_by in CASES:
        if only and name not in only:
            continue
        times = []
        first = None
        for _ in range(repeat):
            t0 = time.perf_counter()
            res = create_layout(
                data[inp],
                tile_count=tile_count,
                group_by=group_by,
                layout=make_layout(tiling, layout),
                show_progress=False,
            )
            times.append(time.perf_counter() - t0)
            if first is None:
                first = res
        src = first.source_indices
        results[name] = {
            "assignments": np.asarray(first.assignments, dtype=np.intp),
            "source_indices": None if src is None else np.asarray(src, dtype=np.intp),
            "n_tiles": int(first.tiling_result.n_tiles),
            "times": times,
        }
        print(f"[{label}] {name}: best {min(times):.2f}s of {repeat}, {len(results[name]['assignments'])} items", flush=True)
    with open(out, "wb") as f:
        pickle.dump(results, f)


def compare(old: str, new: str) -> int:
    with open(old, "rb") as f:
        a = pickle.load(f)
    with open(new, "rb") as f:
        b = pickle.load(f)
    bad = 0
    print(f"{'case':36s} {'items':>6s} {'lattice':>8s} {'identical':>10s} {'old (s)':>9s} {'new (s)':>9s} {'new/old':>8s}")
    for name in a:
        if name not in b:
            continue
        x, y = a[name], b[name]
        same = (
            np.array_equal(x["assignments"], y["assignments"])
            and x["n_tiles"] == y["n_tiles"]
            and (x["source_indices"] is None) == (y["source_indices"] is None)
            and (x["source_indices"] is None or np.array_equal(x["source_indices"], y["source_indices"]))
        )
        bad += not same
        to, tn = min(x["times"]), min(y["times"])
        print(f"{name:36s} {len(x['assignments']):6d} {x['n_tiles']:8d} {same!s:>10s} {to:9.2f} {tn:9.2f} {tn / to:8.2f}")
    print("ALL IDENTICAL" if not bad else f"{bad} CASES DIFFER")
    return bad


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    if sys.argv[1] == "run":
        args = sys.argv[4:]
        rep = 1
        if "--repeat" in args:
            i = args.index("--repeat")
            rep = int(args[i + 1])
            args = args[:i] + args[i + 2 :]
        run(sys.argv[2], sys.argv[3], rep, args)
    else:
        sys.exit(1 if compare(sys.argv[2], sys.argv[3]) else 0)
