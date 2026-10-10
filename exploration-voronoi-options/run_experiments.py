"""Screening runs for the Voronoi cartogram options (one factor at a time around three bases, plus pairs).

Writes one JSON line per run to data/runs.jsonl (runs already in the file are skipped, so the
script can be resumed). Datasets: S = 49 states with population, L = the same with lognormal
weights (seed 1, sigma 1.5), D = 432 congressional districts with population, U = 49 states
without weights (equal areas). Bases: F = fixed union outline, E = ElasticBoundary(0.05),
P = premorph=True (generator anchor 0.5). Every run: RasterBackend(resolution=256),
VoronoiOptions(n_iter=300, area_cv_tol=0.05) unless the factor changes it.

Run from a carto-flow checkout of feat/voronoi-premorph:
    NUMBA_NUM_THREADS=8 uv run python run_experiments.py [S,L,D,U]
"""

from __future__ import annotations

import json
import pickle
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import shapely
import shapely.affinity
from scipy.spatial import procrustes
from scipy.stats import spearmanr

import carto_flow.data as examples
import carto_flow.flow_cartogram as flow
import carto_flow.voronoi_cartogram as vor
from carto_flow.geo_utils.adjacency import find_adjacent_pairs

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "runs.jsonl"
CACHE = HERE / "data" / "cache"

BASES = {
    "F": {},
    "E": {"elastic": 0.05},
    "P": {"premorph": True},
}


def factor_levels(ds: str, base: str) -> list[tuple[str, str, dict]]:
    """(factor, level label, settings override) for one dataset and base."""
    weighted = ds != "U"
    out: list[tuple[str, str, dict]] = []
    anchors = [0.0, 0.25, 0.5, 1.0] if ds in "SLU" else [0.0, 0.25, 0.5, 1.0]
    if ds == "D" and base != "P":
        anchors = [0.5]
    if ds == "U" and base != "P":
        anchors = [0.5]
    for a in anchors:
        if base == "P" and a == 0.5:
            continue
        out.append(("anchor", f"{a:g}", {"anchor": a}))
    for s in ([0.1, 0.2, 0.4] if ds in "SL" else [0.2]):
        out.append(("adjacency_spring", f"{s:g}", {"spring": s}))
    if ds == "D":
        out.append(("intra_group_spring", "0.5 (+adj 0.1)", {"spring": 0.1, "intra": 0.5}))
    if not (ds == "D" and base == "E"):
        out.append(("fix_topology", "5", {"fix_topology": 5}))
    if ds != "D":
        out.append(("relaxation", "lloyd", {"relaxation": "lloyd"}))
    if weighted and not (ds == "D" and base == "E"):
        out.append(("prescale_components", "on", {"prescale": True}))
    if ds in "SL":
        for r in (0.05, 0.25):
            out.append(("area_equalizer_rate", f"{r:g}", {"rate": r}))
        for r in (0, 50):
            out.append(("weight_ramp_iters", f"{r}", {"ramp": r}))
    if ds == "U" and base == "F":
        for r in (0.0, 0.25):
            out.append(("area_equalizer_rate", f"{r:g}", {"rate": r}))
        for c in (0.0, 6.0):
            out.append(("cell_smoothing_px", f"{c:g}", {"smoothing": c}))
        out.append(("output_resolution", "512 (2x)", {"output_resolution": 512}))
        out.append(("distance_mode", "geodesic", {"geodesic": True}))
    if base in "FP":
        out.append(("stopping", "n_iter 30, no area_cv_tol (library default)", {"n_iter": 30, "area_cv_tol": None}))
    if not (ds == "D" and base == "E"):
        out.append(("resolution", "128", {"resolution": 128}))
    if ds == "S":
        out.append(("resolution", "512", {"resolution": 512}))
    # Boundary behavior
    if base == "F":
        out.append(("boundary", "adhesive 0.3", {"adhesive": 0.3}))
        if ds in "SU":
            for spec in ("convex_hull", "circle", "bbox"):
                out.append(("boundary", spec, {"spec": spec}))
        if ds == "S":
            out.append(("simplify_tol", "10 km", {"simplify": 10_000.0}))
    if base == "E" and ds != "D":
        out.append(("boundary", "elastic + adhesion 0.3", {"elastic_adhesion": 0.3}))
        for s in (0.02, 0.1):
            out.append(("boundary", f"elastic {s:g}", {"elastic": s}))
        if ds == "S":
            out.append(("density_smooth", "2", {"density_smooth": 2.0}))
    if base == "P":
        out.append(("boundary", "adhesive 0.3", {"adhesive": 0.3}))
        out.append(("boundary", "elastic 0.02", {"elastic": 0.02}))
    return out


def pair_levels(ds: str, base: str) -> list[tuple[str, str, dict]]:
    out: list[tuple[str, str, dict]] = []
    if ds in "SL" and base == "P":
        for a in (0.0, 1.0):
            for s in (0.2, 0.4):
                out.append(("anchor x spring", f"anchor {a:g}, spring {s:g}", {"anchor": a, "spring": s}))
        out.append(("anchor x fix_topology", "anchor 0, fix 5", {"anchor": 0.0, "fix_topology": 5}))
        out.append(("anchor x elastic", "anchor 0, elastic 0.02", {"anchor": 0.0, "elastic": 0.02}))
    if ds in "SL" and base == "E":
        out.append(("anchor x spring", "anchor 0.5, spring 0.2", {"anchor": 0.5, "spring": 0.2}))
        out.append(("anchor x adhesion", "anchor 0.5, adhesion 0.3", {"anchor": 0.5, "elastic_adhesion": 0.3}))
    if ds in "SL" and base == "F":
        out.append(("spring x fix_topology", "spring 0.2, fix 5", {"spring": 0.2, "fix_topology": 5}))
    if ds == "D" and base == "P":
        out.append(("anchor x spring", "anchor 0, spring 0.2", {"anchor": 0.0, "spring": 0.2}))
        out.append(("anchor x intra", "anchor 0, intra 0.5", {"anchor": 0.0, "spring": 0.1, "intra": 0.5}))
    return out


def repeats(ds: str, base: str) -> int:
    if ds == "S":
        return 3
    if (ds in "LD" and base == "P") or (ds == "U" and base == "E"):
        return 2
    return 1


# ----------------------------------------------------------------------------------------
# Data


def load(ds: str):
    us = examples.load_us_census(population=True)
    if ds == "S":
        return us, "Population (Millions)", None
    if ds == "L":
        u = us.copy()
        u["w"] = np.exp(np.random.default_rng(1).normal(0, 1.5, len(us)))
        return u, "w", None
    if ds == "U":
        u = us.copy()
        u["one"] = 1.0
        return u, "one", None
    d = examples.load_us_census(population=True, level="congressional_district")
    return d, "Population", "State Name"


def flow_reference(ds: str, gdf, col):
    """The flow-cartogram morph with the premorph defaults (cached)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"flow_{ds}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = flow.morph_gdf(gdf, col, options=flow.MorphOptions.preset_balanced().copy_with(n_iter=400, show_progress=False))
    geoms = shapely.make_valid(np.asarray(m.to_geodataframe().geometry, dtype=object))
    p.write_bytes(pickle.dumps(geoms))
    return geoms


def centroids(geoms):
    c = shapely.centroid(np.asarray(geoms, dtype=object))
    return np.column_stack([shapely.get_x(c), shapely.get_y(c)])


def to_frame(xy, outline, ref_outline):
    s = np.sqrt(ref_outline.area / outline.area)
    c, rc = outline.centroid, ref_outline.centroid
    return (xy - [c.x, c.y]) * s + [rc.x, rc.y]


def symdiff(g1, g2):
    k = np.sqrt(g2.area / g1.area)
    g1s = shapely.affinity.scale(g1, k, k, origin=g1.centroid)
    g1s = shapely.affinity.translate(g1s, g2.centroid.x - g1s.centroid.x, g2.centroid.y - g1s.centroid.y)
    return g1s.symmetric_difference(g2).area / g2.area


def pairset(geoms):
    return {(min(i, j), max(i, j)) for i, j, _ in find_adjacent_pairs(list(geoms))}


# ----------------------------------------------------------------------------------------
# One run


def build(settings: dict, ds: str, gdf, col, group_by):
    elastic = settings.get("elastic")
    if settings.get("elastic_adhesion") is not None:
        boundary = vor.ElasticBoundary(elastic or 0.05, adhesion_strength=settings["elastic_adhesion"])
    elif elastic:
        boundary = vor.ElasticBoundary(elastic, density_smooth=settings.get("density_smooth"))
    elif settings.get("adhesive"):
        boundary = vor.AdhesiveBoundary(settings["adhesive"])
    else:
        boundary = None
    backend_kw = dict(
        resolution=settings.get("resolution", 256),
        boundary=boundary,
        adjacency_spring=settings.get("spring", 0.0),
        intra_group_spring=settings.get("intra"),
        generator_anchor=settings.get("anchor"),
        relaxation=settings.get("relaxation", "overrelax"),
    )
    for key, arg in (("rate", "area_equalizer_rate"), ("ramp", "weight_ramp_iters"), ("smoothing", "cell_smoothing_px"),
                     ("output_resolution", "output_resolution")):
        if key in settings:
            backend_kw[arg] = settings[key]
    if settings.get("geodesic"):
        backend_kw["distance_mode"] = "geodesic"
    options = vor.VoronoiOptions(
        n_iter=settings.get("n_iter", 300), area_cv_tol=settings.get("area_cv_tol", 0.05), fix_topology=settings.get("fix_topology"),
        prescale_components=settings.get("prescale", False), simplify_tol=settings.get("simplify"),
    )
    kwargs = dict(
        weights=None if ds == "U" else col,
        backend=vor.RasterBackend(**backend_kw),
        options=options,
        boundary=settings.get("spec", "union"),
        premorph=settings.get("premorph"),
        group_by=group_by,
    )
    return kwargs


def run_one(ds, base, factor, level, settings, rep, ctx):
    gdf, col, group_by, ref = ctx["gdf"], ctx["col"], ctx["group_by"], ctx
    kwargs = build(settings, ds, gdf, col, group_by)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        t = time.perf_counter()
        r = vor.create_voronoi_cartogram(gdf, **kwargs)
        wall = time.perf_counter() - t
    cells = np.asarray(r.cells, dtype=object)
    n = len(cells)
    w = gdf[col].to_numpy(float)
    a = shapely.area(cells)
    err = np.abs(a / (w / w.sum() * a.sum()) - 1) * 100
    outline = r._field._current_boundary
    # Collapsed cells have no centroid; use their generator instead.
    empty = shapely.is_empty(cells) | (a <= 0.0)
    cc = centroids(np.where(empty, shapely.points(r.positions), cells))
    cc_o = to_frame(cc, outline, ref["orig_outline"])
    r0 = ref["r0"]
    d_orig = np.linalg.norm(cc_o - ref["orig_c"], axis=1) / r0
    d_flow = np.linalg.norm(cc_o - ref["flow_c_o"], axis=1) / r0
    _, _, disparity = procrustes(ref["orig_c"], cc)
    rank = 0.5 * (spearmanr(ref["orig_c"][:, 0], cc[:, 0]).correlation + spearmanr(ref["orig_c"][:, 1], cc[:, 1]).correlation)
    lag = np.linalg.norm(r.positions - cc, axis=1) / np.sqrt(np.maximum(a, 1e-300) / np.pi)
    compact = 4 * np.pi * a / np.maximum(shapely.length(cells), 1e-300) ** 2
    split = int(sum(1 for c in cells if c.geom_type == "MultiPolygon" and sorted(g.area for g in c.geoms)[-2] > 0.01 * c.area))
    cell_pairs = pairset(cells)
    orig_pairs = ref["orig_pairs"]
    tx = ref["tx"]
    tx_cell = shapely.union_all(cells[tx])
    tx_reg = ref["tx_flow"]
    return {
        "ds": ds, "base": base, "factor": factor, "level": level, "rep": rep, "settings": {k: v for k, v in settings.items()},
        "n": n, "mean_err": float(err.mean()), "max_err": float(err.max()),
        "d_flow_med": float(np.median(d_flow)), "d_flow_p90": float(np.percentile(d_flow, 90)), "d_flow_max": float(d_flow.max()),
        "d_orig_med": float(np.median(d_orig)), "procrustes": float(disparity), "rank": float(rank),
        "adj_kept": len(cell_pairs & orig_pairs) / len(orig_pairs), "adj_new": len(cell_pairs - orig_pairs),
        "compact": float(np.mean(compact)), "lag_med": float(np.median(lag)), "lag_max": float(lag.max()),
        "split": split, "invalid": int((~shapely.is_valid(cells)).sum()), "degenerate": len(r.degenerate_cells),
        "outline_vs_flow": symdiff(outline, ref["flow_outline"]), "outline_vs_orig": symdiff(outline, ref["orig_outline"]),
        "tx_own": float(tx_cell.intersection(tx_reg).area / tx_reg.area),
        "it": int(r.metrics["n_iterations"]), "time": wall, "converged": bool(r.metrics["converged"]),
        "warnings": sorted({f"{x.category.__name__}: {str(x.message)[:90]}" for x in caught}),
    }


def context(ds):
    gdf, col, group_by = load(ds)
    geoms = np.asarray(gdf.geometry, dtype=object)
    flow_geoms = flow_reference(ds, gdf, col)
    orig_outline = shapely.union_all(geoms)
    flow_outline = shapely.union_all(flow_geoms)
    tx = np.flatnonzero(gdf["State Abbreviation"].to_numpy() == "TX")
    return {
        "gdf": gdf, "col": col, "group_by": group_by,
        "orig_c": centroids(geoms), "orig_outline": orig_outline, "r0": np.sqrt(orig_outline.area / len(gdf)),
        "flow_outline": flow_outline, "flow_c_o": to_frame(centroids(flow_geoms), flow_outline, orig_outline),
        "orig_pairs": pairset(geoms), "tx": tx, "tx_flow": shapely.union_all(flow_geoms[tx]),
    }


def plan(ds):
    for base, settings in BASES.items():
        for rep in range(repeats(ds, base)):
            yield base, "base", "base", dict(settings), rep
        for factor, level, override in factor_levels(ds, base) + pair_levels(ds, base):
            yield base, factor, level, {**settings, **override}, 0


def main():
    which = sys.argv[1].split(",") if len(sys.argv) > 1 else ["S", "L", "U", "D"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            r = json.loads(line)
            done.add((r["ds"], r["base"], r["factor"], r["level"], r["rep"]))
    for ds in which:
        ctx = context(ds)
        for base, factor, level, settings, rep in plan(ds):
            key = (ds, base, factor, level, rep)
            if key in done:
                continue
            try:
                row = run_one(ds, base, factor, level, settings, rep, ctx)
            except Exception as exc:  # record failures instead of stopping the screen
                row = {"ds": ds, "base": base, "factor": factor, "level": level, "rep": rep, "settings": settings,
                       "error": f"{type(exc).__name__}: {exc}"[:300]}
            with OUT.open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(ds, base, factor, level, rep, "err" if "error" in row else f"{row['time']:.1f}s it {row['it']}", flush=True)


if __name__ == "__main__":
    main()
