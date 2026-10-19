import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
for name in ("baseline_county", "bf_county"):
    o = shapely.from_wkb(np.load(d + name + "_wkb.npy", allow_pickle=True))
    valid = shapely.is_valid(o)
    print(name, "invalid", (~valid).sum())
    try:
        ov = shapely.coverage_invalid_edges(o[valid])
        n = (~shapely.is_empty(ov)).sum()
        print("  polygons (valid ones) with invalid coverage edges (overlaps / gaps at shared edges):", n)
    except Exception as e:
        print("  coverage check failed", e)
    # pairwise overlaps by area among valid polygons via STRtree
    tree = shapely.STRtree(o[valid]); vi = np.flatnonzero(valid)
    a, b = tree.query(o[valid], predicate="intersects")
    m = a < b
    ov = shapely.area(shapely.intersection(o[valid][a[m]], o[valid][b[m]]))
    print("  neighbor pairs with overlap area > 1 m2:", int((ov > 1).sum()), "total overlap km2", ov.sum() / 1e6)
