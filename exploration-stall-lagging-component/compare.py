"""Stall-rule candidates on real library runs: counties (ladder), districts, states, synthetic strip scenes.
usage: compare.py <out dir> <case> where case is counties-<validity> | controls | scenes"""
import warnings, sys, json, time; warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow, morph_geometries
import os
out, case = sys.argv[1], sys.argv[2]
case_tag = case + ("-finest" if os.environ.get("CF_LAG_FINEST_ONLY") else "") + ("-bestexcess" if os.environ.get("CF_BEST") else "")
MODES = [m if m != "none" else None for m in os.environ.get("CF_MODES", "none,count1,count,excess,median").split(",")]

def final_stats(result, geoms, v):
    o = np.array(geoms, dtype=object); valid = shapely.is_valid(o); a = shapely.area(o)
    T = v / v[valid].sum() * a[valid].sum(); e = abs(a - T) / T * 100; ev = e[valid]
    return dict(invalid=int((~valid).sum()), mean=float(ev.mean()), median=float(np.median(ev)), p95=float(np.percentile(ev, 95)), max=float(ev.max()),
                n10=int((ev > 10).sum()), n5=int((ev > 5).sum()))

def lagging_of(c, tol=10.0):
    best, last = c.best, c.snapshots.snapshots[-1]
    ex = lambda s: int((np.abs(s.errors.errors_pct) > tol).sum())
    return dict(best_it=c.best_iteration, n_above_best=ex(best), n_above_last=ex(last))

def ladder(gdf, mode, validity, n_iter, mr=dict(min_resolution="auto", levels="auto")):
    t = time.time(); w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(options=MorphOptions(area_scale=1e-6, n_iter=n_iter, show_progress=False, validity=validity, stall_lagging=mode), **mr)
    lv = [dict(grid=c.grid.sx, status=c.status.value, niter=c.niterations, **lagging_of(c)) for c in list(w)[1:]]
    return dict(time=time.time() - t, levels=lv, total_iter=sum(l["niter"] for l in lv), final=final_stats(w[-1], w[-1].get_geometry(), gdf["v"].to_numpy(float)))

res = {}
def save(): json.dump(res, open(f"{out}/compare_{case_tag}.json", "w"), indent=1)
if case.startswith("counties"):
    validity = case.split("-", 1)[1]
    g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True); gdf = g[["geometry"]].assign(v=g["Population"].to_numpy(float))
    for n_iter in (1000, 3000):
        for mode in MODES:
            res[f"{n_iter}-{mode}"] = ladder(gdf, mode, validity, n_iter); r = res[f"{n_iter}-{mode}"]; save()
            print(case_tag, n_iter, mode, round(r["time"]), r["total_iter"], [(l["grid"], l["status"][:4], l["niter"]) for l in r["levels"]], {k: round(x, 2) for k, x in r["final"].items()}, flush=True)
elif case == "controls":
    for level in ("congressional_district", "state"):
        g = data.load_us_census(level=level, max_segment_length=1000 if level != "state" else None).reset_index(drop=True); gdf = g[["geometry"]].assign(v=g["Population"].to_numpy(float))
        for mode in MODES:
            res[f"{level}-{mode}"] = ladder(gdf, mode, "check", 1000); r = res[f"{level}-{mode}"]; save()
            print(level, mode, round(r["time"], 1), r["total_iter"], [(l["grid"], l["status"][:4], l["niter"]) for l in r["levels"]], {k: round(x, 3) for k, x in r["final"].items()}, flush=True)
else:
    sys.path.insert(0, "/home/fakl/carto-flow-wt-177b/tests")
    from test_flow_validity import strip_scene
    for seed in (3, 7, 11, 19):
        polys, vals = strip_scene(seed)
        for validity in ("check", "repair-crossings"):
            for mode in MODES:
                t = time.time()
                r = morph_geometries(polys, vals, options=MorphOptions(grid=64, n_iter=400, mean_tol=0.02, max_tol=0.05, show_progress=False, validity=validity, stall_lagging=mode))
                e = r.get_errors()
                res[f"{seed}-{validity}-{mode}"] = dict(time=time.time() - t, status=r.status.value, niter=r.niterations, best=r.best_iteration, mean=e.mean_error_pct, max=e.max_error_pct, invalid=len(r.invalid_regions))
                print(seed, validity, mode, res[f"{seed}-{validity}-{mode}"], flush=True); save()
