import os
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("NUMBA_NUM_THREADS", "4")
import sys

import geopandas as gpd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carto_flow.data as data
import carto_flow.flow_cartogram.algorithm as alg
import gsm_proto as gp
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.velocity import VelocityComputerFFTW

COUNTIES = os.environ.get(
    "COUNTIES_PARQUET",
    "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/counties_prepared.parquet",
)
# one field recompute (rasterize + FFT) in units of plain advection steps (exploration-adaptive-recompute page)
COST_RATIO = {("states", 128): 9.2, ("states", 256): 12.0, ("districts", 256): 20.9, ("counties", 256): 47.5}


def load(case):
    if case == "states":
        return data.load_us_census(population=True).reset_index(drop=True), "Population", 1.0
    if case == "districts":
        return data.load_us_census(level="congressional_district").reset_index(drop=True), "Population", 1.0
    if case == "counties":
        return gpd.read_parquet(COUNTIES), "total_votes", 1e-6
    raise ValueError(case)


class Counter:
    """Counts and times rasterizations and FFT solves made by the baseline loop."""

    def __enter__(self):
        self.n = dict(raster=0, fft=0)
        self.tr = self.tf = 0.0
        self.r0 = alg.compute_density_field_from_geometries
        self.f0 = VelocityComputerFFTW.compute

        def r(*a, **k):
            t = time.perf_counter()
            out = self.r0(*a, **k)
            self.tr += time.perf_counter() - t
            self.n["raster"] += 1
            return out

        def f(s, *a, **k):
            t = time.perf_counter()
            out = self.f0(s, *a, **k)
            self.tf += time.perf_counter() - t
            self.n["fft"] += 1
            return out

        alg.compute_density_field_from_geometries = r
        VelocityComputerFFTW.compute = f
        return self

    def __exit__(self, *a):
        alg.compute_density_field_from_geometries = self.r0
        VelocityComputerFFTW.compute = self.f0


def baseline(g, col, area_scale, grid_size, n_iter=400, **kw):
    o = MorphOptions(show_progress=False, grid_size=grid_size, n_iter=n_iter, area_scale=area_scale, **kw)
    with Counter() as c:
        t = time.perf_counter()
        r = morph_gdf(g, col, options=o)
        wall = time.perf_counter() - t
    cv = r.convergence
    score = np.maximum(cv.mean_log_errors / np.log2(1 + o.mean_tol), cv.max_log_errors / np.log2(1 + o.max_tol))
    m = gp.metrics(list(r.latest.geometry), g[col].to_numpy(float))
    out = dict(status=str(r.status.value), it=int(len(score)), rec=c.n["fft"], rast=c.n["raster"], wall=wall,
               t_raster=c.tr, t_fft=c.tf, score=score.tolist(), final=m, best=float(score.min()))
    return out, r


def load_avg():
    return open("/proc/loadavg").read().split()[0]
