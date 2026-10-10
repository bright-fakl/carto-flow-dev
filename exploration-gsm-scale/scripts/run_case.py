"""usage: python run_case.py <case> <grid> [variants|all] [dt]   writes ../data/<case>_<grid>[_dt<dt>].json
cases: states, states_mr (coarse multiresolution level), horiz, tang, tilt, districts, counties"""
import json
import os
import sys

from common import *

case, grid_size = sys.argv[1], int(sys.argv[2])
names = MAIN if len(sys.argv) < 4 or sys.argv[3] == "all" else CONTROLS if sys.argv[3] == "controls" else sys.argv[3].split(",")
dt = float(sys.argv[4]) if len(sys.argv) > 4 else None
g, col, sc, kw, n_iter = load_case(case)
base = {"states_mr": "states", "horiz": "states", "tang": "states", "tilt": "states"}.get(case, case)
grid = None
if case == "states_mr":
    from carto_flow.flow_cartogram.workflow import CartogramWorkflow

    o = MorphOptions(show_progress=False, stall_patience=None, n_iter=10, recompute_every=10, area_scale=sc)
    wf = CartogramWorkflow(g, col, None, None, o)
    wf.morph_multiresolution(min_resolution=grid_size, levels=2, options=o)
    grid = wf.results[1].grid
    print("coarse grid", grid.size, flush=True)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data",
                   f"{case}_{grid_size}" + (f"_dt{dt}" if dt else "") + ".json")
res = json.load(open(out)) if os.path.exists(out) else {}
run_one(g.iloc[:30], col, sc, 64, 12, {}, 0.01)  # numba warm-up
for rr in (None, 0.01):
    for n in names:
        key = f"{n}|{'on' if rr else 'off'}"
        if key in res:
            continue
        extra = {**kw, **VARIANTS[n][1]}
        if n == "C3m":
            extra["dt"] = min(1.0, json.load(open(os.path.join(os.path.dirname(out), "dtmatch.json")))[f"{case}_{grid_size}"]["dt_match"])
        try:
            r, _ = run_one(g, col, sc, grid_size, n_iter, extra, rr, dt=dt, grid=grid)
        except Exception as e:  # noqa
            r = dict(status="error: " + repr(e)[:100], it=0, rec=0, score=[], wall=0)
        r["ratio"] = RATIO.get((base, grid_size))
        r["dt_used"] = dt or extra.get("dt", 0.2)
        res[key] = r
        print(case, grid_size, key, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != "score"}, flush=True)
        json.dump(res, open(out, "w"))
