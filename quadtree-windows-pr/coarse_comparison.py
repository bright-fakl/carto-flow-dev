"""Raw coarse counties (43 k vertices): validity none, windows and quadtree; invalid polygons in black."""
import warnings, sys; warnings.filterwarnings("ignore")
import numpy as np, shapely, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
from carto_flow.geo_utils import simplify_coverage
out = sys.argv[1]
g = simplify_coverage(data.load_us_census(level="county").reset_index(drop=True), tolerance=4000.0)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v)
res = {}
for mode in ("none", "windows", "quadtree"):
    w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False, validity=mode))
    o = np.array(w[-1].get_geometry(), dtype=object); res[mode] = (o, shapely.is_valid(o))
INK = "#1f2933"
fig, axs = plt.subplots(1, 3, figsize=(17, 4.6))
for ax, mode in zip(axs, ("none", "windows", "quadtree")):
    o, val = res[mode]; ax.axis("off"); gs = gpd.GeoSeries(list(o), crs=g.crs)
    gs[val].plot(ax=ax, color="#d5dae0", edgecolor="white", linewidth=0.1)
    gs[~val].plot(ax=ax, color=INK, edgecolor=INK, linewidth=0.4)
    ax.set_title(f'validity="{mode}": {int((~val).sum())} invalid polygons (black)', loc="left", fontsize=10, color=INK)
fig.tight_layout(); fig.savefig(f"{out}/fig1_raw_coarse.png", dpi=150)
print({m: int((~res[m][1]).sum()) for m in res})
