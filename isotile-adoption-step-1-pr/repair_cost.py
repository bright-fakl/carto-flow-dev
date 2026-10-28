"""Time per stage of the mosaic layout, and the work of the repair stages, on four inputs.

    python repair_cost.py <label> <output.json> [input name, ...] [--repeat N]

Run once with the sources of the old code on PYTHONPATH and once with the new code, one after the other in the same
session and with nothing else running on the machine: timings are comparable only within a session.

Inputs (all hexagon and square tilings, ``morph=False``):

* ``districts``: the 432 congressional districts, one tile count per district, grouped by state
* ``states``: the 49 states, 150 tiles in proportion to the population
* ``texas``: the 254 counties of Texas, about 400 tiles in proportion to the population
* ``districts-division``: the 432 districts grouped by Census division

Per run: wall time, calibrated lattice size, and the cumulative time and the number of calls of tile generation
(``Tiling.generate``), ``calibrate_tiling``, the Hungarian assignment with its repair loop, ``_relocate_ring_tiles``,
``_chain_swap_repair`` (with ``repair_contiguity`` inside it) and ``_count_split_units`` (the score of a candidate move).
A second, untimed run counts the work: ring tiles relocated, passes and swaps of ``repair_contiguity``, splits before and
after the chain-swap repair, and the region and group counts of the result.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import time
import warnings

import numpy as np

STAGES: dict[str, dict] = {}


def timed(owner, name: str, label: str):
    original = getattr(owner, name)

    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            entry = STAGES.setdefault(label, {"seconds": 0.0, "calls": 0})
            entry["seconds"] += time.perf_counter() - t0
            entry["calls"] += 1

    setattr(owner, name, wrapper)
    return original


def tiling_classes(base):
    for cls in base.__subclasses__():
        yield cls
        yield from tiling_classes(cls)


def install_timers() -> None:
    import carto_flow.geo_utils.contiguity as contiguity
    import carto_flow.symbol_cartogram.layouts.mosaic as mosaic
    from carto_flow.symbol_cartogram import tiling as tmod
    from carto_flow.symbol_cartogram.layouts.mosaic import _assignment, _calibration

    seen = set()
    for cls in tiling_classes(tmod.Tiling):
        if "generate" in cls.__dict__ and cls.__dict__["generate"] not in seen:
            seen.add(cls.__dict__["generate"])
            timed(cls, "generate", "tiling.generate")
    timed(_calibration, "calibrate_tiling", "calibrate_tiling")
    timed(_assignment, "hungarian_morphed_assignment", "hungarian_morphed_assignment")
    timed(mosaic, "_relocate_ring_tiles", "_relocate_ring_tiles")
    timed(mosaic, "_chain_swap_repair", "_chain_swap_repair")
    timed(contiguity, "repair_contiguity", "repair_contiguity")
    timed(mosaic, "_count_split_units", "_count_split_units")


def load_inputs() -> dict:
    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 150)).astype(int)
    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    counties = load_us_census(population=True, level="county").reset_index(drop=True)
    texas = counties[counties["State Name"] == "Texas"].reset_index(drop=True)
    pop = texas["Population"].to_numpy(dtype=float)
    texas["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 400)).astype(int)
    import geopandas as gpd
    from shapely.geometry import box

    rng = np.random.default_rng(7)
    squares = gpd.GeoDataFrame(
        {"tiles": rng.integers(2, 7, size=100)}, geometry=[box(c, r, c + 1, r + 1) for r in range(10) for c in range(10)]
    )
    return {
        "grid-10x10": (squares, "tiles", None),
        "districts": (districts, None, "State Name"),
        "states": (states, "tiles", None),
        "texas": (texas, "tiles", None),
        "districts-division": (districts, None, "Division"),
    }


def run_once(gdf, tile_count, group_by, tiling: str, show_progress: bool):
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

    t0 = time.perf_counter()
    res = create_layout(
        gdf,
        tile_count=tile_count,
        group_by=group_by,
        layout=MosaicLayout(tiling=tiling, morph=False),
        show_progress=show_progress,
    )
    return res, time.perf_counter() - t0


def counting_run(gdf, tile_count, group_by, tiling: str) -> dict:
    """Run with progress output captured; parse the repair work out of it."""
    import carto_flow.geo_utils.contiguity as contiguity

    original = contiguity.repair_contiguity

    def forced(*args, **kwargs):
        kwargs["show_progress"] = True
        return original(*args, **kwargs)

    contiguity.repair_contiguity = forced
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            res, _ = run_once(gdf, tile_count, group_by, tiling, show_progress=True)
    finally:
        contiguity.repair_contiguity = original
    text = buf.getvalue()
    passes = [(int(m[0]), int(m[1])) for m in re.findall(r"\[contiguity\]\s+pass\s+(\d+)\s+swaps=(\d+)", text)]
    relocated = re.findall(r"ring swap-back: (\d+) tile\(s\) relocated; (\d+) ring tile\(s\) and (\d+) unassigned", text)
    chain = re.findall(r"chain-swap repair: \(group, geom\) splits \((\d+), (\d+)\) -> \((\d+), (\d+)\)\s+(\w+)", text)
    algo = res.metrics.algorithm
    return {
        "ring_relocated": [int(r[0]) for r in relocated],
        "ring_tiles_left": [int(r[1]) for r in relocated],
        "unassigned_core_after_ring": [int(r[2]) for r in relocated],
        "chain_swap": [
            {"before": [int(c[0]), int(c[1])], "after": [int(c[2]), int(c[3])], "result": c[4]} for c in chain
        ],
        "contiguity_passes": len(passes),
        "contiguity_swaps": sum(s for _, s in passes),
        "hungarian_repair_passes": int(algo.repair_passes),
        "noncontiguous_regions": int(algo.n_noncontiguous_regions),
        "split_groups": int(algo.n_split_groups),
        "regions_correct": f"{algo.regions_correct}/{algo.regions_total}",
        "unassigned_core_tiles": int(algo.n_unassigned_core_tiles),
        "enclosed_unassigned_tiles": int(algo.n_enclosed_unassigned_tiles),
        "lattice_tiles": int(res.tiling_result.n_tiles),
        "assigned_tiles": int(len(res.assignments)),
    }


def main(label: str, out: str, names: list[str], repeat: int) -> None:
    install_timers()
    data = load_inputs()
    results = []
    for name in names or list(data):
        gdf, tile_count, group_by = data[name]
        for tiling in ("hexagon", "square"):
            runs = []
            for _ in range(repeat):
                STAGES.clear()
                _, dt = run_once(gdf, tile_count, group_by, tiling, show_progress=False)
                runs.append({"wall": dt, "stages": json.loads(json.dumps(STAGES))})
            best = min(runs, key=lambda r: r["wall"])
            work = counting_run(gdf, tile_count, group_by, tiling)
            results.append({"input": name, "tiling": tiling, "best": best, "all_wall": [r["wall"] for r in runs], "work": work})
            st = best["stages"]
            print(
                f"[{label}] {name} {tiling}: wall {best['wall']:.2f}s (runs {[round(r['wall'], 2) for r in runs]}), "
                + ", ".join(f"{k} {v['seconds']:.2f}s/{v['calls']}" for k, v in st.items())
                + f" | work {json.dumps(work)}",
                flush=True,
            )
    with open(out, "w") as f:
        json.dump(results, f, indent=1)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    args = sys.argv[3:]
    rep = 3
    if "--repeat" in args:
        i = args.index("--repeat")
        rep = int(args[i + 1])
        del args[i : i + 2]
    main(sys.argv[1], sys.argv[2], args, rep)
