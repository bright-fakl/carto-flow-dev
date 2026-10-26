"""County ladder (1 km input, auto grid, n_iter 1000) per validity mode: how each level ends, and the error of the result."""
import warnings, sys, json, time; warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
out = sys.argv[1]
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v)

def stats(geoms):
    o = np.array(geoms, dtype=object); valid = shapely.is_valid(o); a = shapely.area(o)
    T = v / v[valid].sum() * a[valid].sum(); e = abs(a - T) / T * 100
    ev = e[valid]
    return dict(invalid=int((~valid).sum()), mean_valid=float(ev.mean()), median_valid=float(np.median(ev)), p95_valid=float(np.percentile(ev, 95)),
                max_valid=float(ev.max()), n10_valid=int((ev > 10).sum()), n1_valid=int((ev > 1).sum()))

res = {}
for mode in ("check", "repair-crossings", "repair-quadtree"):
    t = time.time(); w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False, validity=mode))
    levels = [dict(grid=(c.grid.sx if c.grid else None), status=str(c.status.value), niter=c.niterations, best=c.best_iteration,
                   mean_pct=float(c.get_errors().mean_error_pct), max_pct=float(c.get_errors().max_error_pct)) for c in list(w)[1:]]
    res[mode] = dict(time=time.time() - t, levels=levels, final=stats(w[-1].get_geometry()), nverts=int(len(shapely.get_coordinates(np.array(w[-1].get_geometry(), dtype=object)))))
    print(mode, json.dumps(res[mode]), flush=True)
    json.dump(res, open(f"{out}/ladder_modes.json", "w"), indent=1)
