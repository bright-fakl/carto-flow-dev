"""Finest county level continued past its stall with validity="repair-crossings": per-region errors every 20 iterations."""
import warnings, sys, json, time; warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
out = sys.argv[1]
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v)
opt = dict(area_scale=1e-6, show_progress=False, validity="repair-crossings")
w = CartogramWorkflow(gdf, "v", validate=False)
w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(n_iter=1000, **opt))
shrink = None
a0 = shapely.area(np.array(g.geometry, dtype=object)); T0 = v / v.sum() * a0.sum(); shrink = T0 / a0
t = time.time()
c2 = w.morph(options=MorphOptions(grid=2048, n_iter=1000, stall_patience=None, snapshot_every=20, **opt))
rows = []
for sn in c2.snapshots.snapshots:
    o = np.array(sn.geometry, dtype=object); valid = shapely.is_valid(o); a = shapely.area(o)
    T = v / v[valid].sum() * a[valid].sum(); e = abs(a - T) / T * 100
    rows.append(dict(it=sn.iteration, errors=e.tolist(), invalid=int((~valid).sum())))
json.dump(dict(time=time.time() - t, shrink=shrink.tolist(), rows=rows), open(f"{out}/continue_valid.json", "w"))
print("done", time.time() - t, len(rows))
