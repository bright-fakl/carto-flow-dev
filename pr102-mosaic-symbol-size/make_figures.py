# Produces the before/after figures for the MosaicLayout symbol-size fix: for each tiling and mosaic mode
# (one tile per region, tile_count, group_by) a side-by-side PNG of main (left) and the fix (right),
# and prints the overlapping-pair counts. Run from a carto-flow checkout: uv run python make_figures.py
# "Before" reproduces main by making Tiling.symbol_size_for_tile_size return tile_size.
# Uses bundled data only; PNGs are written next to this script.
import os
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

import carto_flow.data as examples
import carto_flow.symbol_cartogram as smb
from carto_flow.symbol_cartogram.tiling import Tiling

warnings.filterwarnings("ignore")
OUT = os.path.dirname(os.path.abspath(__file__))

states = examples.load_us_census(population=True)
states["Tiles"] = (states["Population"] / 2e6).round().clip(lower=1).astype(int)
dist = examples.load_us_census(level="congressional_district", population=True)
print(dist.columns.tolist())
gcol = next(c for c in ("STATE", "State", "state", "STATEFP") if c in dist.columns)

TILINGS = {
    "HexagonTiling": lambda: smb.HexagonTiling(),
    "SquareTiling": lambda: smb.SquareTiling(),
    "TriangleTiling.equilateral": lambda: smb.TriangleTiling.equilateral(),
    "QuadrilateralTiling.rhombus": lambda: smb.QuadrilateralTiling.rhombus(),
    "Isohedral scalloped_hexagon": lambda: smb.IsohedralTiling.from_preset("scalloped_hexagon"),
    "Isohedral wavy_square": lambda: smb.IsohedralTiling.from_preset("wavy_square"),
}
MODES = {
    "one_tile": (states, {}),
    "tile_count": (states, {"tile_count": "Tiles"}),
    "group_by": (dist, {"group_by": gcol}),
}


def overlaps(gdf):
    g = np.asarray(gdf.geometry)
    t = shapely.STRtree(g)
    a, b = t.query(g, predicate="intersects")
    k = a < b
    if not k.any():
        return 0
    return int((shapely.area(shapely.intersection(g[a[k]], g[b[k]])) > 1e-6 * shapely.area(g).mean()).sum())


orig = Tiling.symbol_size_for_tile_size
counts = {}
geoms = {}
for state in ("before", "after"):
    Tiling.symbol_size_for_tile_size = (lambda self, t: t) if state == "before" else orig
    for mode, (gdf, kw) in MODES.items():
        for tn, tf in TILINGS.items():
            if mode == "group_by" and tn not in ("HexagonTiling", "SquareTiling", "Isohedral scalloped_hexagon"):
                continue
            cart = smb.create_symbol_cartogram(
                gdf, layout=smb.MosaicLayout(tiling=tf(), spacing=0.0, morph=False), show_progress=False, **kw
            )
            sym = cart.to_geodataframe()
            counts[(state, mode, tn)] = overlaps(sym)
            geoms[(state, mode, tn)] = np.asarray(sym.geometry)
            fig, ax = plt.subplots(figsize=(7, 5))
            cart.plot(ax=ax, legend=False, edgecolor="black", linewidth=0.3)
            ax.set_axis_off()
            ax.set_title(f"{state}: {tn}, {mode} ({counts[(state, mode, tn)]} overlapping pairs)", fontsize=9)
            fig.savefig(f"{OUT}/_{state}_{mode}_{tn.replace(' ', '_').replace('.', '_')}.png", dpi=110)
            plt.close(fig)

# hexagon identity
for mode in MODES:
    b, a = geoms[("before", mode, "HexagonTiling")], geoms[("after", mode, "HexagonTiling")]
    d = max(np.abs(shapely.get_coordinates(x) - shapely.get_coordinates(y)).max() for x, y in zip(b, a))
    print("hex max coord diff", mode, d)

for k, v in counts.items():
    print(k, v)

# side-by-side
from PIL import Image

for mode in MODES:
    for tn in TILINGS:
        if ("before", mode, tn) not in counts:
            continue
        s = tn.replace(" ", "_").replace(".", "_")
        ims = [Image.open(f"{OUT}/_{st}_{mode}_{s}.png") for st in ("before", "after")]
        w = Image.new("RGB", (ims[0].width * 2, ims[0].height), "white")
        w.paste(ims[0], (0, 0))
        w.paste(ims[1], (ims[0].width, 0))
        w.save(f"{OUT}/{mode}_{s}.png")
import glob
import os

for f in glob.glob(f"{OUT}/_*.png"):
    os.remove(f)
