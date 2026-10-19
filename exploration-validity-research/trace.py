"""Error of the valid polygons at snapshots during a fixed-schedule ladder. usage: trace.py <method> <dt>  (method base|vw1|vw10)"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness, vwd as vw
import carto_flow.flow_cartogram.algorithm as alg
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
m, dt = sys.argv[1], float(sys.argv[2]); sched = [int(x) for x in os.environ.get("SCHED", "600,150,400").split(",")]
if m.startswith("vw"): alg.VW_HOOK = vw.VW(check_every=int(m[2:]))
gdf, v = harness.load("county")
w = CartogramWorkflow(gdf, "v", validate=False)
w.morph_multiresolution(min_resolution="auto", levels="auto", options=[MorphOptions(area_scale=1e-6, n_iter=k, show_progress=False, stall_patience=None, dt=dt, snapshot_every=25) for k in sched])
for li, c in enumerate(w):
    if c.grid is None: continue
    for s in c.snapshots.snapshots:
        o = np.array(s.geometry, dtype=object); val = shapely.is_valid(o); a = shapely.area(o)
        T = v / v[val].sum() * a[val].sum(); e = (np.abs(a - T) / T * 100)[val]
        print(f"{m} dt{dt} L{li} it {s.iteration:4d} inv {int((~val).sum()):3d} mean {e.mean():7.3f} med {np.median(e):8.4f} p95 {np.percentile(e,95):7.3f} >10% {int((e>10).sum()):4d}", flush=True)
