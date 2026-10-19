import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, xing
o = shapely.from_wkb(np.load(os.path.dirname(os.path.abspath(__file__)) + f"/out/{sys.argv[1]}_wkb.npy", allow_pickle=True))
inv = np.flatnonzero(~shapely.is_valid(o))
for i in inv:
    g = o[i]
    gt, c, offs = shapely.to_ragged_array(np.array([g], dtype=object))
    ro = np.asarray(offs[0], dtype=np.int64)
    G = xing.Grid(c, ro, 6.0); f = G.crossing()
    pt = shapely.get_coordinates(shapely.from_wkt(shapely.is_valid_reason(g).split("[")[1].rstrip("]").replace(" ", " ").join(["POINT(", ")"]))) if False else None
    L = np.hypot(*(c[G.first+1]-c[G.first]).T)
    print(i, shapely.is_valid_reason(g)[:60], "area", shapely.area(g), "nverts", len(c), "detector flagged", f.sum(), "min seg", L.min(), "n seg < 1m", (L<1).sum(), "n<0.01", (L<0.01).sum())
