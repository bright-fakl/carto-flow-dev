"""Shared helpers for the preset review: datasets, one measured run, cost model."""

from __future__ import annotations

import os
import time
import warnings

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.flow_cartogram.algorithm as alg
from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf

warnings.filterwarnings("ignore")

STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
_COUNTIES = os.environ.get("COUNTIES_PARQUET")
COUNTIES = gpd.read_parquet(_COUNTIES) if _COUNTIES else None
INPUTS = {"states": (STATES, "Population", {}), "districts": (DISTRICTS, "Population", {})}
if COUNTIES is not None:
    INPUTS["counties"] = (COUNTIES, "total_votes", {"area_scale": 1e-6})

# Cost of one field recompute in plain steps (adaptive-recompute-experiment, exploration-default-dt): states 9/12/24/71 at
# grids 128/256/512/1024, districts 18/21/23/47, counties 21/47.5/28.5 (grids 128/256/512).
RATIO = {
    "states": {128: 9.0, 256: 12.0, 512: 24.0, 1024: 71.0},
    "districts": {128: 18.0, 256: 21.0, 512: 23.0, 1024: 47.0},
    "counties": {128: 21.0, 256: 47.5, 512: 28.5, 1024: 60.0},
}

COUNT = {"recomputes": 0}
_orig_compute = alg.VelocityComputerFFTW.compute


def _counting_compute(self, rho):
    COUNT["recomputes"] += 1
    return _orig_compute(self, rho)


alg.VelocityComputerFFTW.compute = _counting_compute


def true_errors(geoms, values):
    a = np.array([g.area for g in geoms])
    return np.abs(a / (np.asarray(values, float) / np.sum(values) * a.sum()) - 1) * 100


def run(name, options, repeats=1):
    """One measured run (wall time: minimum over `repeats`); options already include the preset."""
    gdf, col, extra = INPUTS[name]
    opts = options.copy_with(show_progress=False, **extra)
    best_wall = None
    for _ in range(repeats):
        COUNT["recomputes"] = 0
        t = time.perf_counter()
        r = morph_gdf(gdf, col, options=opts)
        wall = time.perf_counter() - t
        best_wall = wall if best_wall is None else min(best_wall, wall)
    geoms = list(r.get_geometry())
    e = true_errors(geoms, gdf[col].values)
    rep = r.get_errors()
    grid = opts.grid_size if isinstance(opts.grid_size, int) else 256
    return {
        "input": name, "status": r.status.value, "it": int(r.niterations), "recomputes": COUNT["recomputes"],
        "cost": r.niterations + COUNT["recomputes"] * RATIO[name].get(grid, 20.0),
        "wall": best_wall, "reported_mean": float(rep.mean_error_pct), "reported_max": float(rep.max_error_pct),
        "true_mean": float(e.mean()), "true_max": float(e.max()),
        "invalid": int((~shapely.is_valid(np.array(geoms, dtype=object))).sum()), "grid": grid,
    }


def fmt(r):
    return (f"{r['status']}, {r['it']} it, {r['recomputes']} rc, cost {r['cost']:.0f}, {r['wall']:.2f} s | "
            f"mean {r['true_mean']:.2f} % max {r['true_max']:.1f} % | invalid {r['invalid']}")
