import hashlib, sys
import numpy as np
sys.path.insert(0, "/home/fakl/carto-flow/visual_checks/mosaic-options-sweep")
import inputs as IN
from carto_flow.flow_cartogram.algorithm import morph_geometries
from carto_flow.flow_cartogram.options import MorphOptions
gdf = IN.load_states()
res = morph_geometries(list(gdf.geometry), values=np.ones(len(gdf)),
                       options=MorphOptions(n_iter=100, show_progress=False))
h = hashlib.sha256()
for g in res.latest.geometry:
    h.update(np.asarray(g.centroid.coords, dtype=np.float64).tobytes())
print("morph hash", h.hexdigest()[:20])
