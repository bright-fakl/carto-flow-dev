"""Side-by-side figures of the grid and mosaic layouts, tactile-based tilings (before) against the isotile tilings (after).

    python layout_cases.py run before before.pkl     # with the sources of a9b4b7f (tactile) on PYTHONPATH
    python layout_cases.py run after after.pkl       # with the sources of the pull request
    python make_figures.py before.pkl after.pkl <output directory>

Writes fig_states_grid.png, fig_states_mosaic.png, fig_districts_grid.png and fig_districts_mosaic.png. Tiles are colored by
region (the same color before and after); the black outlines are the input regions (bundled census data). The titles give
the mean distance of a region from its tiles in tile sizes, the number of regions split into more than one block of tiles,
and the wall time of the run (single runs on a machine with other jobs; use the table of the page for timing).
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon

from carto_flow.data import load_us_census

FIGURES = {
    "fig_states_grid.png": ("states", "grid", ["hexagon", "square", "triangle", "scalloped_hexagon"]),
    "fig_states_mosaic.png": ("states", "mosaic", ["hexagon", "square", "triangle", "scalloped_hexagon"]),
    "fig_districts_grid.png": ("districts", "grid", ["hexagon", "square"]),
    "fig_districts_mosaic.png": ("districts", "mosaic", ["hexagon", "square", "triangle", "scalloped_hexagon"]),
}


def draw(ax, result, outlines, n_regions):
    rng = np.random.default_rng(3)
    palette = plt.get_cmap("tab20")(rng.permutation(n_regions) % 20)
    patches = []
    colors = []
    for wkb, region in zip(result["tile_polygons_wkb"], result["tile_region"], strict=True):
        poly = shapely.from_wkb(wkb)
        patches.append(MplPolygon(np.array(poly.exterior.coords), closed=True))
        colors.append(palette[region])
    ax.add_collection(PatchCollection(patches, facecolors=colors, edgecolors="#ffffff", linewidths=0.3))
    for geom in outlines:
        for part in getattr(geom, "geoms", [geom]):
            ax.plot(*part.exterior.xy, color="black", lw=0.35)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")


def main(before_path: str, after_path: str, out: str) -> None:
    before = pickle.load(open(before_path, "rb"))
    after = pickle.load(open(after_path, "rb"))
    data = {
        "states": load_us_census(population=True).reset_index(drop=True),
        "districts": load_us_census(population=True, level="congressional_district").reset_index(drop=True),
    }
    for filename, (source, layout, tilings) in FIGURES.items():
        gdf = data[source]
        fig, axes = plt.subplots(len(tilings), 2, figsize=(12, 3.6 * len(tilings) * (1.0 if source == "states" else 1.1)))
        for row, tiling in enumerate(tilings):
            name = f"{source} {layout} {tiling}"
            for col, (label, results) in enumerate((("before", before), ("after", after))):
                ax = axes[row, col]
                r = results[name]
                draw(ax, r, list(gdf.geometry), len(gdf))
                ax.set_title(
                    f"{tiling}, {label}: distance {r['disp_mean']:.2f}, split {r['split']}",
                    fontsize=9,
                )
        fig.suptitle(f"{source}, {layout} layout", fontsize=11)
        fig.tight_layout()
        fig.savefig(Path(out) / filename, dpi=110)
        plt.close(fig)
        print(filename)


if __name__ == "__main__":
    main(*sys.argv[1:4])
