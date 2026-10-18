import warnings,time; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
sets={"states":(data.load_us_census().reset_index(drop=True),"Population",[(64,3),(32,5)]),"districts":(data.load_us_census(level="congressional_district").reset_index(drop=True),"Population",[(128,3),(64,4),(32,5)])}
for name,(g0,col,lads) in sets.items():
    for seg in (None,2000,1000,500):
        g=g0 if seg is None else densify_coverage(g0,max_segment_length=seg)
        v=g[col].to_numpy(float); gdf=g[["geometry"]].copy(); gdf["v"]=v
        for r0,L in lads:
            t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution=r0,levels=L,options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
            c=w.last; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
            print(f"{name:9s} seg {str(seg):5s} ladder {r0}x{L} {c.status.name:9s} {time.time()-t:5.1f}s mean {e.mean():6.2f} med {np.median(e):5.2f} invalid {int((~shapely.is_valid(o)).sum())}",flush=True)
