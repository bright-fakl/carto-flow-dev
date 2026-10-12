"""Coarse-to-fine with relaxed coarse tolerances, on several value distributions.

    NUMBA_NUM_THREADS=8 uv run python relaxed_coarse.py [inputs] [distributions]
"""
import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import shapely

from carto_flow import data
from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions
from carto_flow.flow_cartogram.grid import build_multilevel_grids

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
BASE = {
    "states": data.load_us_census(population=True).reset_index(drop=True),
    "districts": data.load_us_census(population=True, level="congressional_district").reset_index(drop=True),
}
import os
FINEST = {"states": int(os.environ.get("FIN", 256)), "districts": int(os.environ.get("FIN", 512))}
COARSEST = {"states": int(os.environ.get("COA", 64)), "districts": int(os.environ.get("COA", 128))}
TOL = (0.01, 0.03)


def values(gdf, dist):
    rng = np.random.default_rng(0)
    a = gdf.geometry.area.to_numpy()
    if dist == "population":
        return gdf["Population"].to_numpy(float)
    if dist == "lognormal1":
        return rng.lognormal(0, 1, len(gdf))
    if dist == "lognormal2":
        return rng.lognormal(0, 2, len(gdf))
    if dist == "area_like":
        return a * rng.lognormal(0, 0.2, len(gdf))
    if dist == "inverse_area":
        return a**-0.5 * rng.lognormal(0, 0.2, len(gdf))
    if dist in ("smooth1", "smooth2"):
        c = gdf.geometry.centroid
        xy = np.column_stack([c.x, c.y])
        scale = 0.15 * max(np.ptp(xy[:, 0]), np.ptp(xy[:, 1]))
        pts = rng.uniform(xy.min(0), xy.max(0), size=(40, 2))
        amp = rng.normal(size=40)
        f = (amp * np.exp(-((xy[:, None, :] - pts[None]) ** 2).sum(-1) / (2 * scale**2))).sum(1)
        f = (f - f.mean()) / f.std()
        return a * np.exp((1 if dist == "smooth1" else 2) * f)
    if dist == "density":
        return gdf["Population Density"].to_numpy(float) * a
    raise ValueError(dist)


def run(name, dist, scheme):
    gdf = BASE[name][["geometry"]].copy()
    gdf["v"] = values(BASE[name], dist)
    fin, coa = FINEST[name], COARSEST[name]
    if scheme == "single":
        starts, k = fin, 1
    else:
        starts = coa
        k = 1 if scheme == "strict" else 4
    levels = int(math.log2(fin // starts)) + 1
    opts = []
    for i in range(levels):
        f = 1 if i == levels - 1 else k
        opts.append(MorphOptions(show_progress=False, mean_tol=TOL[0] * f, max_tol=TOL[1] * f))
    wf = CartogramWorkflow(gdf, "v", options=opts[0])
    t = time.perf_counter()
    if scheme == "relaxed":
        grids = build_multilevel_grids(gdf.total_bounds, starts, levels, margin=0.5, square=True)
        for i, (g, o) in enumerate(zip(grids, opts, strict=True)):
            o.grid = g
            if i:
                o.prescale_components = False
            wf.morph(options=o)
    else:
        wf.morph_multiresolution(min_resolution=starts, levels=levels, options=opts)
    wall = time.perf_counter() - t
    res = wf.results[1:]
    geoms = list(wf.last.get_geometry())
    a = np.array([g.area for g in geoms])
    err = np.abs(a / (gdf["v"].to_numpy(float) / gdf["v"].sum() * a.sum()) - 1) * 100
    return {
        "input": name, "dist": dist, "scheme": scheme,
        "levels": [(int(r.options.grid.sx), r.status.value, int(r.niterations)) for r in res],
        "iterations": int(sum(r.niterations for r in res)), "wall": wall,
        "status": wf.last.status.value, "true_mean": float(err.mean()), "true_max": float(err.max()),
        "invalid": int((~shapely.is_valid(np.array(geoms, dtype=object))).sum()),
    }


if __name__ == "__main__":
    names = sys.argv[1].split(",") if len(sys.argv) > 1 else list(BASE)
    dists = sys.argv[2].split(",") if len(sys.argv) > 2 else ["population", "lognormal1", "lognormal2", "area_like", "inverse_area"]
    rows = []
    for n in names:
        for d in dists:
            for s in ("single", "strict", "relaxed"):
                r = run(n, d, s)
                rows.append(r)
                print(f"{n:9s} {d:13s} {s:8s} {r['status']:9s} it {r['iterations']:5d} {r['wall']:6.1f}s mean {r['true_mean']:6.2f} max {r['true_max']:7.1f} inv {r['invalid']:3d} {r['levels']}", flush=True)
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / f"relaxed_{'_'.join(names)}_f{os.environ.get('FIN', 'def')}_{'_'.join(dists)}.json").write_text(json.dumps(rows))
