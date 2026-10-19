import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
o = shapely.from_wkb(np.load(d + sys.argv[1] + "_wkb.npy", allow_pickle=True))
print("invalid", (~shapely.is_valid(o)).sum(), "verts", len(shapely.get_coordinates(o)))
inv = np.flatnonzero(~shapely.is_valid(o))
a0 = shapely.area(o)
for tol in (0.001, 0.01, 0.1, 1.0, 10.0):
    t = time.time()
    try:
        s = shapely.coverage_simplify(o, tol)
    except Exception as e:
        print(tol, "failed", str(e)[:100]); continue
    nv = len(shapely.get_coordinates(s)); a1 = shapely.area(s)
    print(f"tol {tol}: {time.time()-t:.1f}s invalid {(~shapely.is_valid(s)).sum()} verts {nv} removed {len(shapely.get_coordinates(o))-nv} max rel area change {np.max(np.abs(a1-a0)/np.maximum(a0,1)):.2e} invalid-set area change {np.max(np.abs(a1[inv]-a0[inv])/a0[inv]):.2e}")
