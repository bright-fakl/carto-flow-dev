"""Grid vs mosaic layout measurement harness.

Runs both layouts on the same inputs, computes one uniform metric set
(``metrics.compute_metrics``) for every run, and appends each result to
``results.jsonl`` as soon as it finishes, so a partial run still leaves data
on disk.

Three inputs:

* ``states_uniform`` -- 49 US states, no ``size``/``tile_count``/``group_by``:
  one tile per region.  This is the gallery case
  (``docs/examples/plot_symbol_cartogram.py``) and what the ``tile_map_cartogram``
  (hexagon) and ``demers_cartogram`` (square) presets produce.
* ``states`` -- the same 49 states with ``tile_count="tiles"`` (~154 tiles).
* ``districts`` -- 432 congressional districts with ``group_by="State Name"``.

Usage (from the repo root, with origin/main sources on the path):

    PYTHONPATH=<checkout of origin/main>/src uv run python \
        visual_checks/grid-vs-mosaic-similarity/run.py [--only ...]
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from metrics import build_study_union, compute_metrics, extract_placement  # noqa: E402

RESULTS = HERE / "results.jsonl"
PLACEMENTS = HERE / "placements"

N_TILES_STATES = 150


# ---------------------------------------------------------------- inputs


def load_inputs():
    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * N_TILES_STATES)).astype(int)

    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    return states, districts


def input_context(gdf, *, tile_count=None, group_by=None):
    from carto_flow.symbol_cartogram.adjacency import compute_adjacency
    from carto_flow.symbol_cartogram.options import AdjacencyMode

    cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
    adj = compute_adjacency(gdf, mode=AdjacencyMode.BINARY)
    if tile_count is not None:
        req = gdf[tile_count].to_numpy(dtype=int)
    else:
        req = np.ones(len(gdf), dtype=int)
    groups = None
    if group_by is not None:
        _, groups = np.unique(gdf[group_by].to_numpy(), return_inverse=True)
    return {
        "orig_centroids": cent,
        "adjacency_G": adj,
        "requested_counts": req,
        "input_bounds": tuple(float(x) for x in gdf.total_bounds),
        "group_labels": groups,
        "study_union": build_study_union(gdf),
    }


# ------------------------------------------------- morphed reference footprint


_MORPH_CACHE: dict = {}


def morph_reference(key, gdf, counts):
    """Reproduce the footprint MosaicLayout(morph=True) actually tiles against.

    ``MosaicLayout`` builds ``working_union`` from the flow-morphed geometries
    (``mosaic/__init__.py`` step 1) and never stores them on the result, so the
    only way to get the morphed union and the morphed centroids is to run the
    same morph with the same arguments: the source geometries, ``counts`` as
    values, and ``MorphOptions(n_iter=100, show_progress=False)`` -- the default
    the layout constructs when ``morph_options`` is None.  The repeat check
    found mosaic's morph=True metrics identical across runs, so reproducing it
    here is sound; if that ever stops holding, these reference numbers stop
    being exact.
    """
    if key in _MORPH_CACHE:
        return _MORPH_CACHE[key]
    import shapely
    from shapely.ops import unary_union

    from carto_flow.flow_cartogram.algorithm import morph_geometries
    from carto_flow.flow_cartogram.options import MorphOptions

    res = morph_geometries(
        list(gdf.geometry),
        values=np.asarray(counts, dtype=np.float64),
        options=MorphOptions(n_iter=100, show_progress=False),
    )
    morphed = [shapely.make_valid(g) for g in res.latest.geometry]
    ref = {
        "working_union": unary_union(morphed),
        "working_centroids": np.array([[g.centroid.x, g.centroid.y] for g in morphed]),
    }
    _MORPH_CACHE[key] = ref
    return ref


# ---------------------------------------------------------------- runner


def append_result(rec: dict) -> None:
    with RESULTS.open("a") as f:
        f.write(json.dumps(rec, default=_json_default) + "\n")
        f.flush()


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def save_placement(name: str, result, gdf) -> None:
    """Store just what the figure script needs (assigned tile polygons)."""
    PLACEMENTS.mkdir(exist_ok=True)
    p = extract_placement(result, len(gdf))
    polys = result.tiling_result.polygons
    assigned = set(p.region_of_tile)
    # lattice edge-adjacency restricted to assigned tiles, so figures use the
    # same adjacency the metrics do (not a geometric touch test)
    nbrs = {int(t): [int(u) for u in np.flatnonzero(p.tile_adj[t]) if int(u) in assigned] for t in assigned}
    payload = {
        "tile_of_region": p.tile_of_region,
        "polygons": {int(t): polys[t] for t in assigned},
        "neighbours": nbrs,
        "tile_size": p.tile_size,
    }
    with (PLACEMENTS / f"{name}.pkl").open("wb") as f:
        pickle.dump(payload, f)


def run_one(
    name, gdf, ctx, *, layout, tile_count=None, group_by=None, keep_placement=False, extra=None, morph_ref=None
):
    from carto_flow.symbol_cartogram import create_layout

    print(f"[run] {name}", flush=True)
    t0 = time.perf_counter()
    try:
        res = create_layout(
            gdf,
            tile_count=tile_count,
            group_by=group_by,
            layout=layout,
            show_progress=False,
        )
        elapsed = time.perf_counter() - t0
        m = compute_metrics(res, **ctx, **(morph_ref or {}))
    except Exception:
        append_result({"name": name, "error": traceback.format_exc(limit=3), **(extra or {})})
        print(f"[fail] {name}", flush=True)
        return None
    rec = {"name": name, "wall_clock_s": elapsed, **(extra or {}), **m}
    append_result(rec)
    if keep_placement:
        save_placement(name, res, gdf)
    print(f"[done] {name} in {elapsed:.1f}s", flush=True)
    return rec


def trio(case, gdf, ctx, *, tiling="hexagon", tile_count=None, group_by=None, suffix="", morph_ref=None):
    """grid + mosaic(morph=True) x3 + mosaic(morph=False) for one input/tiling."""
    from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
    from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

    common = dict(tile_count=tile_count, group_by=group_by)
    base = {"input": case, "tiling": tiling}
    run_one(
        f"{case}{suffix}__grid",
        gdf,
        ctx,
        layout=GridBasedLayout(tiling=tiling),
        keep_placement=True,
        extra={**base, "layout": "grid", "morph": None, "rep": 0},
        **common,
    )
    for rep in range(3):
        run_one(
            f"{case}{suffix}__mosaic_morph__rep{rep}",
            gdf,
            ctx,
            layout=MosaicLayout(tiling=tiling, morph=True),
            keep_placement=(rep == 0),
            extra={**base, "layout": "mosaic", "morph": True, "rep": rep},
            morph_ref=morph_ref,
            **common,
        )
    run_one(
        f"{case}{suffix}__mosaic_nomorph",
        gdf,
        ctx,
        layout=MosaicLayout(tiling=tiling, morph=False),
        keep_placement=True,
        extra={**base, "layout": "mosaic", "morph": False, "rep": 0},
        **common,
    )


# ---------------------------------------------------------------- cases


def uniform(states):
    """Primary case: 49 states, one tile per region, hexagon and square."""
    ctx = input_context(states)
    ref = morph_reference("states_uniform", states, np.ones(len(states)))
    trio("states_uniform", states, ctx, tiling="hexagon", morph_ref=ref)
    trio("states_uniform", states, ctx, tiling="square", suffix="_sq", morph_ref=ref)


def comparison(states, districts):
    ctx_s = input_context(states, tile_count="tiles")
    trio(
        "states",
        states,
        ctx_s,
        tiling="hexagon",
        tile_count="tiles",
        morph_ref=morph_reference("states", states, states["tiles"].to_numpy()),
    )
    ctx_d = input_context(districts, group_by="State Name")
    trio(
        "districts",
        districts,
        ctx_d,
        tiling="hexagon",
        group_by="State Name",
        morph_ref=morph_reference("districts", districts, np.ones(len(districts))),
    )


SWEEP = {
    "origin_weight": [0.0, 0.5, 1.0, 2.0, 5.0, 20.0, 100.0],
    "neighbor_weight": [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 20.0],
    "topology_weight": [0.0, 0.5, 1.0, 2.0, 5.0],
    "compactness": [0.0, 0.1, 0.5, 1.0, 2.0],
}
DEFAULTS = {"origin_weight": 0.5, "neighbor_weight": 0.5, "topology_weight": 0.5, "compactness": 0.1}


def sweep(case, gdf, ctx, *, tile_count=None, tiling="hexagon"):
    from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout

    for knob, values in SWEEP.items():
        for v in values:
            kw = dict(DEFAULTS)
            kw[knob] = v
            run_one(
                f"sweep__{case}__{knob}__{v}",
                gdf,
                ctx,
                layout=GridBasedLayout(tiling=tiling, **kw),
                tile_count=tile_count,
                keep_placement=False,
                extra={
                    "input": case,
                    "layout": "grid",
                    "tiling": tiling,
                    "sweep_case": case,
                    "sweep_knob": knob,
                    "sweep_value": v,
                    **kw,
                },
            )


# ---------------------------------------------------------------- mosaic sweep

MOSAIC_SWEEP = {
    "neighbor_bfs": [False, True],
    "neighbor_weight": [0.0, 0.05, 0.1, 0.2, 0.3, 0.6, 1.0, 2.0, 5.0],
    "distance_weight": [0.25, 0.5, 1.0, 2.0, 4.0],
    "interior_bonus": [0.0, 0.25, 0.5, 1.0, 2.0],
}
MOSAIC_DEFAULTS = {
    "distance_weight": 1.0,
    "interior_bonus": 0.5,
    "neighbor_weight": 0.3,
    "neighbor_bfs": False,
}
# neighbor_bfs=True crossed with the neighbour-weight range: the two interact
MOSAIC_COMBO = [
    {"neighbor_bfs": True, "neighbor_weight": w} for w in MOSAIC_SWEEP["neighbor_weight"]
]


def _mosaic_case(case):
    """(gdf-key, tile_count, group_by) for a case name."""
    return {
        "states_uniform": (None, None),
        "states": ("tiles", None),
        "districts": (None, "State Name"),
    }[case]


def mosaic_sweep(case, gdf, ctx, *, morph=True, tiling="hexagon", morph_ref=None):
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

    tile_count, group_by = _mosaic_case(case)
    tag = "" if morph else "_nomorph"

    def go(label, kw):
        opts = dict(MOSAIC_DEFAULTS)
        opts.update(kw)
        run_one(
            f"msweep{tag}__{case}__{label}",
            gdf,
            ctx,
            layout=MosaicLayout(tiling=tiling, morph=morph, hungarian_options=HungarianOptions(**opts)),
            tile_count=tile_count,
            group_by=group_by,
            keep_placement=False,
            morph_ref=morph_ref if morph else None,
            extra={
                "input": case,
                "layout": "mosaic",
                "morph": morph,
                "tiling": tiling,
                "msweep_case": case,
                "msweep_label": label,
                **opts,
            },
        )

    for knob, values in MOSAIC_SWEEP.items():
        for v in values:
            go(f"{knob}__{v}", {knob: v})
    for kw in MOSAIC_COMBO:
        go(f"bfs_x_nw__{kw['neighbor_weight']}", kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        choices=[
            "uniform",
            "comparison",
            "sweep",
            "sweep_uniform",
            "placements",
            "mosaic_sweep",
        ],
        default=None,
    )
    args = ap.parse_args()

    if args.only == "placements":
        # re-run only the figure configurations; metric records go to a
        # scratch file so results.jsonl is not duplicated
        global RESULTS
        RESULTS = HERE / "results_placements_rerun.jsonl"

    states, districts = load_inputs()
    print(f"states={len(states)} tiles={int(states['tiles'].sum())} districts={len(districts)}", flush=True)

    if args.only in (None, "uniform", "placements"):
        uniform(states)
    if args.only in (None, "comparison", "placements"):
        comparison(states, districts)
    if args.only in (None, "sweep_uniform"):
        sweep("states_uniform", states, input_context(states))
    if args.only in (None, "sweep"):
        sweep("states", states, input_context(states, tile_count="tiles"), tile_count="tiles")
    if args.only in (None, "mosaic_sweep"):
        mosaic_sweep(
            "states_uniform",
            states,
            input_context(states),
            morph_ref=morph_reference("states_uniform", states, np.ones(len(states))),
        )
        mosaic_sweep(
            "states",
            states,
            input_context(states, tile_count="tiles"),
            morph_ref=morph_reference("states", states, states["tiles"].to_numpy()),
        )
        mosaic_sweep(
            "districts",
            districts,
            input_context(districts, group_by="State Name"),
            morph_ref=morph_reference("districts", districts, np.ones(len(districts))),
        )
    print("[all done]", flush=True)


if __name__ == "__main__":
    main()
