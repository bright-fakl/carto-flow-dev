"""Shared helpers: cases, one-run driver with independent accuracy / stability metrics.

Run from the carto-flow worktree on branch investigate/area-coverage with `uv run python`.
A variant is a dict(cov=None|2|4|8|"exact", ro=refresh_on_rise (None or 0.01), dt=..., re=recompute_every).
"""

import os
import time
import warnings

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.data as data
import carto_flow.flow_cartogram.algorithm as alg
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor
from carto_flow.flow_cartogram.stall import StallMonitor, cycle_length

warnings.filterwarnings("ignore")
SP = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/"
COUNTIES = SP + "counties_prepared.parquet"

COV_NAME = {None: "center", 2: "s2", 4: "s4", 8: "s8", "exact": "exact"}


def load_case(case):
    """Return (gdf, column, base option dict)."""
    states = data.load_us_census(population=True).reset_index(drop=True)
    bal = MorphOptions.preset_balanced().copy_with(area_scale=1e-6, n_iter=400, show_progress=False)
    aniso = {
        "horiz": DirectionalTensor(theta=0, Dpar=4, Dperp=0.3),
        "tang": DirectionalTensor.tangential(Dpar=4, Dperp=0.3),
        "tilt": DirectionalTensor(theta=np.pi / 6, Dpar=4, Dperp=0.3),
    }
    if case == "states":
        return states, "Population", dict(n_iter=400)
    if case in aniso:
        base = {k: getattr(bal, k) for k in ("dt", "Dx", "Dy", "density_mod", "mean_tol", "max_tol")}
        base.update(area_scale=1e-6, n_iter=400, anisotropy=aniso[case])
        return states, "Population", base
    if case == "districts":
        return data.load_us_census(level="congressional_district").reset_index(drop=True), "Population", dict(n_iter=400)
    if case == "counties":
        return gpd.read_parquet(COUNTIES), "total_votes", dict(area_scale=1e-6, n_iter=int(os.environ.get("NITER", 300)))
    raise KeyError(case)


def score_hist(res, o):
    c = res.convergence
    return np.maximum(c.mean_log_errors / np.log2(1 + o.mean_tol), c.max_log_errors / np.log2(1 + o.max_tol))


def share_errors(geoms, targets):
    """Linear relative error of area shares |a_i/sum(a) / (t_i/sum(t)) - 1| from output geometries."""
    a = shapely.area(np.asarray(list(geoms), dtype=object))
    t = np.asarray(targets, dtype=float)
    return np.abs((a / a.sum()) / (t / t.sum()) - 1.0)


def stall_replay(res, o, patience=4):
    """Step (1-based) at which the stall rule of the current stack would stop the run, or None."""
    c = res.convergence
    lm, lx = np.log2(1 + o.mean_tol), np.log2(1 + o.max_tol)
    mon = StallMonitor(patience, o.stall_min_improvement, cycle_length(o.recompute_every))
    for k in range(len(c.mean_log_errors)):
        if (c.mean_log_errors[k] / lm < 1) and (c.max_log_errors[k] / lx < 1):
            return None
        if mon.update(k, c.mean_log_errors[k] / lm, c.max_log_errors[k] / lx):
            return k + 1
    return None


def stability(s):
    s = np.asarray(s)
    up = s[1:] > s[:-1]
    low = s[:-1] < 20
    rises20 = int(np.sum(up & low))
    spike = float(np.max((s[1:] / s[:-1])[low]) if low.any() else 1.0)
    return rises20, spike


def run(g, col, base, v, grid, patience=None, extra=None):
    """One morph run. Returns (metrics dict, result)."""
    kw = dict(base)
    kw.update(dt=v.get("dt", kw.get("dt", 0.2)), recompute_every=v.get("re", 10), refresh_on_rise=v.get("ro", 0.01))
    kw.update(extra or {})
    o = MorphOptions(
        **{**dict(show_progress=False, grid_size=grid, stall_patience=patience, benchmark=True, density_coverage=v.get("cov")), **kw}
    )
    steps = {"n": 0, "refresh": []}
    orig_d, orig_e = alg.compute_density_field_from_geometries, alg.compute_error_metrics

    def d(*a, **k):
        steps["refresh"].append(steps["n"])
        return orig_d(*a, **k)

    def e(*a, **k):
        steps["n"] += 1
        return orig_e(*a, **k)

    alg.compute_density_field_from_geometries, alg.compute_error_metrics = d, e
    load = os.getloadavg()[0]
    try:
        t0 = time.perf_counter()
        res = morph_gdf(g, col, options=o)
        wall = time.perf_counter() - t0
    finally:
        alg.compute_density_field_from_geometries, alg.compute_error_metrics = orig_d, orig_e
    return summarize(res, o, g, col, grid, steps, wall, load), res


def summarize(res, o, g, col, grid, steps, wall, load):
    s = score_hist(res, o)
    b = res.benchmark
    it = len(s)
    rec = b.density_calls
    step_s = (b.displacement_s + b.areas_s + b.errors_s) / it
    rec_s = (b.density_s + b.velocity_s) / max(rec, 1)
    ratio = rec_s / step_s
    err = share_errors(res.latest.geometry, g[col])
    cell = res.grid.dx * res.grid.dy
    area0 = shapely.area(np.asarray(list(g.geometry), dtype=object))
    cells0 = area0 / cell
    worst = np.argsort(err)[::-1][:5]
    rises20, spike = stability(s)
    stall_at = stall_replay(res, o)
    status = str(res.status.value if hasattr(res.status, "value") else res.status)
    return dict(
        status=status,
        it=it,
        rec=rec,
        ratio=float(ratio),
        cost=float(it + rec * ratio),
        wall=float(wall),
        raster_s=float(b.density_s),
        raster_per_call=float(b.density_s / max(rec, 1)),
        vel_per_call=float(b.velocity_s / max(rec, 1)),
        step_s=float(step_s),
        load=float(load),
        mean=float(res.latest.errors.mean_error_pct),
        max=float(res.latest.errors.max_error_pct),
        best=float(s.min()),
        final=float(s[-1]),
        ext_mean=float(err.mean() * 100),
        ext_max=float(err.max() * 100),
        ext_gt10=float((err > 0.10).mean() * 100),
        rises20=rises20,
        spike=spike,
        stall_at=stall_at,
        diverged=bool((~np.isfinite(s)).any() or s.max() > 10 * s[0]),
        valid=int(shapely.is_valid(np.asarray(list(res.latest.geometry), dtype=object)).sum()),
        n=len(g),
        worst=[(int(i), float(err[i] * 100), float(cells0[i])) for i in worst],
        score=s.tolist(),
        refresh_iters=list(steps["refresh"]),
    )


def warmup():
    """Compile the numba coverage kernel outside the timed runs."""
    from carto_flow.flow_cartogram.density import compute_density_field_from_geometries as f
    from carto_flow.flow_cartogram.grid import Grid

    sq = [shapely.box(0, 0, 1, 1)]
    f(sq, [1.0], Grid.from_bounds((0, 0, 1, 1), size=8, margin=0.5), coverage="exact")


warmup()


def key(v):
    return f"{COV_NAME[v.get('cov')]}|ro{v.get('ro', 0.01)}|dt{v.get('dt', 'base')}|re{v.get('re', 10)}"
