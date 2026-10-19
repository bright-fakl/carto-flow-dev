import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness, vw
import carto_flow.flow_cartogram.algorithm as alg
hook = vw.VW(check_every=10); alg.VW_HOOK = hook
gdf, v = harness.load("county")
w, m = harness.run("county", 1000, "bf")
print("levels", len(w), "events", len(hook.events), "marks", hook.level_marks)
gt, c0, offs0 = shapely.to_ragged_array(np.array(gdf.geometry.values, dtype=object))
fin = shapely.get_coordinates(np.array(w[-1].get_geometry(), dtype=object))
lifted = vw.backfill(c0, hook.events)
print("input verts", len(c0), "lifted", len(lifted), "final", len(fin))
# lifted input polygon: same point set (areas equal per ring)
ring_offs = np.asarray(offs0[0])
print("input area total", shapely.area(gdf.geometry.values).sum())
# new vertices in the lifted input lie on the input segments: collinearity check via polygon area identical
import shapely.geometry as sg
# build lifted geometries using the final structure (ring offsets of final)
_, cf, of = shapely.to_ragged_array(np.array(w[-1].get_geometry(), dtype=object))
g2 = shapely.from_ragged_array(shapely.GeometryType.POLYGON if len(of)==2 else shapely.GeometryType.POLYGON, lifted, of) if False else None
# per-level frames: level snapshots
for k, c in enumerate(w):
    if c.grid is None: continue
    n = len(shapely.get_coordinates(np.array(c.get_geometry(), dtype=object)))
    print("level", k, "verts", n)
