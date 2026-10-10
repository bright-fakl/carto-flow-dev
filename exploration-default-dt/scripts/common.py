"""Shared helpers: cases, one instrumented run (counts rasterizations and FFT solves), metrics from the output geometries.

Run with the worktree interpreter of investigate/default-dt (`uv run python ...` from the repository root).
"""
import os
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("NUMBA_NUM_THREADS", "4")

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.data as data
import carto_flow.flow_cartogram.algorithm as alg
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor
from carto_flow.flow_cartogram.velocity import VelocityComputerFFTW

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SCRATCH = os.environ.get("DT_SCRATCH", "/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
COUNTIES = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/counties_prepared.parquet"
# one field recompute (rasterize + FFT) in plain advection steps (adaptive-recompute page)
RATIO = {("states", 128): 9, ("states", 256): 12, ("states", 512): 24, ("states", 1024): 71,
         ("districts", 128): 18, ("districts", 256): 21, ("districts", 512): 23, ("districts", 1024): 47,
         ("counties", 128): 21, ("counties", 256): 47.5, ("counties", 512): 28.5}
TIGHT = dict(mean_tol=0.005, max_tol=0.01)

_cache = {}


def load_case(case):
    """Returns geodataframe, value column, area_scale, extra MorphOptions kwargs, n_iter."""
    if case in _cache:
        return _cache[case]
    if case in ("states", "states_mr", "horiz", "tang", "tilt"):
        g, col, sc, kw = data.load_us_census(population=True).reset_index(drop=True), "Population", 1.0, {}
        if case in ("horiz", "tang", "tilt"):
            mod = {"horiz": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3),
                   "tang": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
                   "tilt": DirectionalTensor(theta=np.pi / 6, Dpar=4, Dperp=0.3)}[case]
            BAL = MorphOptions.preset_balanced()
            kw = {k: getattr(BAL, k) for k in ("Dx", "Dy", "density_mod", "mean_tol", "max_tol") if hasattr(BAL, k)}
            kw["anisotropy"] = mod
            sc = 1e-6
        out = g, col, sc, kw, 400
    elif case == "districts":
        out = data.load_us_census(level="congressional_district").reset_index(drop=True), "Population", 1.0, {}, 400
    elif case == "counties":
        out = gpd.read_parquet(COUNTIES), "total_votes", 1e-6, {}, 300
    else:
        raise ValueError(case)
    _cache[case] = out
    return out


def metrics(geoms, target):
    """Accuracy and validity measured from the output geometries (linear relative error of area shares)."""
    a = np.array([g.area for g in geoms])
    t = np.asarray(target, float)
    lin = np.abs((a / a.sum()) / (t / t.sum()) - 1)
    arr = np.asarray(geoms, dtype=object)
    valid = shapely.is_valid(arr)
    reasons = shapely.is_valid_reason(arr[~valid])
    return dict(mean=float(lin.mean()), max=float(lin.max()), gt10=float((lin > 0.10).mean()),
                invalid=int((~valid).sum()), selfint=int(sum("Self-intersection" in r for r in reasons)))


class Counter:
    def __enter__(self):
        self.n = dict(raster=0, fft=0)
        self.r0, self.f0 = alg.compute_density_field_from_geometries, VelocityComputerFFTW.compute

        def r(*a, **k):
            self.n["raster"] += 1
            return self.r0(*a, **k)

        def f(s, *a, **k):
            self.n["fft"] += 1
            return self.f0(s, *a, **k)

        alg.compute_density_field_from_geometries, VelocityComputerFFTW.compute = r, f
        return self

    def __exit__(self, *a):
        alg.compute_density_field_from_geometries, VelocityComputerFFTW.compute = self.r0, self.f0


def trace_stats(score):
    rises = score[1:] > score[:-1]
    return dict(best=float(score.min()), final=float(score[-1]),
                rises20=int((rises & (score[:-1] < 20)).sum()),
                spike=float(max([score[i + 1] / score[i] for i in range(len(score) - 1) if score[i] < 20 and rises[i]], default=1.0)),
                first_below1=int(np.argmax(score < 1)) + 1 if (score < 1).any() else None)


def score_of(r, o):
    cv = r.convergence
    return np.maximum(cv.mean_log_errors / np.log2(1 + o.mean_tol), cv.max_log_errors / np.log2(1 + o.max_tol))


def options_for(grid_size, n_iter, sc, extra, dt, rr, rre, tight, grid=None):
    kw = dict(extra)
    kw["dt"] = dt
    if rre is not None:
        kw["recompute_every"] = rre
    if tight:
        kw.update(TIGHT)
    if grid is not None:
        kw["grid"] = grid
    else:
        kw["grid_size"] = grid_size
    return MorphOptions(show_progress=False, n_iter=n_iter, area_scale=sc, refresh_on_rise=rr, **kw)


def run_one(case, grid_size, dt, rr, rre=None, tight=False, n_iter=None, grid=None, base_opts=None, g=None, col=None, **tags):
    g0, col0, sc, extra, n0 = load_case(case)
    g = g0 if g is None else g
    col = col0 if col is None else col
    o = base_opts if base_opts is not None else options_for(grid_size, n_iter or n0, sc, extra, dt, rr, rre, tight, grid)
    load = open("/proc/loadavg").read().split()[0]
    with Counter() as c:
        t = time.perf_counter()
        r = morph_gdf(g, col, options=o)
        wall = time.perf_counter() - t
    score = score_of(r, o)
    geoms = list(r.latest.geometry)
    m = metrics(geoms, g[col].to_numpy(float))
    rec = dict(case=case, grid=grid_size, dt=dt, rr=rr, rre=o.recompute_every, tight=bool(tight),
               status=str(r.status.value), stop=str(getattr(r.stop_reason, "value", r.stop_reason)),
               best_it=r.best_iteration, it=int(len(score)), rec=c.n["fft"], wall=round(wall, 2), load=load,
               score=[round(float(x), 4) for x in score], **trace_stats(score), **m, **tags)
    base = case if case != "states_mr" else "states"
    ratio = RATIO.get((base, grid_size))
    rec["cost"] = None if ratio is None else rec["it"] + rec["rec"] * ratio
    return rec, r, geoms


def key_of(rec):
    return f"{rec['case']}|{rec['grid']}|{rec['dt']}|{rec['rr']}|{rec['rre']}|{int(rec['tight'])}"
