"""Sweep of QuadtreeSettings.area_ratio for validity="repair-quadtree" (library code, branch feat/quadtree-windows).

usage: sweep.py INPUT DT [REPEAT]    INPUT in county, district, coarse
"""
import json, resource, sys, time, warnings
warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
import carto_flow.flow_cartogram.algorithm as algorithm
from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions
from carto_flow.flow_cartogram.validity_quadtree import QuadtreeSettings, QuadtreeWindows
from carto_flow.geo_utils import simplify_coverage

inp, dt = sys.argv[1], float(sys.argv[2])
repeat = int(sys.argv[3]) if len(sys.argv) > 3 else 1
import os
RATIOS = [float(x) for x in os.environ.get("RATIOS", "0.001,0.003,0.01,0.03,0.1,0.2").split(",")]
if inp == "county":
    g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
elif inp == "district":
    g = data.load_us_census(level="congressional_district", max_segment_length=1000).reset_index(drop=True)
else:
    g = simplify_coverage(data.load_us_census(level="county").reset_index(drop=True), tolerance=4000.0)
v = g["Population"].to_numpy(float); gdf = g[["geometry"]].assign(v=v)
instances = []
for ratio in RATIOS:
    for rep in range(repeat):
        class Q(QuadtreeWindows):
            def __init__(self, n, settings=None, _r=ratio):
                super().__init__(n, QuadtreeSettings(area_ratio=_r))
                self.min_seen = 1.0
                instances.append(self)

            def _min_area_ratio(self):
                value = super()._min_area_ratio()
                self.min_seen = min(self.min_seen, value)
                return value
        algorithm.QuadtreeWindows = Q
        instances.clear()
        t = time.time(); w = CartogramWorkflow(gdf, "v", validate=False)
        w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, dt=dt, show_progress=False, validity="repair-quadtree"))
        el = time.time() - t
        o = np.array(w[-1].get_geometry(), dtype=object); a = shapely.area(o); val = shapely.is_valid(o)
        T = v / v[val].sum() * a[val].sum(); e = (abs(a - T) / T * 100)[val]
        row = dict(input=inp, dt=dt, ratio=ratio, rep=rep, time=round(el, 1), invalid=int((~val).sum()), vertices=int(len(shapely.get_coordinates(o))),
                   mean=round(float(e.mean()), 2), median=round(float(np.median(e)), 3), p95=round(float(np.percentile(e, 95)), 2), above10=int((e > 10).sum()),
                   rebuilds=sum(q.n_rebuilds for q in instances), fixed=sum(q.n_fixed for q in instances), limited=sum(q.n_limited for q in instances),
                   unresolved=sum(q.n_unresolved for q in instances), min_area_ratio_seen=min(q.min_seen for q in instances), levels=[x.niterations for x in w if x.grid is not None], rss=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024))
        print(json.dumps(row), flush=True)
