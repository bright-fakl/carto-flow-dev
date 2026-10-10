"""Shared harness: cases, variants, one instrumented run, metrics from the output geometries.

Imports the prototype from its worktree (investigate/adaptive-step). Counters wrap the density
and displacement calls of the algorithm module, so the library needs no instrumentation.
"""

import os
import sys
import time
import warnings

import numpy as np

WT = os.environ.get("CF_SRC", "/home/fakl/carto-flow/.claude/worktrees/agent-ab5bf2668bfc3a4df/src")
sys.path.insert(0, WT)
os.environ.setdefault("NUMBA_NUM_THREADS", "4")
warnings.filterwarnings("ignore")

import carto_flow.data as data  # noqa: E402
import carto_flow.flow_cartogram.algorithm as alg  # noqa: E402
from carto_flow.flow_cartogram import MorphOptions, morph_gdf  # noqa: E402
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor  # noqa: E402

assert WT in alg.__file__, alg.__file__

COUNTIES = os.environ.get(
    "CF_COUNTIES",
    "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/counties_prepared.parquet",
)

# Cost of one field recompute in plain steps (adaptive-recompute-experiment, scripts/costs.py).
RATIO = {
    "states": {128: 9.2, 256: 12.0, 512: 24.2, 1024: 70.9},
    "districts": {128: 18.2, 256: 20.9, 512: 23.1, 1024: 46.8},
    "counties": {128: 21.4, 256: 47.5, 512: 28.5},
}
RATIO["horiz"] = RATIO["tang"] = RATIO["tilt"] = RATIO["states_t"] = RATIO["states"]
RATIO["districts_t"] = RATIO["districts"]
TIGHT = dict(mean_tol=0.005, max_tol=0.01)  # the tolerances of issue #94

# Counters filled by the wrappers below.
CNT = {"rec": 0, "disp": 0, "refresh_iters": [], "disp_dt": []}
_orig_density = alg.compute_density_field_from_geometries
_orig_disp = alg.displace_coords_numba


def _density(*a, **k):
    CNT["rec"] += 1
    CNT["refresh_iters"].append(CNT["disp"])
    return _orig_density(*a, **k)


def _disp(coords, xc, yc, vx, vy, dt, *a, **k):
    CNT["disp"] += 1
    CNT["disp_dt"].append(float(dt))
    return _orig_disp(coords, xc, yc, vx, vy, dt, *a, **k)


alg.compute_density_field_from_geometries = _density
alg.displace_coords_numba = _disp

_CACHE = {}


def load_case(case):
    """Return (geodataframe, value column, base option kwargs)."""
    if case in _CACHE:
        return _CACHE[case]
    if case.endswith("_t"):
        gdf, col, base = load_case(case[:-2])
        out = (gdf, col, {**base, **TIGHT})
    elif case == "counties":
        import geopandas as gpd

        out = (gpd.read_parquet(COUNTIES), "total_votes", dict(area_scale=1e-6, n_iter=300))
    elif case == "districts":
        out = (data.load_us_census(level="congressional_district").reset_index(drop=True), "Population", dict(n_iter=400))
    else:
        states = data.load_us_census(population=True).reset_index(drop=True)
        if case == "states":
            out = (states, "Population", dict(n_iter=400))
        else:
            bal = MorphOptions.preset_balanced()
            base = {k: getattr(bal, k) for k in ("dt", "Dx", "Dy", "density_mod", "mean_tol", "max_tol")}
            aniso = {
                "horiz": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3),
                "tang": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
                "tilt": DirectionalTensor(theta=np.pi / 6, Dpar=4, Dperp=0.3),
            }[case]
            base.update(area_scale=1e-6, n_iter=400, anisotropy=aniso)
            out = (states, "Population", base)
    _CACHE[case] = out
    return out


# Controller variants: extra MorphOptions fields. A = error-driven dt, B = area-change limit, C = restart only.
VARIANTS = {"base": {}}
for ref in (3, 10, 30):
    for dmin in (0.05, 0.1):
        VARIANTS[f"A_r{ref}_m{dmin}"] = dict(step_score_ref=ref, step_dt_min=dmin)
for f in (0.02, 0.05, 0.1, 0.2):
    VARIANTS[f"B_{f}"] = dict(step_max_area_change=f)
for ref in (3, 10, 30):
    VARIANTS[f"C_r{ref}"] = dict(step_score_ref=ref, step_dt_min=0.05, step_restart_only=True)
    for f in (0.05,):
        VARIANTS[f"AB_r{ref}_f{f}"] = dict(step_score_ref=ref, step_dt_min=0.05, step_max_area_change=f)


def score_of(c, o):
    return np.maximum(c.mean_log_errors / np.log2(1 + o.mean_tol), c.max_log_errors / np.log2(1 + o.max_tol))


def share_errors(geoms, values):
    a = np.array([g.area for g in geoms])
    rel = np.abs((a / a.sum()) / (np.asarray(values, float) / np.sum(values)) - 1.0)
    return float(rel.mean()), float(rel.max()), float((rel > 0.1).mean())


def classify(res, s):
    """converged / stalled / diverged / incomplete from the status and the whole score history."""
    st = res.status.value
    if st == "converged":
        return "converged"
    if s[-1] > s[0]:
        return "diverged"
    return "stalled" if st == "stalled" else "incomplete"


def run(case, grid=256, variant="base", dt=0.2, R=10, rr="on", keep_score=False, extra=None, geoms=None, **opt):
    g, col, base = load_case(case)
    if geoms is not None:
        g = g.set_geometry(geoms)
    kw = dict(show_progress=False, grid_size=grid)
    kw.update(base)
    kw.update(dt=dt, recompute_every=R, refresh_on_rise=0.01 if rr == "on" else None)
    kw.update(VARIANTS[variant])
    kw.update(extra or {})
    kw.update(opt)
    o = MorphOptions(**kw)
    CNT.update(rec=0, disp=0, refresh_iters=[], disp_dt=[])
    load = os.getloadavg()[0]
    t0 = time.perf_counter()
    res = morph_gdf(g, col, options=o)
    wall = time.perf_counter() - t0
    s = score_of(res.convergence, o)
    it = int(len(s))
    below = s[:-1] < 20
    rises20 = int(np.sum((s[1:] > s[:-1]) & below))
    spike = float(np.max(s[1:][below] / s[:-1][below])) if below.any() else 1.0
    mean_s, max_s, share10 = share_errors(list(res.get_geometry()), g[col].values)
    e = res.latest.errors
    out = dict(
        case=case, grid=grid, variant=variant, dt=dt, R=R, rr=rr,
        status=res.status.value, cls=classify(res, s), it=it, rec=CNT["rec"],
        redo=CNT["disp"] - it, best_it=int(res.best_iteration),
        rises=int(np.sum(s[1:] > s[:-1])), rises20=rises20, spike=spike,
        best=float(s.min()), final=float(s[-1]), s0=float(s[0]),
        lib_mean=float(e.mean_error_pct), lib_max=float(e.max_error_pct),
        out_mean=mean_s * 100, out_max=max_s * 100, out_share10=share10 * 100,
        cost=it + CNT["rec"] * RATIO[case][grid], wall=wall, load=load,
    )
    if keep_score:
        out["score"] = [round(float(x), 5) for x in s]
        out["refresh_iters"] = list(CNT["refresh_iters"])
        d = np.array(CNT["disp_dt"])
        out["dt_trace"] = [round(float(x), 5) for x in d]
    out["_res"] = res
    return out


def key_of(job):
    return "|".join(str(job.get(k)) for k in ("case", "grid", "variant", "dt", "R", "rr", "tag"))


def _worker(job):
    job = dict(job)
    tag = job.pop("tag", None)
    out = run(**job)
    out.pop("_res")
    out["tag"] = tag
    return out


def pool_run(jobs, outfile, workers=4):
    """Run jobs in worker processes; append one JSON line per job to outfile (resumable)."""
    import json
    import multiprocessing as mp

    done = set()
    if os.path.exists(outfile):
        for line in open(outfile):
            done.add(key_of(json.loads(line)))
    todo = [j for j in jobs if key_of(j) not in done]
    print(f"{len(todo)} of {len(jobs)} jobs to run", flush=True)
    ctx = mp.get_context("spawn")
    with ctx.Pool(workers) as pool, open(outfile, "a") as f:
        for out in pool.imap_unordered(_worker, todo):
            f.write(json.dumps(out) + "\n")
            f.flush()
            print(out["case"], out["variant"], out["dt"], out["R"], out["rr"], out["cls"], out["it"], out["rec"], round(out["out_max"], 2), round(out["wall"], 1), flush=True)
