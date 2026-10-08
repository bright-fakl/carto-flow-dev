"""Measure mosaic repair objective on 4 cases. Usage: measure.py <label> <outjson>"""

import json
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import geopandas as gpd
import numpy as np
from shapely.geometry import box

import carto_flow.data as cfdata
import carto_flow.symbol_cartogram as smb
from carto_flow.geo_utils import find_adjacent_pairs
from carto_flow.symbol_cartogram.layouts import prepare_layout_data
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

COUNTS_3X3 = [4, 5, 3, 6, 4, 5, 3, 4, 6]


def blocks_per_key(result, keys):
    polys = [result.tiling_result.polygons[int(t)] for t in result.assignments]
    adj = {i: set() for i in range(len(polys))}
    for i, j, _ in find_adjacent_pairs(polys):
        adj[i].add(j)
        adj[j].add(i)
    grouped = {}
    for slot, geom in enumerate(np.asarray(result.source_indices).tolist()):
        grouped.setdefault(keys[geom], []).append(slot)
    out = {}
    for k, tiles in grouped.items():
        tset = set(tiles)
        seen, blocks = set(), 0
        for s in tiles:
            if s in seen:
                continue
            blocks += 1
            stack = [s]
            while stack:
                u = stack.pop()
                if u in seen:
                    continue
                seen.add(u)
                stack.extend(v for v in adj[u] if v in tset)
        out[k] = blocks
    return out


def summarize(name, gdf, result, t, group_keys=None):
    G = len(gdf)
    per_geom = blocks_per_key(result, list(range(G)))
    noncontig = sum(1 for v in per_geom.values() if v > 1)
    split_groups = None
    if group_keys is not None:
        per_group = blocks_per_key(result, list(group_keys))
        split_groups = sum(1 for v in per_group.values() if v > 1)
    m = result.metrics
    am = m.algorithm
    return {
        "case": name,
        "regions_correct": int(am.regions_correct),
        "regions_total": int(am.regions_total),
        "non_contiguous_regions": int(noncontig),
        "split_groups": split_groups,
        "iterations": m.iterations,
        "converged": m.converged,
        "wall_s": round(t, 2),
        "extra": {
            k: getattr(am, k, None)
            for k in ("n_noncontiguous_regions", "n_split_groups", "repair_passes")
        },
    }


def run_fixture():
    geoms = [box(c, r, c + 1, r + 1) for r in range(3) for c in range(3)]
    gdf = gpd.GeoDataFrame({"tiles": COUNTS_3X3}, geometry=geoms)
    data = prepare_layout_data(gdf, tile_count="tiles")
    t0 = time.perf_counter()
    res = MosaicLayout(morph=False).compute(data, show_progress=False)
    return summarize("3x3 fixture", gdf, res, time.perf_counter() - t0)


def run_states():
    g = cfdata.load_us_census(population=True)
    g["tiles"] = np.maximum(1, np.round(g["Population"] / g["Population"].sum() * 150)).astype(int)
    t0 = time.perf_counter()
    r = smb.create_symbol_cartogram(g, tile_count="tiles", layout="mosaic", show_progress=False)
    t = time.perf_counter() - t0
    return summarize("US states (tile_count~Population)", g, r.layout_result, t)


def run_districts(group=False):
    g = cfdata.load_us_census(population=True, level="congressional_district")
    kw = {"group_by": "State Name"} if group else {}
    t0 = time.perf_counter()
    r = smb.create_symbol_cartogram(g, layout="mosaic", show_progress=False, **kw)
    t = time.perf_counter() - t0
    keys = list(g["State Name"]) if group else None
    name = "districts + group_by" if group else "districts (1 tile each)"
    return summarize(name, g, r.layout_result, t, group_keys=keys)


if __name__ == "__main__":
    label, out = sys.argv[1], sys.argv[2]
    rows = [run_fixture(), run_states(), run_districts(False), run_districts(True)]
    with open(out, "w") as fh:
        json.dump({"label": label, "rows": rows}, fh, indent=2, default=str)
    for r in rows:
        print(r)
