import numpy as np, shapely
from shapely.geometry import MultiPolygon

def _polys(g, fallback):
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    parts = []
    for p in shapely.get_parts(g):
        if p.geom_type == "Polygon": parts.append(p)
        elif p.geom_type == "MultiPolygon": parts.extend(p.geoms)
    return MultiPolygon(parts) if parts else fallback

class InvHook:
    def __init__(self, repair=True, exclude=True, pointset=False):
        self.do_repair = repair; self.do_exclude = exclude; self.pointset = pointset; self.mv_area = None
        self.mask = None; self.log = []
    def repair(self, geoms):
        arr = np.empty(len(geoms), dtype=object); arr[:] = geoms
        self.mask = ~shapely.is_valid(arr)
        self.log.append(int(self.mask.sum()))
        if self.do_repair and self.mask.any():
            idx = np.flatnonzero(self.mask)
            mv = shapely.make_valid(arr[idx])
            self.mv_area = np.zeros(len(arr)); 
            for i, g in zip(idx, mv):
                arr[i] = _polys(g, arr[i]); self.mv_area[i] = shapely.area(arr[i])
        return list(arr)
    def areas(self, a, T):
        if self.pointset and self.mask is not None and self.mask.any() and self.mv_area is not None and len(self.mask) == len(a):
            a = a.copy(); a[self.mask] = self.mv_area[self.mask]; return a
        if self.do_exclude and self.mask is not None and self.mask.any() and len(self.mask) == len(a):
            a = a.copy(); a[self.mask] = T[self.mask]
        return a
