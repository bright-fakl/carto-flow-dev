"""Shared helpers: cases, variants, one instrumented run (counts rasterizations and FFT solves)."""
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

COUNTIES = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/counties_prepared.parquet"
# one field recompute (rasterize + FFT) in plain advection steps (adaptive-recompute page)
RATIO = {("states", 128): 9, ("states", 256): 12, ("states", 512): 24, ("states", 1024): 71,
         ("districts", 128): 18, ("districts", 256): 21, ("districts", 512): 23, ("districts", 1024): 47,
         ("counties", 128): 21, ("counties", 256): 47.5, ("counties", 512): 28.5}

# name -> (label, MorphOptions kwargs)
VARIANTS = {
    "A": ("A constant (current)", {}),
    "B1": ("B1 gsm_normalized, floor 0.02", dict(step_scale_mode="gsm_normalized")),
    "B1f01": ("B1 floor 0.01", dict(step_scale_mode="gsm_normalized", step_scale_floor=0.01)),
    "B1f10": ("B1 floor 0.1", dict(step_scale_mode="gsm_normalized", step_scale_floor=0.1)),
    "B3n": ("B3 precomputed B1", dict(step_scale_mode="gsm_normalized", step_scale_precompute=True)),
    "B2": ("B2 gsm_physical, cap 1 cell", dict(step_scale_mode="gsm_physical", step_scale_max_cells=1.0)),
    "B2c3": ("B2 cap 3 cells", dict(step_scale_mode="gsm_physical", step_scale_max_cells=3.0)),
    "B2nc": ("B2 no cap", dict(step_scale_mode="gsm_physical")),
    "B3p": ("B3 precomputed B2 (cap 1)", dict(step_scale_mode="gsm_physical", step_scale_max_cells=1.0, step_scale_precompute=True)),
    "B4n": ("B4ii integral, normalized", dict(step_scale_mode="integral_normalized")),
    "B4s": ("B4ii integral, sub-steps, cap 1", dict(step_scale_mode="integral_physical", step_scale_max_cells=1.0)),
    "B4snc": ("B4ii integral, sub-steps, no cap", dict(step_scale_mode="integral_physical")),
    "B4o": ("B4i integral, one step per round", dict(step_scale_mode="integral_oneshot")),
    "B4oc": ("B4i one step, cap 3 cells", dict(step_scale_mode="integral_oneshot", step_scale_max_cells=3.0)),
    "C1": ("C1 physical, constant scale, cap 1", dict(step_scale_mode="const_physical", step_scale_max_cells=1.0)),
    "C2": ("C2 pattern at A's mean step, floor 0.02", dict(step_scale_mode="gsm_equal_step")),
    "C2f10": ("C2 floor 0.1", dict(step_scale_mode="gsm_equal_step", step_scale_floor=0.1)),
    "C2f50": ("C2 floor 0.5", dict(step_scale_mode="gsm_equal_step", step_scale_floor=0.5)),
    "C3m": ("C3 A at dt matched to B2", dict(step_scale_max_cells=1.0)),
    "C3d06": ("C3 A dt 0.6, cap 1", dict(dt=0.6, step_scale_max_cells=1.0)),
    "C3d10": ("C3 A dt 1.0, cap 1", dict(dt=1.0, step_scale_max_cells=1.0)),
    "C4a": ("C4 error-prop, dt_max 0.6, ref 3", dict(step_scale_mode="constant_errprop", dt=0.6, step_scale_ref=3.0, step_scale_max_cells=1.0)),
    "C4b": ("C4 dt_max 0.6, ref 10", dict(step_scale_mode="constant_errprop", dt=0.6, step_scale_ref=10.0, step_scale_max_cells=1.0)),
    "C4c": ("C4 dt_max 1.0, ref 3", dict(step_scale_mode="constant_errprop", dt=1.0, step_scale_ref=3.0, step_scale_max_cells=1.0)),
    "C4d": ("C4 dt_max 1.0, ref 10", dict(step_scale_mode="constant_errprop", dt=1.0, step_scale_ref=10.0, step_scale_max_cells=1.0)),
    "C4e": ("C4 dt_max 0.6, ref 30", dict(step_scale_mode="constant_errprop", dt=0.6, step_scale_ref=30.0, step_scale_max_cells=1.0)),
    "C4f": ("C4 dt_max 1.0, ref 30", dict(step_scale_mode="constant_errprop", dt=1.0, step_scale_ref=30.0, step_scale_max_cells=1.0)),
}
MAIN = ["A", "B1", "B1f01", "B1f10", "B3n", "B2", "B2c3", "B2nc", "B3p", "B4n", "B4s", "B4snc", "B4o", "B4oc"]


def metrics(geoms, target):
    """Accuracy and validity measured from the output geometries (linear relative error of area shares)."""
    a = np.array([g.area for g in geoms])
    t = np.asarray(target, float)
    lin = np.abs((a / a.sum()) / (t / t.sum()) - 1)
    arr = np.asarray(geoms, dtype=object)
    return dict(mean=float(lin.mean()), max=float(lin.max()), gt10=float((lin > 0.10).mean()),
                invalid=int((~shapely.is_valid(arr)).sum()))


def load_case(case):
    if case in ("states", "states_mr", "horiz", "tang", "tilt"):
        g, col, sc, kw = data.load_us_census(population=True).reset_index(drop=True), "Population", 1.0, {}
        if case in ("horiz", "tang", "tilt"):
            mod = {"horiz": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3),
                   "tang": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
                   "tilt": DirectionalTensor(theta=np.pi / 6, Dpar=4, Dperp=0.3)}[case]
            BAL = MorphOptions.preset_balanced()
            kw = {k: getattr(BAL, k) for k in ("dt", "Dx", "Dy", "density_mod", "mean_tol", "max_tol") if hasattr(BAL, k)}
            kw["anisotropy"] = mod
            sc = 1e-6
        return g, col, sc, kw, 400
    if case == "districts":
        return data.load_us_census(level="congressional_district").reset_index(drop=True), "Population", 1.0, {}, 400
    if case == "counties":
        return gpd.read_parquet(COUNTIES), "total_votes", 1e-6, {}, 300
    raise ValueError(case)


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


def run_one(g, col, sc, grid_size, n_iter, extra, rr, dt=None, grid=None):
    kw = dict(extra)
    if dt is not None:
        kw["dt"] = dt
    if grid is not None:
        kw["grid"] = grid
    else:
        kw["grid_size"] = grid_size
    o = MorphOptions(show_progress=False, n_iter=n_iter, area_scale=sc, refresh_on_rise=rr, **kw)
    load = open("/proc/loadavg").read().split()[0]
    with Counter() as c:
        t = time.perf_counter()
        r = morph_gdf(g, col, options=o)
        wall = time.perf_counter() - t
    cv = r.convergence
    score = np.maximum(cv.mean_log_errors / np.log2(1 + o.mean_tol), cv.max_log_errors / np.log2(1 + o.max_tol))
    m = metrics(list(r.latest.geometry), g[col].to_numpy(float))
    rises = score[1:] > score[:-1]
    return dict(status=str(r.status.value), it=int(len(score)), rec=c.n["fft"], wall=wall, load=load,
                best=float(score.min()), final=float(score[-1]), rises20=int((rises & (score[:-1] < 20)).sum()),
                spike=float(max([score[i + 1] / score[i] for i in range(len(score) - 1) if score[i] < 20 and rises[i]], default=1.0)),
                first_below1=int(np.argmax(score < 1)) + 1 if (score < 1).any() else None,
                score=[round(float(x), 4) for x in score], **m), r


CONTROLS = ["A", "B1", "B2", "C1", "C2", "C2f10", "C2f50", "C3m", "C3d06", "C3d10", "C4a", "C4b", "C4c", "C4d"]
