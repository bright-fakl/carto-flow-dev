"""Stall parameters per level and an iteration budget for the multiresolution ladder.

    COUNTIES_PARQUET=counties_prepared.parquet NUMBA_NUM_THREADS=8 uv run python stall_levels.py [cases] [variants]

Each level is one CartogramWorkflow.morph pass on a grid of the ladder (levels run in a loop here so that every level can
have its own stall parameters). The stall window is patched through carto_flow.flow_cartogram.algorithm.cycle_length.
"""
import json
import math
import os
import sys
import time
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.flow_cartogram.algorithm as alg
from carto_flow import data
from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions
from carto_flow.flow_cartogram.grid import build_multilevel_grids

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
TOL = (0.01, 0.03)

STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
COUNTIES = gpd.read_parquet(os.environ["COUNTIES_PARQUET"]) if os.environ.get("COUNTIES_PARQUET") else None

RATIO = {  # cost of one field recompute in plain steps (preset-review), nearest lower grid
    "states": {64: 9, 128: 9, 256: 12, 512: 24, 1024: 71, 2048: 280},
    "districts": {64: 18, 128: 18, 256: 21, 512: 23, 1024: 47, 2048: 190},
    "counties": {64: 21, 128: 21, 256: 47.5, 512: 28.5, 1024: 60, 2048: 240},
}

COUNT = {"recomputes": 0}
_orig = alg.VelocityComputerFFTW.compute


def _counting(self, rho):
    COUNT["recomputes"] += 1
    return _orig(self, rho)


alg.VelocityComputerFFTW.compute = _counting
CYCLE = [10]
alg.cycle_length = lambda recompute_every: CYCLE[0]


def values(gdf, dist):
    rng = np.random.default_rng(0)
    a = gdf.geometry.area.to_numpy()
    if dist == "population":
        return gdf["Population"].to_numpy(float)
    if dist == "lognormal2":
        return rng.lognormal(0, 2, len(gdf))
    if dist == "area_like":
        return a * rng.lognormal(0, 0.2, len(gdf))
    if dist == "inverse_area":
        return a**-0.5 * rng.lognormal(0, 0.2, len(gdf))
    if dist == "smooth2":
        c = gdf.geometry.centroid
        xy = np.column_stack([c.x, c.y])
        scale = 0.15 * max(np.ptp(xy[:, 0]), np.ptp(xy[:, 1]))
        pts = rng.uniform(xy.min(0), xy.max(0), size=(40, 2))
        amp = rng.normal(size=40)
        f = (amp * np.exp(-((xy[:, None, :] - pts[None]) ** 2).sum(-1) / (2 * scale**2))).sum(1)
        return a * np.exp(2 * (f - f.mean()) / f.std())
    raise ValueError(dist)


# case: (input, distribution, coarsest, finest)
CASES = {
    "states-area": ("states", "area_like", 64, 256),
    "states-lognormal2": ("states", "lognormal2", 64, 256),
    "districts-smooth2": ("districts", "smooth2", 128, 512),
    "districts-inverse": ("districts", "inverse_area", 128, 512),
    "districts-pop64": ("districts", "population", 64, 512),
    "counties": ("counties", "votes", 512, 2048),
}
# variant: (window, patience, min_improvement) for the levels before the last, and the total iteration budget
BASE = (10, 4, 0.02)
VARIANTS = {
    "baseline": {"coarse": BASE, "budget": None},
    "cpp": {"coarse": (4, 1, 0.2), "budget": None},
    "p1-20": {"coarse": (10, 1, 0.2), "budget": None},
    "p2-10": {"coarse": (10, 2, 0.1), "budget": None},
    "budget": {"coarse": BASE, "budget": 600},
    "cpp+budget": {"coarse": (4, 1, 0.2), "budget": 600},
}
N_ITER = 500
FINAL_RESERVE = 150


def run(case, variant):
    kind, dist, start, fin = CASES[case]
    gdf = {"states": STATES, "districts": DISTRICTS, "counties": COUNTIES}[kind][["geometry"]].copy()
    if kind == "counties":
        gdf["v"] = COUNTIES["total_votes"].to_numpy(float)
        extra = {"area_scale": 1e-6}
    else:
        src = {"states": STATES, "districts": DISTRICTS}[kind]
        gdf["v"] = values(src, dist)
        extra = {}
    v = VARIANTS[variant]
    levels = int(math.log2(fin // start)) + 1
    grids = build_multilevel_grids(gdf.total_bounds, start, levels, margin=0.5, square=True)
    wf = CartogramWorkflow(gdf, "v", options=MorphOptions(show_progress=False, mean_tol=TOL[0], max_tol=TOL[1], **extra))
    COUNT["recomputes"] = 0
    t = time.perf_counter()
    remaining = v["budget"]
    per_level = []
    for i, g in enumerate(grids):
        last = i == levels - 1
        window, patience, imp = BASE if last else v["coarse"]
        n_iter = N_ITER
        if remaining is not None:
            n_iter = max(min(N_ITER, remaining - (0 if last else FINAL_RESERVE)), 10)
        CYCLE[0] = window
        o = MorphOptions(show_progress=False, mean_tol=TOL[0], max_tol=TOL[1], n_iter=n_iter, recompute_every=min(10, n_iter),
                         stall_patience=patience, stall_min_improvement=imp, grid=g, prescale_components=(i == 0), **extra)
        r = wf.morph(options=o)
        per_level.append((int(g.sx), r.status.value, int(r.niterations)))
        if remaining is not None:
            remaining -= r.niterations
        if r.status.value == "converged":
            break
    wall = time.perf_counter() - t
    geoms = list(wf.last.get_geometry())
    a = np.array([x.area for x in geoms])
    err = np.abs(a / (gdf["v"].to_numpy(float) / gdf["v"].sum() * a.sum()) - 1) * 100
    iters = sum(p[2] for p in per_level)
    ratio = RATIO[kind]
    cost = iters + sum(0 for _ in [0])  # recomputes are counted in total below, weighted by the grid of the last level run
    cost = iters + COUNT["recomputes"] * ratio[per_level[-1][0]]
    return {"case": case, "variant": variant, "levels": per_level, "iterations": iters, "recomputes": COUNT["recomputes"],
            "cost": cost, "wall": wall, "status": wf.last.status.value, "true_mean": float(err.mean()),
            "true_max": float(err.max()), "invalid": int((~shapely.is_valid(np.array(geoms, dtype=object))).sum())}


if __name__ == "__main__":
    cases = sys.argv[1].split(",") if len(sys.argv) > 1 else [c for c in CASES if c != "counties" or COUNTIES is not None]
    variants = sys.argv[2].split(",") if len(sys.argv) > 2 else list(VARIANTS)
    rows = []
    for c in cases:
        for vname in variants:
            r = run(c, vname)
            rows.append(r)
            print(f"{c:18s} {vname:11s} {r['status']:9s} it {r['iterations']:5d} rc {r['recomputes']:4d} cost {r['cost']:8.0f} {r['wall']:6.1f}s mean {r['true_mean']:7.2f} max {r['true_max']:8.1f} inv {r['invalid']:3d} {r['levels']}", flush=True)
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / f"stall_{'_'.join(cases)}.json").write_text(json.dumps(rows))
