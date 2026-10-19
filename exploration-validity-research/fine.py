"""Finest-level comparison from a common (valid) level-2 output, stall rule off, fixed iteration counts.

usage: fine.py <config> <n_iter> [stall]   config: base | vw<k> | vwinv<k> | inv ; 'stall' keeps the stall rule on.
"""
import sys, os, time, pickle; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness, vw
import carto_flow.flow_cartogram.algorithm as alg
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
D = os.path.dirname(os.path.abspath(__file__)) + "/out/"
START = os.environ.get("START", "vw1")

def make_start():
    hook = vw.VW(check_every=1); alg.VW_HOOK = hook if START == "vw1" else None
    gdf, v = harness.load("county")
    w = CartogramWorkflow(gdf, "v", validate=False)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False))
    g2 = np.array(w[2].get_geometry(), dtype=object)
    np.save(D + f"start_{START}_wkb.npy", shapely.to_wkb(g2))
    pickle.dump(w[3].grid, open(D + f"start_{START}_grid.pkl", "wb"))
    alg.VW_HOOK = None
    print("start made: invalid at level 2:", int((~shapely.is_valid(g2)).sum()), "verts", len(shapely.get_coordinates(g2)), flush=True)

if not os.path.exists(D + f"start_{START}_wkb.npy"):
    make_start()
g2 = shapely.from_wkb(np.load(D + f"start_{START}_wkb.npy", allow_pickle=True)); grid = pickle.load(open(D + f"start_{START}_grid.pkl", "rb"))
gdf0, v = harness.load("county")
cfg, n = sys.argv[1], int(sys.argv[2]); stall = len(sys.argv) > 3 and sys.argv[3] == "stall"
hook = None
if cfg.startswith("vw"):
    k = int(cfg[2:] or 1); hook = vw.VW(check_every=k); alg.VW_HOOK = hook
gdf = gdf0.copy(); gdf["geometry"] = g2
t = time.time()
w = CartogramWorkflow(gdf, "v", validate=False)
opts = MorphOptions(area_scale=1e-6, n_iter=n, show_progress=False, grid=grid, **({} if stall else {"stall_patience": None}))
c = w.morph(options=opts)
dt = time.time() - t
m = harness.metrics(c.get_geometry(), v)
import resource
oo = np.array(c.get_geometry(), dtype=object); np.savez(D + f"fine_{START}_{cfg}_{n}_{'stall' if stall else 'nostall'}.npz", area=shapely.area(oo), valid=shapely.is_valid(oo), v=v)
print(f"[fine {cfg} n={n} {'stall' if stall else 'nostall'}] {dt:.1f}s its {c.niterations} best {c.best_iteration} inv {m['invalid']} nv {m['nv']} mean {m['mean']:.2f} med {m['med']:.3f} p95 {m['p95']:.2f} >10% {m['gt10']} rss {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024:.0f}MB", flush=True)
