"""Grid and mosaic layouts of the step 1 page (layout_cases.py), extended for the pin bump: more curved presets, the
unassigned core tiles and a lattice-phase scan for the curved presets. Whichever carto-flow is on PYTHONPATH.

    python layout_cases.py run <label> <output.pkl> [case name, ...]
    python layout_cases.py phase <label> <output.json>

``run`` lays out the cases (mosaic with ``morph=False``: the flow morph is not bit-deterministic) and stores per case the
wall time, the lattice size, the tiles assigned to each region (as polygons) and the placement metrics: tiles used,
regions that occupy more than one edge-connected block, and the mean and largest distance (in tile sizes) between the
centroid of a region and the centroid of its tiles.

``phase`` shifts the requested bounds of the tiling relative to the 49 states by six fractions of a tile (grid layout,
one tile per state) and stores the mean distance of each run, per tiling.
"""

from __future__ import annotations

import json
import pickle
import sys
import time
import warnings

import numpy as np
import shapely
from scipy.sparse import csr_array
from scipy.sparse.csgraph import connected_components

CASES = [
    # name, input, tiling, layout, tile_count column, group_by
    ("states grid hexagon", "states", "hexagon", "grid", None, None),
    ("states grid square", "states", "square", "grid", None, None),
    ("states grid triangle", "states", "triangle", "grid", None, None),
    ("states grid quadrilateral", "states", "quadrilateral", "grid", None, None),
    ("states grid scalloped_hexagon", "states", "scalloped_hexagon", "grid", None, None),
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
    ("states grid puzzle_piece", "states", "puzzle_piece", "grid", None, None),
    ("states grid wavy_triangle", "states", "wavy_triangle", "grid", None, None),
    ("states grid flowers", "states", "flowers", "grid", None, None),
    ("states grid arrow_quad", "states", "arrow_quad", "grid", None, None),
    ("states mosaic puzzle_piece", "states", "puzzle_piece", "mosaic", "tiles", None),
    ("states mosaic wavy_triangle", "states", "wavy_triangle", "mosaic", "tiles", None),
    ("states mosaic flowers", "states", "flowers", "mosaic", "tiles", None),
    ("states mosaic arrow_quad", "states", "arrow_quad", "mosaic", "tiles", None),
    ("districts grid puzzle_piece", "districts", "puzzle_piece", "grid", None, None),
    ("districts grid wavy_triangle", "districts", "wavy_triangle", "grid", None, None),
    ("districts grid flowers", "districts", "flowers", "grid", None, None),
    ("districts grid arrow_quad", "districts", "arrow_quad", "grid", None, None),
    ("districts mosaic puzzle_piece", "districts", "puzzle_piece", "mosaic", None, "State Name"),
    ("districts mosaic wavy_triangle", "districts", "wavy_triangle", "mosaic", None, "State Name"),
    ("districts mosaic flowers", "districts", "flowers", "mosaic", None, "State Name"),
    ("districts mosaic arrow_quad", "districts", "arrow_quad", "mosaic", None, "State Name"),
]

PHASES = [(0.0, 0.0), (0.25, 0.5), (0.5, 0.25), (0.75, 0.75), (0.4, 0.9), (0.9, 0.1)]


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


def edge_adjacency(tr) -> csr_array:
    adj = tr.adjacency
    return adj if hasattr(adj, "indptr") else csr_array(np.asarray(adj))


def region_metrics(gdf, res) -> dict:
    """Tiles used, split regions and distance of a region from its tiles, in tile sizes."""
    tr = res.tiling_result
    tiles = np.asarray(res.assignments, dtype=np.intp)
    src = res.source_indices
    regions = np.asarray(src, dtype=np.intp) if src is not None else np.arange(len(tiles), dtype=np.intp)
    n = len(gdf)
    per_region: list[list[int]] = [[] for _ in range(n)]
    for t, g in zip(tiles.tolist(), regions.tolist(), strict=True):
        per_region[g].append(t)
    adj = edge_adjacency(tr)
    split = 0
    disp = []
    for g, ts in enumerate(per_region):
        if not ts:
            continue
        sub = adj[ts][:, ts] if len(ts) > 1 else None
        if sub is not None and connected_components(sub, directed=False)[0] > 1:
            split += 1
        foot = shapely.union_all([tr.polygons[t] for t in ts]).centroid
        c = gdf.geometry.iloc[g].centroid
        disp.append(np.hypot(foot.x - c.x, foot.y - c.y) / tr.tile_size)
    return {
        "lattice_tiles": int(tr.n_tiles),
        "assigned": int(len(tiles)),
        "regions": int(sum(1 for ts in per_region if ts)),
        "split": int(split),
        "disp_mean": float(np.mean(disp)),
        "disp_max": float(np.max(disp)),
        "tile_size": float(tr.tile_size),
    }, per_region


def run(label: str, out: str, only: list[str] | None) -> None:
    from carto_flow.symbol_cartogram import create_layout

    data = load_inputs()
    results = {}
    for name, inp, tiling, layout, tile_count, group_by in CASES:
        if only and name not in only:
            continue
        gdf = data[inp]
        t0 = time.perf_counter()
        try:
            res = create_layout(
                gdf, tile_count=tile_count, group_by=group_by, layout=make_layout(tiling, layout), show_progress=False
            )
        except Exception as e:  # recorded
            results[name] = {"error": f"{type(e).__name__}: {e}"}
            print(f"[{label}] {name}: ERROR {e}", flush=True)
            continue
        dt = time.perf_counter() - t0
        metrics, per_region = region_metrics(gdf, res)
        tr = res.tiling_result
        assigned = np.asarray(res.assignments, dtype=np.intp)
        mosaic = getattr(res.metrics, "algorithm", None)
        results[name] = {
            "seconds": dt,
            **metrics,
            "mosaic_noncontiguous": getattr(mosaic, "n_noncontiguous_regions", None),
            "mosaic_split_groups": getattr(mosaic, "n_split_groups", None),
            "unassigned_core": getattr(mosaic, "n_unassigned_core_tiles", None),
            "assignments": assigned,
            "source_indices": None if res.source_indices is None else np.asarray(res.source_indices, dtype=np.intp),
            "n_tiles": int(tr.n_tiles),
            "tile_polygons_wkb": [shapely.to_wkb(tr.polygons[t]) for t in assigned],
            "tile_region": [int(g) for g in (res.source_indices if res.source_indices is not None else range(len(assigned)))],
        }
        print(f"[{label}] {name}: {dt:.1f}s {metrics}", flush=True)
    with open(out, "wb") as f:
        pickle.dump(results, f)


CURVED = [
    "scalloped_hexagon", "wavy_square", "puzzle_piece", "arrow_quad", "wavy_triangle",
    "interlocking_hexagon", "flowers", "scalloped_quad", "tree",
]


def phase(label: str, out: str) -> None:
    """Mean region-to-tile distance of the states grid layout of each curved preset at six lattice offsets."""
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
    from carto_flow.symbol_cartogram.tiling import IsohedralTiling

    gdf = load_inputs()["states"]
    cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
    results: dict[str, list[float]] = {}
    for name in CURVED:
        means = []
        for off in PHASES:
            tiling = IsohedralTiling.from_preset(name).with_offset(off)
            res = create_layout(gdf, layout=GridBasedLayout(tiling=tiling), show_progress=False)
            tr = res.tiling_result
            c = tr.centers[np.asarray(res.assignments)]
            means.append(float((np.hypot(*(c - cent).T) / tr.tile_size).mean()))
        results[name] = means
        print(f"[{label}] {name}: " + " ".join(f"{m:.3f}" for m in means), flush=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=1)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3], sys.argv[4:] or None)
    else:
        phase(sys.argv[2], sys.argv[3])
