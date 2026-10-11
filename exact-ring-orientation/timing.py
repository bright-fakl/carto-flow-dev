"""Median time of one exact density field (ms); run it in a checkout of main and in one of the fix branch.

    NUMBA_NUM_THREADS=8 uv run python timing.py
"""

import time
import warnings

import numpy as np

from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries

warnings.filterwarnings("ignore")
STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
for name, gdf, n in (("states", STATES, 256), ("districts", DISTRICTS, 256), ("districts", DISTRICTS, 1024)):
    opts = MorphOptions(grid_size=n)
    grid = opts.get_grid(opts._calculate_bounds_from_geometries(gdf.geometry.values))
    geoms, values = list(gdf.geometry.values), gdf["Population"].values.astype(float)
    compute_density_field_from_geometries(geoms, values, grid, 1.0, rasterization="exact")
    t = []
    for _ in range(30):
        s = time.perf_counter()
        compute_density_field_from_geometries(geoms, values, grid, 1.0, rasterization="exact")
        t.append(time.perf_counter() - s)
    print(f"| {name}, {n} | {np.median(t) * 1000:.1f} |")
