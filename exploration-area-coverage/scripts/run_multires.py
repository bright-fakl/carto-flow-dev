"""Multiresolution runs (min_resolution=128, levels=3) for states and districts.

Usage: NUMBA_NUM_THREADS=4 uv run python run_multires.py <states|districts> <stall: off|on> [cov list]
Results go to data/mr_<case>_<stall>.pkl. stall off: stall_patience None, 300 iterations per level.
"""

import pickle
import sys
import time
from pathlib import Path

import numpy as np
import shapely

import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries as dens
from carto_flow.flow_cartogram.grid import Grid
from carto_flow.flow_cartogram.workflow import CartogramWorkflow
from common import COV_NAME, score_hist, share_errors, stall_replay, warmup  # noqa: F401

HERE = Path(__file__).resolve().parent.parent
case, stall = sys.argv[1], sys.argv[2]
covs = [None, 2, 4, 8, "exact"] if len(sys.argv) < 4 else [None if c == "center" else (c if c == "exact" else int(c)) for c in sys.argv[3].split(",")]
ro_list = [0.01, None]
g = (
    data.load_us_census(population=True)
    if case == "states"
    else data.load_us_census(level="congressional_district")
).reset_index(drop=True)
col = "Population"
geoms = list(g.geometry)
areas = shapely.area(np.asarray(geoms, dtype=object))

# sub-cell regions per level, from the original geometry
sub = {}
for n in (128, 256, 512, 1024):
    grid = Grid.from_bounds(g.total_bounds, size=n, margin=0.5)
    cell = grid.dx * grid.dy
    _, m0 = dens(geoms, g[col].to_numpy(float), grid, return_geometry_mask=True)
    seen = np.unique(m0[m0 >= 0])
    sub[n] = dict(lt_cell=int((areas < cell).sum()), no_center=int(len(g) - len(seen)))
print("sub-cell regions", sub, flush=True)

out = HERE / "data" / f"mr_{case}_{stall}.pkl"
res_all = pickle.load(open(out, "rb")) if out.exists() else {}
for ro in ro_list:
    for cov in covs:
        k = f"{COV_NAME[cov]}|ro{ro}"
        if k in res_all:
            continue
        o = MorphOptions(
            show_progress=False,
            stall_patience=None if stall == "off" else 4,
            n_iter=300 if stall == "off" else 400,
            benchmark=True,
            refresh_on_rise=ro,
            density_coverage=cov,
        )
        t0 = time.perf_counter()
        wf = CartogramWorkflow(g, col, None, None, o)
        wf.morph_multiresolution(min_resolution=128, levels=3, options=o)
        wall = time.perf_counter() - t0
        levels = []
        for r in wf.results[1:]:
            s = score_hist(r, r.options)
            b = r.benchmark
            levels.append(
                dict(
                    grid=int(r.grid.sx),
                    status=str(r.status.value),
                    it=len(s),
                    rec=b.density_calls,
                    best=float(s.min()),
                    final=float(s[-1]),
                    lib_max=float(r.latest.errors.max_error_pct),
                    ratio=float(
                        ((b.density_s + b.velocity_s) / max(b.density_calls, 1))
                        / ((b.displacement_s + b.areas_s + b.errors_s) / len(s))
                    ),
                    score=s.tolist(),
                )
            )
        fin = wf.latest.latest
        err = share_errors(fin.geometry, g[col])
        row = dict(
            levels=levels,
            wall=wall,
            ext_mean=float(err.mean() * 100),
            ext_max=float(err.max() * 100),
            ext_gt10=float((err > 0.10).mean() * 100),
            dc_err=float(err[np.argmin(areas)] * 100),
            cost=float(sum(lv["it"] + lv["rec"] * lv["ratio"] for lv in levels)),
            sub=sub,
        )
        res_all[k] = row
        print(case, stall, k, {a: v for a, v in row.items() if a not in ("levels", "sub")}, flush=True)
        for lv in levels:
            print("   ", {a: (round(v, 3) if isinstance(v, float) else v) for a, v in lv.items() if a != "score"}, flush=True)
        pickle.dump(res_all, open(out, "wb"))
