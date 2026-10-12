"""Effect of the starting resolution of a multiresolution morph (final grid fixed at 1024 unless converged earlier).

    COUNTIES_PARQUET=counties_prepared.parquet NUMBA_NUM_THREADS=8 uv run python start_resolution.py [inputs] [tol]
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

from carto_flow import data
from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions
from carto_flow.flow_cartogram.grid import build_multilevel_grids

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
INPUTS = {
    "states": (data.load_us_census(population=True).reset_index(drop=True), "Population", {}),
    "districts": (data.load_us_census(population=True, level="congressional_district").reset_index(drop=True), "Population", {}),
}
if os.environ.get("COUNTIES_PARQUET"):
    INPUTS["counties"] = (gpd.read_parquet(os.environ["COUNTIES_PARQUET"]), "total_votes", {"area_scale": 1e-6})
TOLS = {"loose": (0.10, 0.30), "default": (0.05, 0.10), "tight": (0.01, 0.03), "vtight": (0.005, 0.01)}
FINAL = int(os.environ.get("FINAL", 1024))
STARTS = [int(s) for s in os.environ.get("STARTS", "64,128,256,512,1024").split(",")]


def run(name, start, tol):
    gdf, col, extra = INPUTS[name]
    levels = int(math.log2(FINAL // start)) + 1
    mean_tol, max_tol = TOLS[tol]
    opts = MorphOptions(show_progress=False, mean_tol=mean_tol, max_tol=max_tol, **extra)
    grids = build_multilevel_grids(gdf.total_bounds, start, levels, margin=0.5, square=True)
    cell = grids[0].dx * grids[0].dy
    target = gdf[col].to_numpy(float) / gdf[col].sum() * gdf.geometry.area.sum()
    sub0 = float((target < cell).mean() * 100)
    wf = CartogramWorkflow(gdf, col, options=opts)
    t = time.perf_counter()
    wf.morph_multiresolution(min_resolution=start, levels=levels, options=opts)
    wall = time.perf_counter() - t
    res = wf.results[1:]
    geoms = list(wf.last.get_geometry())
    a = np.array([g.area for g in geoms])
    err = np.abs(a / (gdf[col].to_numpy(float) / gdf[col].sum() * a.sum()) - 1) * 100
    return {
        "input": name, "tol": tol, "start": start, "sub_cell_pct_at_start": sub0,
        "levels_run": [(int(r.options.grid.sx), r.status.value, int(r.niterations)) for r in res],
        "iterations": int(sum(r.niterations for r in res)), "wall": wall,
        "true_mean": float(err.mean()), "true_max": float(err.max()),
        "invalid": int((~shapely.is_valid(np.array(geoms, dtype=object))).sum()),
        "reported_status": wf.last.status.value,
    }


if __name__ == "__main__":
    names = sys.argv[1].split(",") if len(sys.argv) > 1 else list(INPUTS)
    tols = sys.argv[2].split(",") if len(sys.argv) > 2 else list(TOLS)
    rows = []
    for n in names:
        for tol in tols:
            for s in STARTS:
                r = run(n, s, tol)
                rows.append(r)
                print(f"{n:9s} {tol:7s} start {s:4d} sub {r['sub_cell_pct_at_start']:5.1f}% {r['reported_status']:9s} it {r['iterations']:5d} {r['wall']:6.1f}s mean {r['true_mean']:6.2f} max {r['true_max']:7.1f} inv {r['invalid']:3d} {r['levels_run']}", flush=True)
    out = HERE / "data" / f"start_{"_".join(names)}_{"_".join(tols)}_f{FINAL}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows))
