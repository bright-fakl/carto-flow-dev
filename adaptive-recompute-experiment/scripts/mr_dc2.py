import warnings, numpy as np
import carto_flow.data as ex
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
warnings.filterwarnings("ignore")
g = ex.load_us_census(population=True).reset_index(drop=True)
i = int(np.where(g["State Abbreviation"] == "DC")[0][0])
o = MorphOptions(show_progress=False, stall_patience=None, n_iter=300, snapshot_every=1)
r = morph_gdf(g, "Population", options=o.copy_with(grid_size=128))
cell = r.grid.dx * r.grid.dy
print("single grid 128: DC area in cells at iteration", end=" ")
for k in (0, 10, 20, 30, 40, 50, 63):
    k = min(k, len(r.snapshots) - 1)
    print(f"{r.snapshots[k].iteration}:{r.snapshots[k].geometry.iloc[i].area / cell:.2f}" if hasattr(r.snapshots[k].geometry, "iloc") else f"{r.snapshots[k].iteration}:{list(r.snapshots[k].geometry)[i].area / cell:.2f}", end="  ")
print()
