import warnings, numpy as np
import carto_flow.data as ex
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.workflow import CartogramWorkflow
warnings.filterwarnings("ignore")
g = ex.load_us_census(population=True).reset_index(drop=True)
o = MorphOptions(show_progress=False, stall_patience=None, n_iter=300)
r = morph_gdf(g, "Population", options=o.copy_with(grid_size=128))
wf = CartogramWorkflow(g, "Population", None, None, o)
wf.morph_multiresolution(min_resolution=128, levels=2, options=o)
a, b = r.grid, wf.results[1].grid
for name in ("sx", "sy", "xmin", "xmax", "ymin", "ymax", "dx", "dy"):
    print(f"{name:5s} single={getattr(a, name, None)!s:24s} multires={getattr(b, name, None)!s:24s}")
print([n for n in dir(a) if not n.startswith("_")][:30])
