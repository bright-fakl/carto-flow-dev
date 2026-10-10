"""GSM-style passes on carto-flow's own rasterizer and FFT solver (feasibility prototype, not library code).

Derived from the talk-work prototype proto_gsm.py (scripts/proto_gsm.py), adapted to the current API:
takes a Grid, records a per-pass trace (score, linear errors, validity, cost counters), optional fixed
step count, optional velocity modulator. Per pass: rasterize the current polygons, solve the Poisson
problem for the potential gradient (v = grad phi, laplace phi = rho - rho_bar), then carry ALL vertices
from t=0 to t=1 through v(x,t) = grad_phi(x) / rho(x,t) with rho(x,t) = rho_bar + (1-t)(rho0(x) - rho_bar)
(explicit midpoint, adaptive or fixed steps). The blur of the rasterized density is annealed per pass.
"""
import time

import numpy as np
import shapely
from scipy.ndimage import gaussian_filter, map_coordinates

from carto_flow.flow_cartogram.density import compute_density_field_from_geometries as raster
from carto_flow.flow_cartogram.velocity import VelocityComputerFFTW

MEAN_TOL, MAX_TOL = 0.05, 0.10  # MorphOptions defaults


def metrics(geoms, target):
    """Accuracy and validity measured from output geometries."""
    a = np.array([g.area for g in geoms])
    t = np.asarray(target, float)
    ratio = (a / a.sum()) / (t / t.sum())
    lin = np.abs(ratio - 1)
    lg = np.abs(np.log2(np.maximum(ratio, 1e-12)))
    score = max(lg.mean() / np.log2(1 + MEAN_TOL), lg.max() / np.log2(1 + MAX_TOL))
    arr = np.asarray(geoms, dtype=object)
    valid = shapely.is_valid(arr)
    reasons = shapely.is_valid_reason(arr[~valid])
    selfint = int(sum("Self-intersection" in r for r in reasons))
    return dict(
        mean=float(lin.mean()),
        max=float(lin.max()),
        gt10=float((lin > 0.10).mean()),
        score=float(score),
        invalid=int((~valid).sum()),
        selfint=selfint,
    )


def run(geoms0, vals, grid, blur0=0.0, blur_decay=0.5, max_pass=15, fixed_steps=None, tol_cells=0.02,
        modulator=None, stop_score=None, verbose=False):
    geoms = np.array(list(geoms0), dtype=object)
    vals = np.asarray(vals, float)
    comp = VelocityComputerFFTW(grid)
    rho_bar = vals.sum() / sum(g.area for g in geoms)
    x0, y0, dx, dy = grid.x_coords[0], grid.y_coords[0], grid.dx, grid.dy
    xmin, xmax, ymin, ymax = grid.x_coords[0], grid.x_coords[-1], grid.y_coords[0], grid.y_coords[-1]
    trace = [dict(p=0, **metrics(geoms, vals), steps=0, rej=0, evals=0, wall=0.0, t_raster=0.0, t_fft=0.0, t_int=0.0)]
    cum = dict(evals=0, wall=0.0)
    for p in range(max_pass):
        t_start = time.perf_counter()
        rho0, gmask = raster(list(geoms), vals, grid, rho_bar, return_geometry_mask=True)
        t_r = time.perf_counter() - t_start
        if blur0 > 0:
            s = blur0 * blur_decay**p
            mu = rho0.mean()
            rho0 = gaussian_filter(rho0, sigma=s, mode="nearest")
            rho0 *= mu / rho0.mean()
        t = time.perf_counter()
        vx, vy = comp.compute(rho0)
        vx, vy = vx.copy(), vy.copy()
        if modulator is not None:
            vx, vy = modulator(vx, vy, grid, gmask)
        t_f = time.perf_counter() - t
        t = time.perf_counter()
        P = shapely.get_coordinates(geoms)

        def samp(arr, X):
            return map_coordinates(arr, [(X[:, 1] - y0) / dy, (X[:, 0] - x0) / dx], order=1, mode="nearest")

        def vel(X, tt):
            rho = rho_bar + (1.0 - tt) * (samp(rho0, X) - rho_bar)
            return np.column_stack([samp(vx, X), samp(vy, X)]) / rho[:, None]

        evals = steps = rej = 0
        ok = True
        if fixed_steps:
            h = 1.0 / fixed_steps
            for k in range(fixed_steps):
                tt = k * h
                P = P + h * vel(P + 0.5 * h * vel(P, tt), tt + 0.5 * h)
                evals += 2
                steps += 1
        else:
            tt, dt = 0.0, 0.05
            tol = tol_cells * min(dx, dy)
            while tt < 1.0 - 1e-12:
                dt = min(dt, 1.0 - tt)
                v1 = vel(P, tt)
                eul = P + dt * v1
                mid = P + dt * vel(P + 0.5 * dt * v1, tt + 0.5 * dt)
                evals += 2
                err = np.abs(mid - eul).max()
                if err > tol or mid[:, 0].min() < xmin or mid[:, 0].max() > xmax or mid[:, 1].min() < ymin or mid[:, 1].max() > ymax:
                    dt *= 0.5
                    rej += 1
                    if dt < 1e-5:
                        ok = False
                        break
                    continue
                P = mid
                tt += dt
                steps += 1
                dt *= 1.5
        t_i = time.perf_counter() - t
        if not ok:
            if verbose:
                print(f"  pass {p}: step collapsed", flush=True)
            break
        geoms = shapely.set_coordinates(geoms.copy(), P)
        cum["wall"] += time.perf_counter() - t_start
        cum["evals"] += evals
        m = metrics(geoms, vals)  # not counted in wall
        trace.append(dict(p=p + 1, **m, steps=steps, rej=rej, evals=evals, wall=cum["wall"], t_raster=t_r, t_fft=t_f, t_int=t_i))
        if verbose:
            print(f"  pass {p+1}: steps {steps} rej {rej} score {m['score']:.2f} mean {100*m['mean']:.2f}% "
                  f"max {100*m['max']:.1f}% invalid {m['invalid']} wall {cum['wall']:.1f}s", flush=True)
        if stop_score is not None and m["score"] < stop_score:
            break
    return dict(trace=trace, geoms=list(geoms), passes=len(trace) - 1, evals=cum["evals"], wall=cum["wall"])
