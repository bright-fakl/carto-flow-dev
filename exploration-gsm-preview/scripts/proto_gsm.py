"""Prototype: GSM-style passes inside carto-flow (feasibility test, not library code; written from the published idea, not from cartogram-cpp source).
Per pass: rasterise current polygons (carto-flow's own rasteriser) -> velocity potential gradient (carto-flow's FFT solver) -> carry ALL vertices from t=0 to t=1 with an
adaptive explicit-midpoint integrator through  v(x,t) = grad_phi(x) / rho(x,t),  rho(x,t) = rho_bar + (1-t)(rho0(x) - rho_bar)   (continuity: rho*v is static => rho(t) linear).
carto-flow's v = grad(phi) with  laplace(phi) = rho - rho_bar, so v/rho has units of length and t=1 completes the equalisation of the (rasterised) density.
Usage as module: run(gdf, col, grid_size, blur0, ...)."""
import time, warnings; warnings.filterwarnings("ignore")
import numpy as np, shapely
from scipy.ndimage import map_coordinates, gaussian_filter
from carto_flow.flow_cartogram.grid import Grid
from carto_flow.flow_cartogram.velocity import VelocityComputerFFTW
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries as raster

def shares_err(geoms, target):
    a = np.array([x.area for x in geoms]); t = np.asarray(target, float)
    rel = (a / a.sum()) / (t / t.sum()) - 1
    return np.abs(rel)

def run(gdf, col, grid_size=256, margin=0.25, blur0=0.0, max_pass=40, tol_cells=0.02, target_max=0.01, verbose=True):
    geoms = np.array(list(gdf.geometry), dtype=object); vals = gdf[col].to_numpy(float); t_all = vals
    grid = Grid.from_bounds(tuple(gdf.total_bounds), size=grid_size, margin=margin)
    comp = VelocityComputerFFTW(grid)
    rho_bar = vals.sum() / sum(g.area for g in geoms)
    x0, y0, dx, dy = grid.x_coords[0], grid.y_coords[0], grid.dx, grid.dy
    best = (np.inf, geoms.copy(), 0); hist = []; inner_total = 0; t0 = time.perf_counter()
    for p in range(max_pass):
        rho0 = raster(list(geoms), vals, grid, rho_bar)
        if blur0 > 0:
            s = blur0 * 2 ** (-0.5 * p)
            mu = rho0.mean(); rho0 = gaussian_filter(rho0, sigma=s, mode="nearest"); rho0 *= mu / rho0.mean()
        vx, vy = comp.compute(rho0); vx, vy = vx.copy(), vy.copy()
        P = shapely.get_coordinates(geoms)
        def samp(arr, X):
            return map_coordinates(arr, [(X[:, 1] - y0) / dy, (X[:, 0] - x0) / dx], order=1, mode="nearest")
        def vel(X, t):
            rho = rho_bar + (1.0 - t) * (samp(rho0, X) - rho_bar)
            return np.column_stack([samp(vx, X), samp(vy, X)]) / rho[:, None]
        t, dt, steps = 0.0, 0.05, 0
        tol = tol_cells * min(dx, dy)
        xmin, xmax = grid.x_coords[0], grid.x_coords[-1]; ymin, ymax = grid.y_coords[0], grid.y_coords[-1]
        ok = True
        while t < 1.0 - 1e-12:
            dt = min(dt, 1.0 - t)
            v1 = vel(P, t)
            eul = P + dt * v1
            mid = P + dt * vel(P + 0.5 * dt * v1, t + 0.5 * dt)
            err = np.abs(mid - eul).max()
            if err > tol or mid[:, 0].min() < xmin or mid[:, 0].max() > xmax or mid[:, 1].min() < ymin or mid[:, 1].max() > ymax:
                dt *= 0.5
                if dt < 1e-5: ok = False; break
                continue
            P = mid; t += dt; steps += 1; dt *= 1.5
        inner_total += steps
        if not ok:
            if verbose: print(f"  pass {p}: time step collapsed, stopping", flush=True)
            break
        geoms = shapely.set_coordinates(geoms.copy(), P)
        e = shares_err(geoms, t_all); valid = int(shapely.is_valid(geoms).sum())
        hist.append((p, steps, round(100 * e.max(), 2), round(100 * np.median(e), 2), valid))
        if verbose: print(f"  pass {p}: {steps} inner steps, max err {100*e.max():.2f} %, median {100*np.median(e):.2f} %, valid {valid}/{len(geoms)}", flush=True)
        if e.max() < best[0]: best = (e.max(), geoms.copy(), p)
        if e.max() < target_max: break
    return dict(geoms=list(geoms), best_geoms=list(best[1]), best_pass=best[2], hist=hist, passes=len(hist), inner=inner_total, time=time.perf_counter() - t0)
