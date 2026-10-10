"""Mean vertex displacement per step (cells) of A and B2 over a run, per case; dt_match = dt0 * B2 / A. Writes ../data/dtmatch.json"""
import json, os, sys
from common import *
import carto_flow.flow_cartogram.step_scale as ss

cases = [("states", 128), ("states", 256), ("states", 512), ("states_mr", 128), ("horiz", 256), ("tang", 256), ("tilt", 256),
         ("districts", 256), ("districts", 512), ("counties", 256), ("counties", 512)]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "dtmatch.json")
res = json.load(open(out)) if os.path.exists(out) else {}
for case, gs in cases:
    key = f"{case}_{gs}"
    if key in res:
        continue
    g, col, sc, kw, n_iter = load_case(case)
    grid = None
    if case == "states_mr":
        from carto_flow.flow_cartogram.workflow import CartogramWorkflow
        o = MorphOptions(show_progress=False, stall_patience=None, n_iter=10, recompute_every=10, area_scale=sc)
        wf = CartogramWorkflow(g, col, None, None, o)
        wf.morph_multiresolution(min_resolution=gs, levels=2, options=o)
        grid = wf.results[1].grid
    row = {}
    for n in ("A", "B2"):
        ss.MEASURE.clear(); ss.MEASURE_ON = True
        run_one(g, col, sc, gs, n_iter, {**kw, **VARIANTS[n][1]}, 0.01, grid=grid)
        row[n] = float(np.mean(ss.MEASURE)); row[n + "_steps"] = len(ss.MEASURE)
    dt0 = kw.get("dt", 0.2)
    row["dt0"] = dt0; row["dt_match"] = dt0 * row["B2"] / row["A"]
    res[key] = row
    print(key, row, flush=True)
    json.dump(res, open(out, "w"), indent=1)
