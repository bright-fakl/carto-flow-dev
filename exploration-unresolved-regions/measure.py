"""Counties (1 km input, auto ladder, validity="repair-crossings", n_iter 1000) with an absolute area tolerance of k cells,
and an offline estimate of the sub-cell-count exclusion from the baseline levels; districts and states as controls."""
import warnings, sys, json, time; warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
out = sys.argv[1]; which = sys.argv[2:] or ["counties", "controls"]

def load(level):
    g = data.load_us_census(level=level, max_segment_length=1000 if level != "state" else None)
    g = g.reset_index(drop=True); return g[["geometry"]].assign(v=g["Population"].to_numpy(float)), g["Population"].to_numpy(float)

def run(gdf, k, n_iter=1000):
    t = time.time(); w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=n_iter, show_progress=False, validity="repair-crossings", area_tol_cells=k))
    levels = []
    for c in list(w)[1:]:
        e = c.get_errors()
        levels.append(dict(grid=c.grid.sx, cell=c.grid.dx * c.grid.dy, status=c.status.value, niter=c.niterations, best=c.best_iteration, n_unresolved=c.n_unresolved,
                           mean_pct=e.mean_error_pct, max_pct=e.max_error_pct, n10=int((np.abs(e.errors_pct) > 10).sum()),
                           log_errors=e.log_errors.tolist()))
    return dict(time=time.time() - t, levels=levels)

res = {}
if "counties" in which:
    gdf, v = load("county")
    for k in (0, 1, 2, 4, 8, 16):
        res[f"county_{k}"] = run(gdf, k); r = res[f"county_{k}"]
        print("county", k, round(r["time"]), [(l["grid"], l["status"], l["niter"], l["n_unresolved"], round(l["max_pct"], 1)) for l in r["levels"]], flush=True)
        json.dump(res, open(f"{out}/measure.json", "w"))
if "controls" in which:
    for level in ("congressional_district", "state"):
        gdf, v = load(level)
        for k in (0, 4):
            res[f"{level}_{k}"] = run(gdf, k, 300); r = res[f"{level}_{k}"]
            print(level, k, round(r["time"], 1), [(l["grid"], l["status"], l["niter"], round(l["mean_pct"], 4), round(l["max_pct"], 4)) for l in r["levels"]], flush=True)
            json.dump(res, open(f"{out}/measure_controls.json", "w"))
