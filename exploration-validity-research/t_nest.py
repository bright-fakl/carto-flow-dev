import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness
g, v = harness.load("coarse")
o = np.array(g.geometry.values, dtype=object)
print("input invalid:", (~shapely.is_valid(o)).sum(), [ (i, shapely.is_valid_reason(o[i])[:40]) for i in np.flatnonzero(~shapely.is_valid(o))[:5]])
for i in (327, 341, 876, 2727, 53, 2192):
    print(i, o[i].geom_type, "parts", len(shapely.get_parts(o[i])), "holes", sum(len(p.interiors) for p in shapely.get_parts(o[i])), "area km2 %.1f" % (shapely.area(o[i]) / 1e6), "target-share", v[i] / v.sum())
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
b = shapely.from_wkb(np.load(d + "t2_coarse_base_coarse_wkb.npy", allow_pickle=True))
print("baseline coarse: reasons of these:", [(i, shapely.is_valid_reason(b[i])[:25]) for i in (327, 341, 876, 2727, 53, 2192)])
