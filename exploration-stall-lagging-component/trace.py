"""Per-iteration mean ratio, max ratio and lagging error of the county ladder (chosen design, repair-crossings, n_iter 3000).
usage: trace.py <out dir>"""
import warnings, sys, json; warnings.filterwarnings("ignore")
import numpy as np
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
from carto_flow.flow_cartogram import stall
out = sys.argv[1]
log = []  # (monitor id, step, mean_ratio, max_ratio, moved, lag)
original = stall.StallMonitor.update
def update(self, step, mean_ratio, max_ratio, moved, lag=None):
    log.append((id(self), step, mean_ratio, max_ratio, moved, lag))
    return original(self, step, mean_ratio, max_ratio, moved, lag)
stall.StallMonitor.update = update
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
gdf = g[["geometry"]].assign(v=g["Population"].to_numpy(float))
w = CartogramWorkflow(gdf, "v", validate=False)
w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=3000, show_progress=False, validity="repair-crossings", stall_lagging=True))
levels = [dict(grid=c.grid.sx, status=c.status.value, niter=c.niterations, best=c.best_iteration, cycle=None) for c in list(w)[1:]]
ids = list(dict.fromkeys(r[0] for r in log))
runs = [[r[1:] for r in log if r[0] == i] for i in ids]
cycle = None
json.dump(dict(levels=levels, runs=runs, patience=4, min_efficiency=0.05), open(f"{out}/trace.json", "w"))
print(levels, [len(r) for r in runs])
