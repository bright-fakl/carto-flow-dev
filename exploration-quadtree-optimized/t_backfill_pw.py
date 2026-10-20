import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness, pwo
import carto_flow.flow_cartogram.algorithm as alg
h = pwo.PWO(2.0 ** -6, prune_tol=0.02, prune_every=1, rebuild_every=4, min_ratio=0.6)
alg.PW_HOOK = h
gdf, v = harness.load("county")
w, m = harness.run("county", 1000, "pwo_bf")
gt, c0, offs0 = shapely.to_ragged_array(np.array(gdf.geometry.values, dtype=object))
fin = shapely.get_coordinates(np.array(w[-1].get_geometry(), dtype=object))
lifted = pwo.backfill(c0, h.events)
print("input verts", len(c0), "lifted", len(lifted), "final", len(fin), "events", len(h.events))
# the input vertices are still vertices of the final structure: orig flags
print("orig flags at the end:", int(h.orig.sum()), "(input vertices 768,580)")
# lifted input has the same point set per ring (only collinear inserted points): areas equal
_, cf, of = shapely.to_ragged_array(np.array(w[-1].get_geometry(), dtype=object))
a0 = shapely.area(gdf.geometry.values).sum()
# polygon area of lifted input using final ring offsets
def ring_area(c, offs):
    s = 0.0
    for r in range(len(offs) - 1):
        x = c[offs[r]:offs[r + 1], 0]; y = c[offs[r]:offs[r + 1], 1]
        s += 0.5 * np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])
    return s
print("signed ring-area sum input %.6e, lifted %.6e" % (ring_area(c0, np.asarray(offs0[0])), ring_area(lifted, np.asarray(of[0]))))
