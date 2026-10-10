"""Check the numba exact coverage against polygon clipping (shapely.intersection of each boundary cell)."""

import warnings

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.data as data
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries as f
from carto_flow.flow_cartogram.grid import Grid

warnings.filterwarnings("ignore")
SP = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/"


def clip_field(geoms, vals, grid):
    dx, dy, xs, ys = grid.dx, grid.dy, grid.x_coords, grid.y_coords
    rho = np.zeros_like(grid.X)
    cover = np.zeros_like(grid.X)
    for geom, val in zip(geoms, vals):
        minx, miny, maxx, maxy = geom.bounds
        c0 = int(np.searchsorted(xs, minx - 0.5 * dx))
        c1 = int(np.searchsorted(xs, maxx + 0.5 * dx, side="right"))
        r0 = int(np.searchsorted(ys, miny - 0.5 * dy))
        r1 = int(np.searchsorted(ys, maxy + 0.5 * dy, side="right"))
        X, Y = np.meshgrid(xs[c0:c1], ys[r0:r1])
        b = shapely.box(X - 0.5 * dx, Y - 0.5 * dy, X + 0.5 * dx, Y + 0.5 * dy)
        fr = shapely.area(shapely.intersection(geom, b)) / (dx * dy)
        rho[r0:r1, c0:c1] += fr * val / geom.area
        cover[r0:r1, c0:c1] += fr
    return rho + np.clip(1 - cover, 0, 1) * vals.sum() / sum(g.area for g in geoms)


sets = {
    "states": (data.load_us_census(population=True).reset_index(drop=True), "Population"),
    "districts": (data.load_us_census(level="congressional_district").reset_index(drop=True), "Population"),
    "counties": (gpd.read_parquet(SP + "counties_prepared.parquet").iloc[:500], "total_votes"),
}
for name, (g, col) in sets.items():
    geoms, vals = list(g.geometry), g[col].to_numpy(float)
    for n in (64, 256):
        grid = Grid.from_bounds(g.total_bounds, size=n, margin=0.5)
        a = f(geoms, vals, grid, coverage="exact")
        b = clip_field(geoms, vals, grid)
        print(name, n, "max relative difference", float(np.abs(a - b).max() / np.abs(b).max()))
