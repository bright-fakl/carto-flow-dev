"""Rotation and offset experiments with whichever carto-flow is first on PYTHONPATH.

    python experiments.py <label> <output.pkl> [--repeat N] [experiment, ...]

Experiments (``--repeat`` runs of each case, the fastest wall time is kept):

* ``rotation``: grid layout of the 49 states, hexagon and square, rotation 0 and 30 degrees, the states centered (as
  loaded, EPSG:102008, meters) and moved 8e6 m east. Runs with the old and the new code.
* ``offsets``: grid and mosaic layout of the states, hexagon and square, offsets (0, 0), (0.25, 0.25), (0.5, 0.5); mosaic
  also at rotation 30 centered and moved. New code only (the options do not exist before).
* ``symmetric``: mosaic layout of the 10 x 10 grid of unit cells (2 to 6 tiles per cell, seed 7, the input of the
  step 1 page), square and hexagon, a 5 x 5 scan of the offset and four rotations. New code only.

Per case: wall time, tiles of the lattice and used, mean and largest distance between the centroid of a region and the
centroid of its tiles in tile sizes, and for the mosaic layout the number of unassigned core tiles and of
non-contiguous regions. The tile polygons and the assignment are stored for the figures.
"""

from __future__ import annotations

import pickle
import sys
import time
import warnings

import numpy as np
import shapely

SHIFT = 8.0e6
OFFSETS = [(0.0, 0.0), (0.25, 0.25), (0.5, 0.5)]
SCAN = [0.0, 0.2, 0.4, 0.6, 0.8]


def load_inputs() -> dict:
    import geopandas as gpd
    from shapely.geometry import box

    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 150)).astype(int)
    rng = np.random.default_rng(7)
    squares = gpd.GeoDataFrame(
        {"tiles": rng.integers(2, 7, size=100)}, geometry=[box(c, r, c + 1, r + 1) for r in range(10) for c in range(10)]
    )
    return {"states": states, "grid10": squares}


def moved(gdf, dx: float):
    out = gdf.copy()
    out["geometry"] = gdf.geometry.translate(xoff=dx)
    return out


def layout_for(kind: str, tiling: str, rotation: float, offset: tuple[float, float], new: bool):
    from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

    extra: dict = {}
    if rotation != 0.0:
        extra["rotation"] = rotation
    if offset != (0.0, 0.0):
        extra["offset"] = offset
    if kind == "grid":
        return GridBasedLayout(tiling=tiling, **extra)
    return MosaicLayout(tiling=tiling, morph=False, **extra)


def measure(gdf, kind: str, tiling: str, rotation: float, offset, new: bool, tile_count, repeat: int) -> dict:
    from carto_flow.symbol_cartogram import create_layout

    best = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        res = create_layout(
            gdf, tile_count=tile_count, layout=layout_for(kind, tiling, rotation, offset, new), show_progress=False
        )
        dt = time.perf_counter() - t0
        if best is None or dt < best[0]:
            best = (dt, res)
    dt, res = best
    tr = res.tiling_result
    tiles = np.asarray(res.assignments, dtype=np.intp)
    src = res.source_indices
    regions = np.asarray(src, dtype=np.intp) if src is not None else np.arange(len(tiles), dtype=np.intp)
    per_region: list[list[int]] = [[] for _ in range(len(gdf))]
    for t, g in zip(tiles.tolist(), regions.tolist(), strict=True):
        per_region[g].append(t)
    disp = []
    for g, ts in enumerate(per_region):
        if not ts:
            continue
        foot = shapely.union_all([tr.polygons[t] for t in ts]).centroid
        c = gdf.geometry.iloc[g].centroid
        disp.append(np.hypot(foot.x - c.x, foot.y - c.y) / tr.tile_size)
    out = {
        "seconds": dt,
        "lattice_tiles": int(tr.n_tiles),
        "assigned": int(len(tiles)),
        "disp_mean": float(np.mean(disp)),
        "disp_max": float(np.max(disp)),
        "tile_size": float(tr.tile_size),
        "polygons": shapely.to_wkb(np.asarray(tr.polygons, dtype=object)),
        "assignments": tiles,
        "regions": regions,
    }
    algo = getattr(res.metrics, "algorithm", None)
    if kind == "mosaic" and algo is not None:
        out["unassigned_core"] = int(algo.n_unassigned_core_tiles)
        out["noncontiguous"] = int(algo.n_noncontiguous_regions)
    return out


def main(label: str, out: str, only: list[str], repeat: int) -> None:
    import inspect

    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayoutOptions

    new = "offset" in inspect.signature(MosaicLayoutOptions).parameters
    data = load_inputs()
    states, grid10 = data["states"], data["grid10"]
    results: dict = {}

    def record(key, **kw):
        results[key] = measure(**kw, new=new, repeat=repeat)
        r = results[key]
        extra = f", unassigned core {r['unassigned_core']}, noncontiguous {r['noncontiguous']}" if "unassigned_core" in r else ""
        print(f"[{label}] {key}: {r['seconds']:.2f}s, mean distance {r['disp_mean']:.3f}, max {r['disp_max']:.2f}{extra}", flush=True)

    if not only or "rotation" in only:
        for tiling in ("hexagon", "square"):
            for pos, dx in (("centered", 0.0), ("moved", SHIFT)):
                for rot in (0.0, 30.0):
                    gdf = states if dx == 0 else moved(states, dx)
                    record(("rotation", tiling, pos, rot), gdf=gdf, kind="grid", tiling=tiling, rotation=rot,
                           offset=(0.0, 0.0), tile_count=None)
    if new and (not only or "offsets" in only):
        for tiling in ("hexagon", "square"):
            for kind in ("grid", "mosaic"):
                for off in OFFSETS:
                    record(("offsets", kind, tiling, off), gdf=states, kind=kind, tiling=tiling, rotation=0.0, offset=off,
                           tile_count="tiles" if kind == "mosaic" else None)
        for pos, dx in (("centered", 0.0), ("moved", SHIFT)):
            gdf = states if dx == 0 else moved(states, dx)
            record(("mosaic rotation", "hexagon", pos, 30.0), gdf=gdf, kind="mosaic", tiling="hexagon", rotation=30.0,
                   offset=(0.0, 0.0), tile_count="tiles")
    if new and (not only or "symmetric" in only):
        for tiling in ("square", "hexagon"):
            for u in SCAN:
                for v in SCAN:
                    record(("symmetric", tiling, "offset", (u, v)), gdf=grid10, kind="mosaic", tiling=tiling, rotation=0.0,
                           offset=(u, v), tile_count="tiles")
            for rot in (0.0, 15.0, 30.0, 45.0):
                record(("symmetric", tiling, "rotation", rot), gdf=grid10, kind="mosaic", tiling=tiling, rotation=rot,
                       offset=(0.0, 0.0), tile_count="tiles")
    with open(out, "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    args = sys.argv[3:]
    rep = 3
    if "--repeat" in args:
        i = args.index("--repeat")
        rep = int(args[i + 1])
        del args[i : i + 2]
    main(sys.argv[1], sys.argv[2], args, rep)
