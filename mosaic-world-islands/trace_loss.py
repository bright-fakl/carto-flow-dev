"""Replicate MosaicLayout._compute's per-component solve loop and trace where
each region's tiles are lost: empty pool, rectangular LSA starvation, or a
later component overwriting an already-assigned tile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wi_inputs as W  # noqa: E402
from diagnose import build_stage_info  # noqa: E402


def trace(gdf, *, morph, tile_count="tiles", min_overlap_frac=0.1, extra_tile_rings=1):
    import shapely
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    from carto_flow.symbol_cartogram.layouts.data_prep import prepare_layout_data
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, _chain_swap_repair, _relocate_ring_tiles
    from carto_flow.symbol_cartogram.layouts.mosaic._assignment import hungarian_morphed_assignment
    from carto_flow.symbol_cartogram.layouts.mosaic._calibration import calibrate_tiling
    from carto_flow.symbol_cartogram.tiling import resolve_tiling

    data = prepare_layout_data(gdf, tile_count=tile_count)
    geometries = list(data.source_gdf.geometry)
    G = len(geometries)
    counts = data.counts_G
    components = data.components
    n_components = len(components)
    target_count = len(data.positions)
    names = [str(x) for x in gdf["name"]]

    if morph:
        from carto_flow.flow_cartogram.algorithm import morph_geometries
        from carto_flow.flow_cartogram.options import MorphOptions
        r = morph_geometries(geometries, values=counts.astype(np.float64),
                             options=MorphOptions(n_iter=100, show_progress=False))
        working = list(r.latest.geometry)
    else:
        working = geometries
    working = [shapely.make_valid(g) for g in working]
    working_union = unary_union(working)
    comp_union_list = [unary_union([working[i] for i in idx]) for idx in components]
    comp_tree = STRtree(comp_union_list)

    setup = calibrate_tiling(resolve_tiling("hexagon"), working_union.bounds, working_union,
                             target_count, buffer_rings=extra_tile_rings,
                             min_overlap_frac=min_overlap_frac)
    tr, adj_list, core_set = setup.tiling_result, setup.adj_list, setup.core_set
    valid = setup.valid_tile_indices
    T = len(tr.polygons)

    tile_to_comp = np.full(T, -1, dtype=np.int32)
    for t in valid:
        tp = tr.polygons[t]
        cand = comp_tree.query(tp, predicate="intersects")
        if len(cand) == 0:
            tc = tp.centroid
            tile_to_comp[t] = min(range(n_components), key=lambda c: tc.distance(comp_union_list[c].centroid))
        elif len(cand) == 1:
            tile_to_comp[t] = int(cand[0])
        else:
            best_c, best_a = -1, 0.0
            for c in cand:
                a = tp.intersection(comp_union_list[c]).area
                if a > best_a:
                    best_a, best_c = a, c
            tile_to_comp[t] = best_c
    pools = [[] for _ in range(n_components)]
    for t in valid:
        pools[int(tile_to_comp[t])].append(t)
    core_sizes = [len(p) for p in pools]
    if extra_tile_rings > 0:
        for c in range(n_components):
            ps = set(pools[c])
            for _ in range(extra_tile_rings):
                ps |= {nb for t in ps for nb in adj_list[t] if nb not in ps}
            pools[c] = sorted(ps)

    hopts = HungarianOptions()
    assignment = np.full(T, -1, dtype=np.int32)
    owner_comp = np.full(T, -1, dtype=np.int32)
    empty_pool_regions, lsa_short = [], []
    overwrites = []  # (tile, from_geom, from_comp, to_geom, to_comp)

    for c, gidx in enumerate(components):
        arr = np.array(gidx, dtype=np.intp)
        pool_c = pools[c]
        demand = int(counts[arr].sum())
        if not pool_c or demand == 0:
            empty_pool_regions.extend(int(i) for i in arr if counts[i] > 0)
            continue
        if len(pool_c) < demand:
            lsa_short.append((c, demand, len(pool_c)))
        ac = hungarian_morphed_assignment(
            tr, [working[i] for i in gidx], counts[arr], pool_c, adj_list,
            core_set=core_set, working_union=comp_union_list[c], options=hopts,
            group_labels=None, show_progress=False, stats={},
        )
        for t in pool_c:
            lg = int(ac[t])
            if lg >= 0:
                if assignment[t] >= 0:
                    overwrites.append((int(t), int(assignment[t]), int(owner_comp[t]),
                                       int(arr[lg]), int(c)))
                assignment[t] = int(arr[lg])
                owner_comp[t] = c

    after_solve = np.bincount(assignment[assignment >= 0], minlength=G)

    a2 = _relocate_ring_tiles(assignment, adj_list, set(valid), G, None,
                              max_hops=hopts.ring_swapback_max_hops, show_progress=False)
    after_ring = np.bincount(a2[a2 >= 0], minlength=G)
    a3 = _chain_swap_repair(a2, adj_list, G, None, hopts.swap_repair_passes, False)
    after_chain = np.bincount(a3[a3 >= 0], minlength=G)

    return dict(
        names=names, counts=counts.tolist(), G=G,
        comp_of=[int(np.where([i in set(cc) for cc in components])[0][0]) if False else 0 for i in []],
        after_solve=after_solve.tolist(), after_ring=after_ring.tolist(),
        after_chain=after_chain.tolist(),
        empty_pool_regions=empty_pool_regions,
        lsa_short=lsa_short,
        overwrites=overwrites,
        comp_demand=[int(counts[np.array(i)].sum()) for i in components],
        comp_core=core_sizes, comp_pool=[len(p) for p in pools],
        components=[list(map(int, cc)) for cc in components],
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="world")
    ap.add_argument("--budget", type=int, default=384)
    ap.add_argument("--morph", type=int, default=1)
    a = ap.parse_args()
    gdf = {"world": W.load_world, "africa": W.load_africa,
           "world_mainland": lambda b: W.load_world_mainland(b)[0]}[a.case](a.budget)
    r = trace(gdf, morph=bool(a.morph))
    out = HERE / f"trace_{a.case}_{a.budget}_morph{a.morph}.json"
    out.write_text(json.dumps(r))
    n = r["names"]; cnt = r["counts"]
    print(f"empty-pool regions: {[n[i] for i in r['empty_pool_regions']]}")
    print(f"components with pool < demand: {r['lsa_short']}")
    print(f"tile overwrites between components: {len(r['overwrites'])}")
    for t, fg, fc, tg, tc in r["overwrites"]:
        print(f"   tile {t}: {n[fg]} (comp {fc}) -> {n[tg]} (comp {tc})")
    print("\nregion shortfalls by stage:")
    for i in range(r["G"]):
        if r["after_chain"][i] != cnt[i]:
            print(f"  {n[i]:24s} want {cnt[i]:3d}  solve {r['after_solve'][i]:3d}  "
                  f"ring {r['after_ring'][i]:3d}  chain {r['after_chain'][i]:3d}")
