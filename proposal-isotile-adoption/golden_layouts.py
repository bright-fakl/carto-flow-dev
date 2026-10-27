"""Layout-level golden comparison: grid and mosaic layouts with the current tilings and with the isotile wrappers.

``run <label> <pickle> [case,case,...]`` runs the layouts on the standard inputs (49 US states, 432 congressional districts grouped by
state) with whatever carto-flow is on the path (put the sources of the current main, or the copy that holds the
wrapper prototype of ``wrapper_proto.py``, in front with PYTHONPATH) and stores per case: tile size, tile count, the
polygons of the assigned tiles per region and the lattice adjacency of the assigned tiles.
``compare <old.pkl[,more.pkl]> <new.pkl[,more.pkl]>`` prints, per case, tile counts, the placement metrics of both and the overlap of the
tile footprint of each region between the two runs.

Mosaic runs use ``morph=False`` (the flow morph is not bit-deterministic, see the project notes).

    PYTHONPATH=<src> python golden_layouts.py run old old.pkl
    PYTHONPATH=<src> python golden_layouts.py run new new.pkl
    python golden_layouts.py compare old.pkl new.pkl
"""

from __future__ import annotations

import pickle
import sys
import time
import warnings

import numpy as np
import shapely
from shapely.ops import unary_union

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
    ("districts mosaic hexagon", "districts", "hexagon", "mosaic", None, "State Name"),
]


def load_inputs():
    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 150)).astype(int)
    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    return {"states": states, "districts": districts}


def run(label: str, out: str, only: list[str] | None = None) -> None:
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

    data = load_inputs()
    results = {}
    for name, inp, tiling, layout, tile_count, group_by in CASES:
        if only and name not in only:
            continue
        gdf = data[inp]
        lay = GridBasedLayout(tiling=tiling) if layout == "grid" else MosaicLayout(tiling=tiling, morph=False)
        t0 = time.perf_counter()
        try:
            res = create_layout(gdf, tile_count=tile_count, group_by=group_by, layout=lay, show_progress=False)
        except Exception as e:  # recorded, the comparison reports it
            results[name] = {"error": f"{type(e).__name__}: {e}"}
            print(f"[{label}] {name}: ERROR {e}", flush=True)
            continue
        dt = time.perf_counter() - t0
        tr = res.tiling_result
        tiles = np.asarray(res.assignments, dtype=np.intp)
        src = res.source_indices
        regions = np.asarray(src, dtype=np.intp) if src is not None else np.arange(len(tiles), dtype=np.intp)
        n = len(gdf)
        polys = [[] for _ in range(n)]
        idx = [[] for _ in range(n)]
        for t, g in zip(tiles.tolist(), regions.tolist(), strict=True):
            polys[g].append(tr.polygons[t])
            idx[g].append(int(t))
        adj = np.asarray(tr.adjacency)
        assigned = np.unique(tiles)
        sub = adj[np.ix_(assigned, assigned)]
        results[name] = {
            "seconds": dt,
            "tile_size": float(tr.tile_size),
            "n_tiles": int(tr.n_tiles),
            "n_assigned": int(len(tiles)),
            "footprint_wkb": [shapely.to_wkb(unary_union(p)) if p else None for p in polys],
            "tiles_of_region": idx,
            "assigned": assigned,
            "assigned_adjacency": sub,
            "centroids": np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry]),
            "layout_centers": tr.centers[assigned],
            "tile_polygon_wkb": [shapely.to_wkb(tr.polygons[t]) for t in assigned],
        }
        print(f"[{label}] {name}: {dt:.1f}s, {tr.n_tiles} tiles, {len(tiles)} assigned", flush=True)
    with open(out, "wb") as f:
        pickle.dump(results, f)


def components(tiles: list[int], assigned_list: list[int], sub: np.ndarray) -> int:
    """Number of edge-connected blocks of ``tiles`` (lattice adjacency ``sub`` of the assigned tiles)."""
    pos = {t: i for i, t in enumerate(assigned_list)}
    tile_set = set(tiles)
    seen: set[int] = set()
    n = 0
    for t in tiles:
        if t in seen:
            continue
        n += 1
        stack = [t]
        seen.add(t)
        while stack:
            u = stack.pop()
            for v in np.flatnonzero(sub[pos[u]]):
                w = assigned_list[v]
                if w in tile_set and w not in seen:
                    seen.add(w)
                    stack.append(w)
    return n


def metrics(r: dict) -> dict:
    assigned_list = r["assigned"].tolist()
    sub = r["assigned_adjacency"]
    foot = [shapely.from_wkb(w) if w is not None else None for w in r["footprint_wkb"]]
    s = r["tile_size"]
    disp, split = [], 0
    for g, tiles in enumerate(r["tiles_of_region"]):
        if not tiles:
            continue
        split += components(tiles, assigned_list, sub) > 1
        c = foot[g].centroid
        disp.append(np.hypot(c.x - r["centroids"][g][0], c.y - r["centroids"][g][1]) / s)
    return {"tiles": r["n_tiles"], "assigned": r["n_assigned"], "split": int(split), "disp_mean": float(np.mean(disp)), "disp_max": float(np.max(disp))}


def compare(old_path: str, new_path: str) -> None:
    old, new = ({} for _ in range(2))
    for target, paths in ((old, old_path), (new, new_path)):
        for path in paths.split(","):  # several pickles of one side are merged
            with open(path, "rb") as f:
                target.update(pickle.load(f))
    print(f"{'case':<34}{'lattice tiles old/new':>22}{'assigned':>10}{'regions split':>15}{'mean displacement (tile sizes)':>34}{'footprint IoU mean / min':>26}{'s old/new':>12}")
    for name, *_ in CASES:
        if name not in old or name not in new:
            continue
        a, b = old[name], new[name]
        if "error" in a or "error" in b:
            print(f"{name:<34} old: {a.get('error', 'ok')}  new: {b.get('error', 'ok')}")
            continue
        ma, mb = metrics(a), metrics(b)
        ious = []
        for fa, fb in zip(a["footprint_wkb"], b["footprint_wkb"], strict=True):
            if fa is None or fb is None:
                continue
            A, B = shapely.from_wkb(fa), shapely.from_wkb(fb)
            u = A.union(B).area
            ious.append(A.intersection(B).area / u if u > 0 else 1.0)
        print(
            f"{name:<34}{ma['tiles']:>10}/{mb['tiles']:<11}{ma['assigned']:>5}/{mb['assigned']:<4}{ma['split']:>8}/{mb['split']:<6}"
            f"{ma['disp_mean']:>14.3f}/{mb['disp_mean']:<8.3f}(max {ma['disp_max']:.2f}/{mb['disp_max']:.2f})"
            f"{np.mean(ious):>12.3f} /{np.min(ious):>6.3f}{a['seconds']:>8.1f}/{b['seconds']:<6.1f}"
        )


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3], sys.argv[4].split(",") if len(sys.argv) > 4 else None)
    else:
        compare(sys.argv[2], sys.argv[3])
