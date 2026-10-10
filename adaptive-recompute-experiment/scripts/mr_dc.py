import warnings, numpy as np, shapely
import carto_flow.data as ex
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.workflow import CartogramWorkflow
warnings.filterwarnings("ignore")
g = ex.load_us_census(population=True).reset_index(drop=True)
dc = g.loc[g["State Abbreviation"] == "DC", "geometry"].iloc[0]
o = MorphOptions(show_progress=False, stall_patience=None, n_iter=10, recompute_every=10)
r = morph_gdf(g, "Population", options=o.copy_with(grid_size=128))
wf = CartogramWorkflow(g, "Population", None, None, o)
wf.morph_multiresolution(min_resolution=128, levels=2, options=o)
for label, grid in (("single 128x88", r.grid), ("multires 128x89", wf.results[1].grid), ("multires 256x178", wf.results[2].grid), ("single 256", morph_gdf(g, "Population", options=o.copy_with(grid_size=256)).grid)):
    X, Y = np.meshgrid(grid.x_coords, grid.y_coords) if np.ndim(grid.x_coords) == 1 else (grid.X, grid.Y)
    inside = int(shapely.contains_xy(dc, X.ravel(), Y.ravel()).sum())
    print(f"{label:18s} cell centres inside DC: {inside}   (DC area / cell area = {dc.area / (grid.dx * grid.dy):.2f})")
