"""Sweep of mosaic layout / Hungarian assignment options.

Reuses ``grid-vs-mosaic-similarity/metrics.py`` unchanged: every run is scored
with the same uniform metric set (displacement, adjacency, direction, spread,
combinatorial Polsby-Popper, silhouette, integrity).

Each result is appended to ``results.jsonl`` the moment it finishes.

Usage (from the repo root):

    PYTHONPATH=<checkout of origin/main>/src uv run python \
        visual_checks/mosaic-options-sweep/run.py [--cases a,b] [--knobs x,y]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "grid-vs-mosaic-similarity"))

import inputs as IN  # noqa: E402
from metrics import compute_metrics, extract_placement  # noqa: E402

RESULTS = HERE / "results.jsonl"

# ---------------------------------------------------------------- sweep spec

HUNG_DEFAULTS = dict(
    distance_weight=1.0,
    outside_penalty=1.0,
    interior_bonus=2.0,
    max_connectivity_iters=15,
    disconnected_penalty_mult=10.0,
    gap_bridge_mult=5.0,
    disconnected_score_weight=100,
    neighbor_weight=0.3,
    neighbor_bfs=False,
    swap_repair_passes=10,
    ring_swapback_max_hops=16,
)
LAYOUT_DEFAULTS = dict(spacing=0.0, extra_tile_rings=1, min_overlap_frac=0.1, tile_size=None)

HUNG_SWEEP = {
    "outside_penalty": [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 10.0],
    "max_connectivity_iters": [0, 1, 2, 5, 15, 30],
    "disconnected_penalty_mult": [0.0, 1.0, 2.0, 5.0, 10.0, 50.0],
    "gap_bridge_mult": [0.0, 1.0, 2.0, 5.0, 20.0],
    "disconnected_score_weight": [0, 1, 10, 100, 1000],
    "swap_repair_passes": [0, 1, 2, 5, 10, 30],
    "ring_swapback_max_hops": [0, 1, 2, 4, 8, 16, 32],
}
LAYOUT_SWEEP = {
    "extra_tile_rings": [0, 1, 2, 3, 5],
    "min_overlap_frac": [0.02, 0.1, 0.25, 0.5, 0.75, 1.0],
    "spacing": [0.0, 0.05, 0.2, 0.5],
}
# joint (distance_weight, outside_penalty) grid
JOINT = [(dw, op) for dw in (0.25, 1.0, 4.0) for op in (0.0, 0.5, 1.0, 2.0, 4.0)]
# explicit tile_size override, as a multiple of the calibrated size
TILE_SIZE_MULT = [0.8, 0.9, 1.0, 1.1, 1.25]


# ---------------------------------------------------------------- plumbing


def _json_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def append_result(rec: dict) -> None:
    with RESULTS.open("a") as f:
        f.write(json.dumps(rec, default=_json_default) + "\n")
        f.flush()


def fingerprint(result, n_regions: int) -> str:
    """Stable hash of the assignment: which tiles each region owns.

    Byte-identity across parameter values is the dead-zone test.
    """
    p = extract_placement(result, n_regions)
    payload = json.dumps(
        [sorted(int(t) for t in ts) for ts in p.tile_of_region] + [round(float(p.tile_size), 6)]
    )
    return hashlib.sha1(payload.encode()).hexdigest()[:16]


_MORPH_CACHE: dict = {}


def morph_reference(key, gdf, counts):
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


def run_one(case, gdf, ctx, *, morph, tiling, tile_count, group_by, hung, layout_kw, extra, morph_ref):
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

    name = extra["run"]
    print(f"[run] {name}", flush=True)
    t0 = time.perf_counter()
    try:
        layout = MosaicLayout(
            tiling=tiling,
            morph=morph,
            hungarian_options=HungarianOptions(**hung),
            **layout_kw,
        )
        res = create_layout(
            gdf, tile_count=tile_count, group_by=group_by, layout=layout, show_progress=False
        )
        elapsed = time.perf_counter() - t0
        m = compute_metrics(res, **ctx, **(morph_ref or {}))
        fp = fingerprint(res, len(gdf))
    except Exception:
        append_result({"error": traceback.format_exc(limit=4), **extra})
        print(f"[fail] {name}", flush=True)
        return None
    rec = {
        "wall_clock_s": elapsed,
        "fingerprint": fp,
        **extra,
        "opts": {**hung, **{k: v for k, v in layout_kw.items()}},
        **m,
    }
    append_result(rec)
    print(f"[done] {name} {elapsed:.1f}s fp={fp}", flush=True)
    return res


def sweep_case(case, *, morph, only_knobs=None):
    loader, tile_count, group_by, tiling = IN.CASES[case]
    gdf = loader()
    ctx = IN.input_context(gdf, tile_count=tile_count, group_by=group_by)
    counts = gdf[tile_count].to_numpy() if tile_count else np.ones(len(gdf))
    morph_ref = morph_reference(case, gdf, counts) if morph else None

    common = dict(
        tiling=tiling, tile_count=tile_count, group_by=group_by, morph=morph, morph_ref=morph_ref
    )
    base_extra = dict(case=case, morph=morph, tiling=tiling)

    def go(knob, value, hung_kw=None, layout_kw=None, label=None):
        hung = dict(HUNG_DEFAULTS)
        hung.update(hung_kw or {})
        lay = {k: v for k, v in LAYOUT_DEFAULTS.items()}
        lay.update(layout_kw or {})
        tag = label or f"{knob}={value}"
        extra = {
            **base_extra,
            "knob": knob,
            "value": value,
            "run": f"{case}__morph{int(morph)}__{tag}",
        }
        return run_one(
            case, gdf, ctx, hung=hung, layout_kw=lay, extra=extra, **common
        )

    want = (lambda k: True) if not only_knobs else (lambda k: k in only_knobs)

    # baseline (all defaults) -- reference point for every curve
    base_res = None
    if want("baseline"):
        base_res = go("baseline", None, label="baseline")

    for knob, values in HUNG_SWEEP.items():
        if not want(knob):
            continue
        for v in values:
            if v == HUNG_DEFAULTS[knob]:
                continue  # equals baseline
            go(knob, v, hung_kw={knob: v})

    if want("distance_x_outside"):
        for dw, op in JOINT:
            if dw == 1.0 and op == 1.0:
                continue
            go(
                "distance_x_outside",
                [dw, op],
                hung_kw={"distance_weight": dw, "outside_penalty": op},
                label=f"dw{dw}_op{op}",
            )

    for knob, values in LAYOUT_SWEEP.items():
        if not want(knob):
            continue
        for v in values:
            if v == LAYOUT_DEFAULTS[knob]:
                continue
            go(knob, v, layout_kw={knob: v})

    if want("tile_size"):
        # need the calibrated size: take it from a baseline run
        from carto_flow.symbol_cartogram import create_layout
        from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

        if base_res is None:
            base_res = create_layout(
                gdf,
                tile_count=tile_count,
                group_by=group_by,
                layout=MosaicLayout(tiling=tiling, morph=morph),
                show_progress=False,
            )
        calib = float(base_res.tiling_result.tile_size)
        for mult in TILE_SIZE_MULT:
            go("tile_size", mult, layout_kw={"tile_size": calib * mult}, label=f"tile_size_x{mult}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=",".join(IN.CASES))
    ap.add_argument("--knobs", default=None)
    ap.add_argument("--morph", default="1,0")
    args = ap.parse_args()
    knobs = set(args.knobs.split(",")) if args.knobs else None
    for case in args.cases.split(","):
        for m in args.morph.split(","):
            sweep_case(case, morph=bool(int(m)), only_knobs=knobs)
    print("[all done]", flush=True)


if __name__ == "__main__":
    main()
