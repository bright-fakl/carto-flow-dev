"""Run baseline (fix/stall-detection defaults) and the GSM-style prototype on one case; write data/<name>.json.

usage: NUMBA_NUM_THREADS=4 uv run python run_case.py <case> <grid> [max_pass]
cases: states, districts, counties, states_mr (coarse multiresolution level), horiz, tang, tilt (strong anisotropy)
"""
import json
import shapely
import numpy as np
import os
import sys

from common import *  # noqa: F403
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor
from carto_flow.flow_cartogram.workflow import CartogramWorkflow

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
case, grid_size = sys.argv[1], int(sys.argv[2])
max_pass = int(sys.argv[3]) if len(sys.argv) > 3 else 12
base_case = {"states_mr": "states", "horiz": "states", "tang": "states", "tilt": "states"}.get(case, case)
g, col, sc = load(base_case)
vals = g[col].to_numpy(float)
kw, n_iter, modulator = {}, 400, None
baseline(g.iloc[:20], col, sc, 64, n_iter=12)  # numba warm-up (JIT excluded from timings)
gp.run(g.geometry[:20], vals[:20], baseline(g.iloc[:20], col, sc, 64, n_iter=12)[1].grid, max_pass=1)
dc_idx = list(g["State Abbreviation"]).index("DC") if (case.startswith("states") or case in ("horiz", "tang", "tilt")) else None


def dc_err(geoms):
    if dc_idx is None:
        return None
    a = np.array([x.area for x in geoms])
    return float(abs(a[dc_idx] / a.sum() / (vals[dc_idx] / vals.sum()) - 1))


def cells_in(geom, grid):
    X, Y = np.meshgrid(grid.x_coords, grid.y_coords)
    return int(shapely.contains_xy(geom, X.ravel(), Y.ravel()).sum())

if case == "counties":
    n_iter = 300
if case in ("horiz", "tang", "tilt"):
    mod = {"horiz": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3), "tang": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
           "tilt": DirectionalTensor(theta=3.141592653589793 / 6, Dpar=4, Dperp=0.3)}[case]
    BAL = MorphOptions.preset_balanced()
    kw = {k: getattr(BAL, k) for k in ("dt", "Dx", "Dy", "density_mod", "mean_tol", "max_tol") if hasattr(BAL, k)}
    kw["anisotropy"] = mod
    sc = 1e-6
    modulator = mod
    gp.MEAN_TOL, gp.MAX_TOL = kw["mean_tol"], kw["max_tol"]
if case == "states_mr":
    o = MorphOptions(show_progress=False, stall_patience=None, n_iter=10, recompute_every=10, area_scale=sc)
    wf = CartogramWorkflow(g, col, None, None, o)
    wf.morph_multiresolution(min_resolution=grid_size, levels=2, options=o)
    grid = wf.results[1].grid
    kw["grid"] = grid
    print("multires coarse grid", grid.size, grid.dx, flush=True)
    del kw["grid"]
    kw["grid"] = grid
    b, r = baseline(g, col, sc, grid_size, n_iter=n_iter, **kw)
else:
    b, r = baseline(g, col, sc, grid_size, n_iter=n_iter, **kw)
grid = r.grid
b["dc_err"] = dc_err(list(r.latest.geometry))
b["dc_cells0"] = cells_in(g.geometry[dc_idx], grid) if dc_idx is not None else None
b["ratio"] = COST_RATIO.get((base_case, grid_size))
b["load"] = load_avg()
print(case, grid_size, {k: v for k, v in b.items() if k != "score"}, flush=True)
res = dict(case=case, grid=grid_size, grid_shape=list(grid.size), baseline=b, gsm={})
configs = [(f"blur{bl}", dict(blur0=bl)) for bl in (0, 1, 2, 4)]
if case in ("states", "states_mr", "districts"):
    configs += [(f"blur1_fix{n}", dict(blur0=1, fixed_steps=n)) for n in (4, 8, 16, 32)]
if case == "counties":
    configs = [(f"blur{bl}", dict(blur0=bl)) for bl in (1, 4, 8)]
for name, cfg in configs:
    out = gp.run(g.geometry, vals, grid, max_pass=max_pass, modulator=modulator, **cfg)
    tr = out["trace"]
    best = min(tr, key=lambda d: d["score"])
    res["gsm"][name] = dict(cfg=cfg, trace=tr, passes=out["passes"], evals=out["evals"], wall=out["wall"], best_pass=best["p"], dc_err=dc_err(out["geoms"]),
                            load=load_avg())
    print(f"  {name}: passes {out['passes']} evals {out['evals']} wall {out['wall']:.1f}s | final score {tr[-1]['score']:.2f} "
          f"mean {100*tr[-1]['mean']:.2f}% max {100*tr[-1]['max']:.1f}% invalid {tr[-1]['invalid']} | best pass {best['p']} score {best['score']:.2f}",
          flush=True)
    json.dump(res, open(os.path.join(OUT, f"{case}_{grid_size}.json"), "w"))
