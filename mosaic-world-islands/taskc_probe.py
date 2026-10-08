"""Feasibility probe for a 'guarantee at least one tile' placement option.

For every region that ends up with zero tiles, find the lattice cell that
overlaps its (morphed) geometry most, and report whether that cell is free in
the final assignment, whether it is a core tile, and which component owns it.
A free, non-core cell means the guarantee costs no other region a tile; a cell
already owned means the guarantee has to take one from somebody.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import wi_inputs as W  # noqa: E402

OUT = HERE / "taskc_probe.jsonl"


def probe(case, budget, morph):
    import shapely
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    from carto_flow.flow_cartogram.algorithm import morph_geometries
    from carto_flow.flow_cartogram.options import MorphOptions
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.data_prep import prepare_layout_data
    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout
    from carto_flow.symbol_cartogram.layouts.mosaic._calibration import calibrate_tiling
    from carto_flow.symbol_cartogram.tiling import resolve_tiling

    gdf = {"world": W.load_world, "africa": W.load_africa}[case](budget)
    names = [str(x) for x in gdf["name"]]
    data = prepare_layout_data(gdf, tile_count="tiles")
    geoms = list(data.source_gdf.geometry)
    counts = data.counts_G
    components = data.components
    comp_of = np.zeros(len(geoms), dtype=int)
    for ci, c in enumerate(components):
        for i in c:
            comp_of[i] = ci

    if morph:
        r = morph_geometries(geoms, values=counts.astype(float),
                             options=MorphOptions(n_iter=100, show_progress=False))
        working = [shapely.make_valid(g) for g in r.latest.geometry]
    else:
        working = [shapely.make_valid(g) for g in geoms]
    union = unary_union(working)
    setup = calibrate_tiling(resolve_tiling("hexagon"), union.bounds, union,
                             len(data.positions), buffer_rings=1, min_overlap_frac=0.1)
    tr = setup.tiling_result
    polys = np.asarray(tr.polygons)
    tile_area = polys[0].area
    tree = STRtree(polys)

    res = create_layout(gdf, tile_count="tiles", layout=MosaicLayout(morph=morph), show_progress=False)
    placed = res.regions_gdf["tile_count"].to_numpy()

    # occupied cells of the final layout, keyed by rounded centroid (tile
    # indices are identical because calibration is deterministic)
    occ = {}
    for i, g in enumerate(res.tiles_gdf["geometry_id"].tolist()):
        c = res.tiles_gdf.geometry.iloc[i].centroid
        occ[(round(c.x, 3), round(c.y, 3))] = int(g)

    rows = []
    for g in range(len(geoms)):
        if placed[g] != 0:
            continue
        cand = tree.query(working[g], predicate="intersects")
        if len(cand) == 0:
            rows.append(dict(region=names[g], component=int(comp_of[g]), best_frac=0.0,
                             best_tile=None, tile_free=None, owner=None, core=None))
            continue
        inter = shapely.area(shapely.intersection(polys[cand], working[g]))
        order = np.argsort(-inter)
        t = int(cand[order[0]])
        c = polys[t].centroid
        key = (round(c.x, 3), round(c.y, 3))
        owner = occ.get(key)
        rows.append(dict(
            region=names[g], component=int(comp_of[g]),
            best_frac=float(inter[order[0]] / tile_area),
            best_tile=t, core=bool(t in setup.core_set),
            tile_free=owner is None,
            owner=None if owner is None else names[owner],
            n_zero_in_component=int(sum(1 for i in components[comp_of[g]] if placed[i] == 0)),
            component_size=len(components[comp_of[g]]),
            component_demand=int(counts[np.array(components[comp_of[g]])].sum()),
        ))

    # how many of the best-overlap cells collide with each other
    best_tiles = [r["best_tile"] for r in rows if r["best_tile"] is not None]
    collisions = {t: n for t, n in Counter(best_tiles).items() if n > 1}

    rec = dict(case=case, budget=budget, morph=morph, n_zero=int((placed == 0).sum()),
               rows=rows, n_free=sum(1 for r in rows if r["tile_free"]),
               n_taken=sum(1 for r in rows if r["tile_free"] is False),
               best_tile_collisions=collisions,
               core_tiles=len(setup.core_set), requested=int(counts.sum()),
               placed_total=int(placed.sum()))
    with OUT.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"\n== {case} b{budget} morph={morph}: {rec['n_zero']} zero-tile regions, "
          f"{rec['n_free']} best cells free, {rec['n_taken']} already owned, "
          f"collisions={collisions}")
    print(f"   core tiles={rec['core_tiles']} requested={rec['requested']} placed={rec['placed_total']}")
    for r in rows:
        print(f"   {r['region']:24s} comp={r['component']:2d} (size {r.get('component_size')}, "
              f"demand {r.get('component_demand')}, {r.get('n_zero_in_component')} zero) "
              f"best_frac={r['best_frac']:.3f} core={r['core']} free={r['tile_free']} owner={r['owner']}")
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budgets", default="384,800")
    a = ap.parse_args()
    for b in [int(x) for x in a.budgets.split(",")]:
        for morph in (True, False):
            probe("world", b, morph)
