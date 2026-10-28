# Produces fig_slivers.png: tiles selected with outline="straight" (left) and "curved" (right) at margin 0, with the
# part of the region that the tiles leave uncovered in red. Run from an isotile checkout on the branch
# cover-curved-outline: `uv run --with matplotlib python make_figures.py` (copy this file there or pass its path).
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shapely

from isotile import IsohedralTiling

REGION = (0.0, 0.0, 10.0, 6.0)
CASES = [("wavy_triangle", 100, None), ("puzzle_piece", 100, (0.0, -0.3, 4.0, 1.5)), ("arrow_quad", 100, (-0.3, 4.2, 3.0, 6.3))]  # name, n_tiles, zoom window

fig, axes = plt.subplots(len(CASES), 2, figsize=(11, 8))
for row, (name, n, zoom) in zip(axes, CASES, strict=True):
    tiling = IsohedralTiling.from_preset(name)
    box = shapely.box(*REGION)
    for ax, outline in zip(row, ("straight", "curved"), strict=True):
        tiles = tiling.fill_region(REGION, n_tiles=n, margin=0.0, outline=outline)
        polys = tiles.polygons()
        gap = box.difference(shapely.union_all(polys))  # exact, shapely
        for p in polys:
            ax.fill(*p.exterior.xy, fc="#cfe2f3", ec="#4a6f8a", lw=0.5)
        for g in getattr(gap, "geoms", [gap]):
            if g.area > 1e-9 * box.area:  # smaller components are rounding noise along shared edges
                ax.fill(*g.exterior.xy, fc="#d62728", ec="none")
        x0, y0, x1, y1 = REGION
        ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], "k--", lw=0.8)
        wx0, wy0, wx1, wy1 = zoom or (x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5)
        ax.set_xlim(wx0, wx1)
        ax.set_ylim(wy0, wy1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f'{name}, outline="{outline}": {len(tiles)} tiles, uncovered {gap.area / box.area:.1e}', fontsize=9)
fig.tight_layout()
fig.savefig("fig_slivers.png", dpi=130)
