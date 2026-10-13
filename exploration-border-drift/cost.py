"""Cost of the correction (#86): the sum in place during the morph, and the remap afterwards.

    NUMBA_NUM_THREADS=8 uv run python cost.py
"""
import json
import time
import warnings
from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import numpy as np
import shapely

import border_band as bb
import carto_flow.flow_cartogram as flow
import carto_flow.flow_cartogram.algorithm as alg
import carto_flow.proportional_cartogram as prop
from jacobian_path import proxy_remap, proxy_remap_fast, proxy_remap_sampled
from velocity_profile import sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
g = bb.g
col = "Below Poverty Level"
d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=0)
owner = np.array([list(g.index).index(o) for o in d["original_index"]])
P0 = np.array([[p.x, p.y] for p in d.geometry])
lm = gpd.GeoSeries(shapely.points(P0), crs=g.crs)
orig_fn = alg.displace_coords_numba
opts = flow.MorphOptions(area_scale=1e-6, n_iter=400, show_progress=False)


def morph(wrap):
    st = {"key": None, "div": None, "grid": None, "logJ": np.zeros(len(P0)), "extra": 0.0}

    def wrapped(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel=True):
        if coords.ndim == 2 and coords.shape[0] == len(P0):
            t = time.perf_counter()
            key = float(vx.sum())
            if st["key"] != key:
                st["key"] = key
                st["div"] = np.gradient(vx, dx, axis=1) + np.gradient(vy, dy, axis=0)
                st["grid"] = SimpleNamespace(x_coords=xs, y_coords=ys, dx=dx, dy=dy)
            st["logJ"] += dt * sample(st["div"], st["grid"], coords)
            st["extra"] += time.perf_counter() - t
        return orig_fn(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel)

    if wrap:
        alg.displace_coords_numba = wrapped
    try:
        t0 = time.perf_counter()
        c = flow.create_flow_cartogram(g, "Population", landmarks=lm, options=opts)
        sec = time.perf_counter() - t0
    finally:
        alg.displace_coords_numba = orig_fn
    return c, st, sec


morph(False)  # warm-up (compilation)
without = [morph(False)[2] for _ in range(3)]
runs = [morph(True) for _ in range(3)]
withs = [r[2] for r in runs]
extra = [r[1]["extra"] for r in runs]
c, st, _ = runs[-1]
fin = c.snapshots[-1]
Pf = np.array([[p.x, p.y] for p in fin.landmarks])
geoms = [x.buffer(0) for x in fin.geometry]
orig = list(g.geometry)
ratio = np.array([geoms[r].area / orig[r].area for r in range(len(orig))])
cdot = np.exp(-st["logJ"]) * ratio[owner]
bb.owner = owner
res = {"iterations": int(c.niterations), "landmarks": len(P0), "morph_seconds_without": [round(x, 3) for x in without], "morph_seconds_with": [round(x, 3) for x in withs],
       "seconds_in_the_sum": [round(x, 4) for x in extra], "remap": []}
for n in (26,):
    t = time.perf_counter()
    Q = proxy_remap(geoms, Pf, owner, cdot, n_grid=n)
    sec = time.perf_counter() - t
    sc = np.array([np.sqrt(geoms[o].area) for o in owner])
    row = {"grid_points": n, "seconds": round(sec, 2), "z": round(bb.band_z(geoms, Q)[2], 2), "shift_median": round(float(np.median(np.linalg.norm(Q - Pf, axis=1) / sc)), 4)}
    res["remap"].append(row)
    print(row, flush=True)
t = time.perf_counter()
Q = proxy_remap_fast(geoms, Pf, owner, cdot)
sec = time.perf_counter() - t
sc = np.array([np.sqrt(geoms[o].area) for o in owner])
row = {"grid_points": "first order, no buffers", "seconds": round(sec, 2), "z": round(bb.band_z(geoms, Q)[2], 2), "shift_median": round(float(np.median(np.linalg.norm(Q - Pf, axis=1) / sc)), 4)}
res["remap"].append(row)
print(row, flush=True)
for n_ref in (200, 400, 1000):
    t = time.perf_counter()
    Q = proxy_remap_sampled(geoms, Pf, owner, cdot, n_ref=n_ref)
    sec = time.perf_counter() - t
    row = {"grid_points": f"{n_ref} sample points per region", "seconds": round(sec, 2), "z": round(bb.band_z(geoms, Q)[2], 2), "shift_median": round(float(np.median(np.linalg.norm(Q - Pf, axis=1) / sc)), 4)}
    res["remap"].append(row)
    print(row, flush=True)
res["z_before"] = round(bb.band_z(geoms, Pf)[2], 2)
print(res)
(HERE / "data" / "cost.json").write_text(json.dumps(res))
