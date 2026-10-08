"""Evaluate linear vs squared distance normalisation in the mosaic cost matrix.

`_build_cost_matrix` normalises the SQUARED centroid distance by the maximum
SQUARED distance, while `outside_frac` and `connectivity` are linear fractions.
All three land in [0, 1] -- which is the stated design intent -- but the
distance term's distribution is quadratic, so a tile at fraction f of the
maximum distance costs f**2 rather than f.

The variant under test changes that one expression to linear distance over the
maximum linear distance.  It is applied by monkeypatching `_build_cost_matrix`
with a verbatim copy carrying the one changed line, so nothing in the library
is modified and both variants run against the same checkout.

Every record is appended to results.jsonl the moment it finishes.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))
sys.path.insert(0, str(HERE.parent / "grid-vs-mosaic-similarity"))
sys.path.insert(0, str(HERE.parent / "mosaic-world-islands"))

import inputs as IN  # noqa: E402
import wi_inputs as WI  # noqa: E402
from metrics import compute_metrics  # noqa: E402

RESULTS = HERE / "results.jsonl"


# --------------------------------------------------------------- the variant


def _linear_build_cost_matrix(
    tiling_result, geometries, counts, valid_tile_indices, adj_list, working_union,
    *, distance_weight, outside_penalty, interior_bonus,
):
    """`_build_cost_matrix` with linear distance normalisation.

    Verbatim copy of the library function except for the two marked lines.
    """
    import shapely as _shapely

    G = len(geometries)
    valid_set = set(valid_tile_indices)

    tile_polys = [tiling_result.polygons[t] for t in valid_tile_indices]
    tile_area = tile_polys[0].area

    geom_centroids = np.array([[g.centroid.x, g.centroid.y] for g in geometries], dtype=np.float64)
    tile_centroids = np.array([[p.centroid.x, p.centroid.y] for p in tile_polys], dtype=np.float64)

    dx = tile_centroids[:, 0][None, :] - geom_centroids[:, 0][:, None]
    dy = tile_centroids[:, 1][None, :] - geom_centroids[:, 1][:, None]
    dist_matrix = np.sqrt(dx**2 + dy**2)          # <-- linear, not squared
    max_dist = dist_matrix.max() or 1.0           # <-- max linear distance
    dist_norm = dist_matrix / max_dist

    tile_inside_area = _shapely.area(_shapely.intersection(np.asarray(tile_polys), working_union))
    tile_inside_area = np.where(tile_inside_area > 1e-12, tile_inside_area, tile_area)
    outside_frac = 1.0 - tile_inside_area / tile_area

    connectivity = np.array(
        [sum(1 for nb in adj_list[t] if nb in valid_set) / max(len(adj_list[t]), 1) for t in valid_tile_indices],
        dtype=np.float64,
    )

    cost_G = (
        distance_weight * dist_norm + outside_penalty * outside_frac[None, :] - interior_bonus * connectivity[None, :]
    )

    slot_to_geom: list[int] = []
    for g in range(G):
        slot_to_geom.extend([g] * int(counts[g]))

    cost = cost_G[slot_to_geom, :]
    return cost_G, cost, slot_to_geom, connectivity


# --------------------------------------------------------------- plumbing


def _default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def append(rec):
    with RESULTS.open("a") as f:
        f.write(json.dumps(rec, default=_default) + "\n")
        f.flush()


CASES = {
    "states_uniform": (IN.load_states, None, None, "hexagon"),
    "states_uniform_sq": (IN.load_states, None, None, "square"),
    "states": (IN.load_states, "tiles", None, "hexagon"),
    "districts": (IN.load_districts, None, "State Name", "hexagon"),
    "world": (lambda: WI.load_world(384), "tiles", None, "hexagon"),
    "africa": (lambda: WI.load_africa(150), "tiles", None, "hexagon"),
    "world_mainland": (lambda: WI.load_world_mainland(384)[0], "tiles", None, "hexagon"),
}


def owner_displacement(result, gdf):
    """Distance from each placed tile to the centroid of the region owning it.

    The statistic the normalisation change targets most directly: how far a
    symbol ends up from the land it represents.  Reported in km and in tiles.
    """
    tg = result.tiles_gdf
    if len(tg) == 0:
        return {}
    gc = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
    cent = np.array([[p.centroid.x, p.centroid.y] for p in tg.geometry])
    gid = tg["geometry_id"].to_numpy().astype(int)
    ok = gid >= 0
    d = np.hypot(cent[ok, 0] - gc[gid[ok], 0], cent[ok, 1] - gc[gid[ok], 1])
    ts = float(result.metrics.algorithm.tile_size)
    return {
        "median_m": float(np.median(d)), "p90_m": float(np.percentile(d, 90)),
        "max_m": float(d.max()), "mean_m": float(d.mean()),
        "median_tiles": float(np.median(d) / ts), "p90_tiles": float(np.percentile(d, 90) / ts),
        "max_tiles": float(d.max() / ts),
    }


_MORPH_CACHE: dict = {}


def morph_reference(key, gdf, counts):
    if key in _MORPH_CACHE:
        return _MORPH_CACHE[key]
    import shapely
    from shapely.ops import unary_union

    from carto_flow.flow_cartogram.algorithm import morph_geometries
    from carto_flow.flow_cartogram.options import MorphOptions

    res = morph_geometries(list(gdf.geometry), values=np.asarray(counts, dtype=np.float64),
                           options=MorphOptions(n_iter=100, show_progress=False))
    morphed = [shapely.make_valid(g) for g in res.latest.geometry]
    ref = {"working_union": unary_union(morphed),
           "working_centroids": np.array([[g.centroid.x, g.centroid.y] for g in morphed])}
    _MORPH_CACHE[key] = ref
    return ref


def run_one(case, gdf, ctx, *, variant, morph, tiling, tile_count, group_by,
            distance_weight, interior_bonus, morph_ref, label, min_one_tile=False):
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout
    from carto_flow.symbol_cartogram.layouts.mosaic import _assignment as M

    original = M._build_cost_matrix
    if variant == "linear":
        M._build_cost_matrix = _linear_build_cost_matrix
    try:
        t0 = time.perf_counter()
        layout = MosaicLayout(
            tiling=tiling, morph=morph, min_one_tile_per_region=min_one_tile,
            hungarian_options=HungarianOptions(distance_weight=distance_weight, interior_bonus=interior_bonus),
        )
        res = create_layout(gdf, tile_count=tile_count, group_by=group_by, layout=layout, show_progress=False)
        elapsed = time.perf_counter() - t0
    finally:
        M._build_cost_matrix = original

    m = compute_metrics(res, **ctx, **(morph_ref or {}))
    rec = dict(label=label, case=case, variant=variant, morph=morph, tiling_name=tiling,
               distance_weight=distance_weight, interior_bonus=interior_bonus,
               min_one_tile=min_one_tile, wall_clock_s=elapsed, owner_displacement=owner_displacement(res, gdf), **m)
    append(rec)
    d = m["displacement"]; i = m["integrity"]; od = rec["owner_displacement"]
    print(f"[done] {label} {elapsed:5.1f}s  disp_tiles={d['median_tiles']:.2f}  "
          f"owner_km={od.get('median_m', 0) / 1000:.0f}  adj={m['adjacency']['frac_edge_adjacent']:.3f}  "
          f"iou={m['silhouette']['iou_aligned'] if m.get('silhouette') else float('nan'):.3f}  "
          f"noncontig={i['n_noncontiguous_regions']}  split={i.get('n_split_groups', 0)}  "
          f"short={i['regions_total'] - i['regions_correct']}  missing={i['n_regions_missing_tiles']}",
          flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=",".join(CASES))
    ap.add_argument("--morphs", default="1,0")
    ap.add_argument("--variants", default="squared,linear")
    ap.add_argument("--weights", default="1.0")
    ap.add_argument("--interior", default="2.0")
    ap.add_argument("--min-one-tile", dest="min_one_tile", default="0")
    a = ap.parse_args()

    for case in a.cases.split(","):
        loader, tile_count, group_by, tiling = CASES[case]
        gdf = loader()
        counts = gdf[tile_count].to_numpy() if tile_count else np.ones(len(gdf))
        ctx = IN.input_context(gdf, tile_count=tile_count, group_by=group_by)
        for morph in [bool(int(x)) for x in a.morphs.split(",")]:
            ref = morph_reference(case, gdf, counts) if morph else None
            for variant in a.variants.split(","):
                for dw in [float(x) for x in a.weights.split(",")]:
                    for ib in [float(x) for x in a.interior.split(",")]:
                      for m1 in [bool(int(x)) for x in a.min_one_tile.split(",")]:
                        label = f"{case}__morph{int(morph)}__{variant}__dw{dw}__ib{ib}__m1{int(m1)}"
                        try:
                            run_one(case, gdf, ctx, variant=variant, morph=morph, tiling=tiling,
                                    tile_count=tile_count, group_by=group_by, distance_weight=dw,
                                    interior_bonus=ib, morph_ref=ref, label=label, min_one_tile=m1)
                        except Exception:
                            append(dict(label=label, case=case, variant=variant, morph=morph,
                                        distance_weight=dw, interior_bonus=ib, min_one_tile=m1,
                                        error=traceback.format_exc(limit=4)))
                            print(f"[fail] {label}", flush=True)


if __name__ == "__main__":
    main()
