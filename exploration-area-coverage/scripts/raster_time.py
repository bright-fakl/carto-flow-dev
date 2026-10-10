"""Rasterization time and mass conservation: center sampling vs supersampling vs exact coverage.

Usage: NUMBA_NUM_THREADS=4 uv run python raster_time.py [cases]   (run from the carto-flow worktree)
"""

import json
import sys
import time
import warnings
from pathlib import Path

import geopandas as gpd

import carto_flow.data as data
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries as f
from carto_flow.flow_cartogram.grid import Grid

warnings.filterwarnings("ignore")
SP = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/"
sets = {
    "states": lambda: (data.load_us_census(population=True).reset_index(drop=True), "Population"),
    "districts": lambda: (data.load_us_census(level="congressional_district").reset_index(drop=True), "Population"),
    "counties": lambda: (gpd.read_parquet(SP + "counties_prepared.parquet"), "total_votes"),
}
results = {}
cases = sys.argv[1].split(",") if len(sys.argv) > 1 else list(sets)
for name in cases:
    g, col = sets[name]()
    geoms = list(g.geometry)
    vals = g[col].to_numpy(float)
    for n in (128, 256, 512, 1024):
        grid = Grid.from_bounds(g.total_bounds, size=n, margin=0.5)
        out = []
        for cov in (None, 2, 4, 8, "exact"):
            best = 1e9
            for _ in range(3):
                t = time.perf_counter()
                r = f(geoms, vals, grid, coverage=cov)
                best = min(best, time.perf_counter() - t)
            results[f"{name}|{n}|{cov}"] = best
            mass = r.sum() * grid.dx * grid.dy / vals.sum()
            out.append(f"{cov}: {best:.3f}s mass={mass:.4f}")
        print(name, n, " | ".join(out), flush=True)

out = Path(__file__).resolve().parent.parent / "data" / "raster_time.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(results, indent=1))
