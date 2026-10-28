"""states grid, preset tree, offset (0.9, 0.1): mean region-to-tile distance after each stage of the grid layout (every
Hungarian solve of assign_to_grid_hungarian, fill_internal_holes, _fix_island_assignments), and the number of tiles
that hole filling and island fixing move. python tree_iteration_probe.py <straight|curved>"""
import functools
import sys
import warnings

import isotile
import numpy as np

warnings.simplefilter("ignore")
if sys.argv[1] == "straight":
    orig = isotile.IsohedralTiling.fill_region
    isotile.IsohedralTiling.fill_region = functools.wraps(orig)(lambda self, *a, **kw: orig(self, *a, outline="straight", **kw))
import carto_flow.symbol_cartogram.layouts.grid._placement as pl
from carto_flow.data import load_us_census
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
from carto_flow.symbol_cartogram.tiling import IsohedralTiling

gdf = load_us_census(population=True).reset_index(drop=True)
cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
state = {}


def mean(c):
    return float((np.hypot(*(state["centers"][c] - cent).T) / state["size"]).mean())


def wrap(name):
    f = getattr(pl, name)

    @functools.wraps(f)
    def g(assignments, *a, **kw):
        out = f(assignments, *a, **kw)
        print(f"{name}: mean {mean(assignments):.3f} -> {mean(out):.3f}, tiles moved {int((np.asarray(out) != np.asarray(assignments)).sum())}")
        return out

    return g


orig_lsa = pl.linear_sum_assignment
pl.linear_sum_assignment = lambda cost: (lambda rc: (print(f"hungarian solve: mean {mean(rc[1]):.3f}") or rc))(orig_lsa(cost))
orig_assign = pl.assign_to_grid_hungarian


def assign(centroids, grid_centers, *a, **kw):
    state["centers"] = grid_centers
    return orig_assign(centroids, grid_centers, *a, **kw)


pl.assign_to_grid_hungarian = assign
pl.fill_internal_holes = wrap("fill_internal_holes")
pl._fix_island_assignments = wrap("_fix_island_assignments")
t = IsohedralTiling.from_preset("tree").with_offset((0.9, 0.1))
import carto_flow.symbol_cartogram.tiling as tm

state["size"] = None
orig_gen = tm._IsotileTiling.generate


def gen(self, *a, **kw):
    r = orig_gen(self, *a, **kw)
    state["size"] = r.tile_size
    return r


tm._IsotileTiling.generate = gen
res = create_layout(gdf, layout=GridBasedLayout(tiling=t), show_progress=False)
print("final mean", round(mean(np.asarray(res.assignments)), 3), "tiles", len(state["centers"]))
