"""Stage-by-stage diagnosis of where a region's tiles are lost in MosaicLayout.

Replicates MosaicLayout._compute up to the per-component Hungarian solve
(library code imported unchanged), then records, per component and per region:

  * demand  = sum of requested tile counts in the component
  * pool    = len(comp_tile_pools[c])  (core tiles + extra rings)
  * core    = core tiles won by the component
  * placed  = tiles actually assigned by the full layout

so a shortfall can be attributed to (a) an empty/short component pool,
(b) the rectangular linear_sum_assignment dropping slots, or (c) a later
post-process.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import wi_inputs as W  # noqa: E402


def build_stage_info(gdf, *, morph, tile_count="tiles", min_overlap_frac=0.1, extra_tile_rings=1):
    import shapely
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    from carto_flow.symbol_cartogram.layouts.data_prep import prepare_layout_data
    from carto_flow.symbol_cartogram.layouts.mosaic._calibration import calibrate_tiling
    from carto_flow.symbol_cartogram.tiling import resolve_tiling

    data = prepare_layout_data(gdf, tile_count=tile_count)
    geometries = list(data.source_gdf.geometry)
    G = len(geometries)
    counts = data.counts_G
    components = data.components
    target_count = len(data.positions)

    if morph:
        from carto_flow.flow_cartogram.algorithm import morph_geometries
        from carto_flow.flow_cartogram.options import MorphOptions

        res = morph_geometries(
            geometries, values=counts.astype(np.float64),
            options=MorphOptions(n_iter=100, show_progress=False),
        )
        working = list(res.latest.geometry)
    else:
        working = geometries
    working = [shapely.make_valid(g) for g in working]
    working_union = unary_union(working)

    comp_union_list = [unary_union([working[i] for i in idx]) for idx in components]
    comp_tree = STRtree(comp_union_list)

    tiling_obj = resolve_tiling("hexagon")
    setup = calibrate_tiling(
        tiling_obj, working_union.bounds, working_union, target_count,
        buffer_rings=extra_tile_rings, min_overlap_frac=min_overlap_frac,
    )
    tr = setup.tiling_result
    T = len(tr.polygons)
    tile_area = tr.polygons[0].area

    # --- component tile partition (verbatim logic from mosaic/__init__.py) ---
    n_components = len(components)
    tile_to_comp = np.full(T, -1, dtype=np.int32)
    for t in setup.valid_tile_indices:
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
    for t in setup.valid_tile_indices:
        pools[int(tile_to_comp[t])].append(t)
    core_counts = [len(p) for p in pools]
    if extra_tile_rings > 0:
        for c in range(n_components):
            ps = set(pools[c])
            for _ in range(extra_tile_rings):
                ps |= {nb for t in ps for nb in setup.adj_list[t] if nb not in ps}
            pools[c] = sorted(ps)

    # --- per-region geometry facts ---
    names = [str(x) for x in gdf["name"]] if "name" in gdf.columns else [str(i) for i in range(G)]
    comp_of = np.empty(G, dtype=int)
    for c, idx in enumerate(components):
        for i in idx:
            comp_of[i] = c

    # best overlap fraction any tile achieves with each region alone
    tree = shapely.STRtree(np.asarray(tr.polygons))
    best_frac = np.zeros(G)
    n_tiles_over_thresh = np.zeros(G, dtype=int)
    for g in range(G):
        cand = tree.query(working[g], predicate="intersects")
        if len(cand) == 0:
            continue
        polys = np.asarray(tr.polygons)[cand]
        inter = shapely.area(shapely.intersection(polys, working[g]))
        fr = inter / tile_area
        best_frac[g] = float(fr.max())
        n_tiles_over_thresh[g] = int((fr >= min_overlap_frac).sum())

    return dict(
        G=G, names=names, counts=counts.tolist(), comp_of=comp_of.tolist(),
        components=[list(map(int, c)) for c in components],
        tile_size=float(setup.tile_size), tile_area=float(tile_area),
        target_count=int(target_count),
        n_core=len(setup.valid_tile_indices),
        comp_demand=[int(counts[np.array(idx)].sum()) for idx in components],
        comp_core=core_counts,
        comp_pool=[len(p) for p in pools],
        area_morphed=[float(working[g].area) for g in range(G)],
        area_orig=[float(geometries[g].area) for g in range(G)],
        best_overlap_frac=best_frac.tolist(),
        n_tiles_over_thresh=n_tiles_over_thresh.tolist(),
    )


def run_layout(gdf, *, morph, tile_count="tiles", **hung):
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

    layout = MosaicLayout(morph=morph, hungarian_options=HungarianOptions(**hung))
    t0 = time.perf_counter()
    res = create_layout(gdf, tile_count=tile_count, layout=layout, show_progress=False)
    return res, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--budget", type=int, default=384)
    ap.add_argument("--morph", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.case == "world":
        gdf = W.load_world(a.budget)
    elif a.case == "africa":
        gdf = W.load_africa(a.budget)
    elif a.case == "world_mainland":
        gdf, _ = W.load_world_mainland(a.budget)
    else:
        raise SystemExit(f"unknown case {a.case}")

    info = build_stage_info(gdf, morph=bool(a.morph))
    res, elapsed = run_layout(gdf, morph=bool(a.morph))
    placed = res.regions_gdf["tile_count"].to_numpy().tolist()
    info["placed"] = placed
    info["wall_clock_s"] = elapsed
    am = res.metrics.algorithm
    info["metrics"] = dict(
        tile_size=am.tile_size, n_components=am.n_components,
        regions_correct=am.regions_correct, regions_total=am.regions_total,
        n_noncontiguous_regions=am.n_noncontiguous_regions,
        n_unassigned_core_tiles=am.n_unassigned_core_tiles,
        n_enclosed_unassigned_tiles=am.n_enclosed_unassigned_tiles,
        repair_passes=am.repair_passes,
    )
    info["case"] = a.case
    info["budget"] = a.budget
    info["morph"] = bool(a.morph)

    out = Path(a.out) if a.out else HERE / f"diag_{a.case}_{a.budget}_morph{a.morph}.json"
    out.write_text(json.dumps(info))
    print(f"wrote {out}")

    short = [(info["names"][g], info["counts"][g], placed[g]) for g in range(info["G"]) if placed[g] != info["counts"][g]]
    print(f"{a.case} budget={a.budget} morph={a.morph}: {elapsed:.1f}s  short={len(short)}  zero={sum(1 for s in short if s[2]==0)}")
    for n, c, p in sorted(short, key=lambda x: x[2]):
        g = info["names"].index(n)
        print(f"  {n:24s} want {c:3d} got {p:3d}  comp={info['comp_of'][g]:2d} "
              f"compdemand={info['comp_demand'][info['comp_of'][g]]:4d} compcore={info['comp_core'][info['comp_of'][g]]:4d} "
              f"comppool={info['comp_pool'][info['comp_of'][g]]:4d} bestfrac={info['best_overlap_frac'][g]:.3f} "
              f"ntiles>=thr={info['n_tiles_over_thresh'][g]}")


if __name__ == "__main__":
    main()
