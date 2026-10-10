"""B1 (two interpolations and a division per vertex) versus B3 (precomputed field W_k = v f_k, one interpolation).

Frozen state at the start of a morph: per-step cost of the displacement part (median of 15 repeats) and the
difference of the displacements of one step at t = 0, 0.5, 0.9 (cells). Writes ../data/bench_precompute.json."""
import json
import os
import time

from common import *
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries as raster
from carto_flow.flow_cartogram.displacement import displace_coords_numba, max_abs_velocity
from carto_flow.flow_cartogram.step_scale import displace_scaled, max_scaled_abs, scaled_field
from carto_flow.flow_cartogram.options import MorphOptions as MO

out = {}
for case, grids in (("states", (256, 512, 1024)), ("districts", (256, 512, 1024)), ("counties", (256, 512, 1024))):
    g, col, sc, kw, _ = load_case(case)
    geoms = list(g.geometry)
    vals = g[col].to_numpy(float)
    coords = shapely.get_coordinates(geoms)
    rho_bar = vals.sum() / sum(x.area for x in geoms)
    for gs in grids:
        o = MO(grid_size=gs, area_scale=sc)
        grid = o.get_grid(o._calculate_bounds_from_geometries(geoms))
        rho0 = raster(geoms, vals, grid, rho_bar)
        vx, vy = VelocityComputerFFTW(grid).compute(rho0)
        vx, vy = vx / np.hypot(vx, vy).max(), vy / np.hypot(vx, vy).max()
        cell = min(grid.dx, grid.dy)
        fl = 0.02

        def b1(t):
            c = 0.2 * cell / max_scaled_abs(vx, vy, rho0, t, rho_bar, fl)
            return displace_scaled(coords, grid.x_coords, grid.y_coords, vx, vy, rho0, c, grid.dx, grid.dy, t, rho_bar, fl, True, 0.0)

        def b3(t):
            wx, wy, m = scaled_field(vx, vy, rho0, t, rho_bar, fl)
            c = 0.2 * cell / m
            return displace_scaled(coords, grid.x_coords, grid.y_coords, wx, wy, rho0, c, grid.dx, grid.dy, t, rho_bar, fl, False, 0.0)

        def a(t):
            c = 0.2 * cell / max_abs_velocity(vx, vy)
            return displace_scaled(coords, grid.x_coords, grid.y_coords, vx, vy, rho0, c, grid.dx, grid.dy, t, rho_bar, fl, False, 0.0)

        row = dict(n_vertices=len(coords), cells=int(np.prod(vx.shape)))
        for name, f in (("A", a), ("B1", b1), ("B3", b3)):
            f(0.5)
            ts = []
            for _ in range(15):
                t0 = time.perf_counter()
                f(0.5)
                ts.append(time.perf_counter() - t0)
            row[f"ms_{name}"] = 1e3 * float(np.median(ts))
        for t in (0.0, 0.5, 0.9):
            d1, d3 = b1(t) - coords, b3(t) - coords
            diff = np.hypot(*(d1 - d3).T) / (0.2 * cell)  # in units of the step length of the fastest point
            row[f"diff_t{t}_max"] = float(diff.max())
            row[f"diff_t{t}_p99"] = float(np.quantile(diff, 0.99))
            row[f"rel_t{t}"] = float(np.hypot(*(d1 - d3).T).sum() / np.hypot(*d1.T).sum())
        row["load"] = open("/proc/loadavg").read().split()[0]
        out[f"{case}_{gs}"] = row
        print(case, gs, {k: round(v, 4) if isinstance(v, float) else v for k, v in row.items()}, flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "bench_precompute.json"), "w"), indent=1)
