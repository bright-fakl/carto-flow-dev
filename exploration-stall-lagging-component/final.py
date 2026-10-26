"""The chosen design (wait_for_lagging_regions True/False) on real runs; usage: final.py <out dir> <case> counties-<validity> | controls | scenes"""
import warnings, sys, json, time; warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow, morph_geometries
out, case = sys.argv[1], sys.argv[2]
res = {}
def save(): json.dump(res, open(f"{out}/final_{case}.json", "w"), indent=1)

def stats(geoms, v):
    o = np.array(geoms, dtype=object); valid = shapely.is_valid(o); a = shapely.area(o)
    T = v / v[valid].sum() * a[valid].sum(); e = abs(a - T) / T * 100; ev = e[valid]
    return dict(invalid=int((~valid).sum()), mean=float(ev.mean()), median=float(np.median(ev)), p95=float(np.percentile(ev, 95)), max=float(ev.max()), n10=int((ev > 10).sum()), n5=int((ev > 5).sum()))

def ladder(gdf, lag, validity, n_iter):
    t = time.time(); w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=n_iter, show_progress=False, validity=validity, wait_for_lagging_regions=lag))
    lv = [dict(grid=c.grid.sx, status=c.status.value, niter=c.niterations, best_it=c.best_iteration, n10_best=int((np.abs(c.best.errors.errors_pct) > 10).sum()),
               n10_last=int((np.abs(c.snapshots.snapshots[-1].errors.errors_pct) > 10).sum())) for c in list(w)[1:]]
    return dict(time=time.time() - t, levels=lv, total_iter=sum(l["niter"] for l in lv), final=stats(w[-1].get_geometry(), gdf["v"].to_numpy(float)))

if case.startswith("counties"):
    validity = case.split("-", 1)[1]
    g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True); gdf = g[["geometry"]].assign(v=g["Population"].to_numpy(float))
    for n_iter in (500, 1000, 3000):
        for lag in (False, True):
            k = f"{n_iter}-{lag}"; res[k] = ladder(gdf, lag, validity, n_iter); r = res[k]; save()
            print(case, k, round(r["time"]), r["total_iter"], [(l["grid"], l["status"][:4], l["niter"], l["n10_best"], l["n10_last"]) for l in r["levels"]], {a: round(b, 2) for a, b in r["final"].items()}, flush=True)
elif case == "controls":
    for level in ("congressional_district", "state"):
        g = data.load_us_census(level=level, max_segment_length=1000 if level != "state" else None).reset_index(drop=True); gdf = g[["geometry"]].assign(v=g["Population"].to_numpy(float))
        for lag in (False, True):
            k = f"{level}-{lag}"; res[k] = ladder(gdf, lag, "check", 500); r = res[k]; save()
            print(k, round(r["time"], 1), r["total_iter"], [(l["grid"], l["status"][:4], l["niter"]) for l in r["levels"]], {a: round(b, 3) for a, b in r["final"].items()}, flush=True)
else:
    sys.path.insert(0, "/home/fakl/carto-flow-wt-177b/tests")
    from test_flow_validity import strip_scene
    for seed in (3, 7, 11, 19, 23, 31):
        polys, vals = strip_scene(seed)
        for validity in ("check", "repair-crossings"):
            for lag in (False, True):
                r = morph_geometries(polys, vals, options=MorphOptions(grid=64, n_iter=400, mean_tol=0.02, max_tol=0.05, show_progress=False, validity=validity, wait_for_lagging_regions=lag))
                e = r.get_errors(); k = f"{seed}-{validity}-{lag}"
                res[k] = dict(status=r.status.value, niter=r.niterations, best=r.best_iteration, mean=e.mean_error_pct, max=e.max_error_pct, invalid=len(r.invalid_regions)); print(k, res[k], flush=True); save()
