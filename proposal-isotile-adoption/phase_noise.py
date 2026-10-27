"""How much does a grid layout change when only the position of the lattice relative to the data changes?

The wrappers anchor the lattice differently from the current classes (region center instead of the lower-left corner for
squares and hexagons, the origin for triangles and quadrilaterals), so the layouts differ from the current ones by a
shift of the lattice. This script measures the size of that effect as the spread of one placement metric over shifts of
the lattice by fractions of a tile, for the same code. The result sets the tolerance of the golden comparison.

For a code version (put its sources on PYTHONPATH), the 49 US states are laid out with the grid layout and one tile per
state; before each run ``generate`` of the tiling is wrapped so that the requested bounds move by (dx, dy) tile sizes.
Metric: mean distance between the centroid of a state and the center of its tile, in tile sizes.

    PYTHONPATH=<src> python phase_noise.py <label> <tiling> > phase_noise_<label>_<tiling>.txt
"""

from __future__ import annotations

import sys
import warnings

import numpy as np

PHASES = [(0.0, 0.0), (0.25, 0.5), (0.5, 0.25), (0.75, 0.75), (0.4, 0.9), (0.9, 0.1)]


def main(label: str, tiling: str) -> None:
    from carto_flow.data import load_us_census
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram import tiling as tmod
    from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout

    gdf = load_us_census(population=True).reset_index(drop=True)
    cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
    cls = {"hexagon": tmod.HexagonTiling, "square": tmod.SquareTiling, "triangle": tmod.TriangleTiling}[tiling]
    results = []
    for dx, dy in PHASES:
        shift = {}

        def patched(self, bounds=tmod.DEFAULT_BOUNDS, n_tiles=None, tile_size=None, margin=0.1, **kw):
            if tile_size is not None:
                s = tile_size * (1.0 if not isinstance(self, tmod.HexagonTiling) else np.sqrt(3.0))
                bounds = (bounds[0] + dx * s, bounds[1] + dy * s, bounds[2] + dx * s, bounds[3] + dy * s)
            return shift["orig"](self, bounds, n_tiles, tile_size, margin, **kw)

        shift["orig"] = cls.generate
        cls.generate = patched
        try:
            lay = GridBasedLayout(tiling=cls() if tiling != "triangle" else tmod.TriangleTiling.equilateral())
            res = create_layout(gdf, layout=lay, show_progress=False)
        finally:
            cls.generate = shift["orig"]
        tr = res.tiling_result
        c = tr.centers[np.asarray(res.assignments)]
        d = np.hypot(*(c - cent).T) / tr.tile_size
        results.append((dx, dy, float(d.mean()), float(d.max())))
        print(f"{label} {tiling} phase ({dx:.2f}, {dy:.2f}): mean {d.mean():.3f}, max {d.max():.3f}", flush=True)
    means = [r[2] for r in results]
    print(f"{label} {tiling}: mean displacement over {len(PHASES)} lattice phases {min(means):.3f} to {max(means):.3f} (spread {max(means) - min(means):.3f})")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    main(sys.argv[1], sys.argv[2])
