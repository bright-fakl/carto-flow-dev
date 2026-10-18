import warnings,time; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g0=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
for seg in (2000,500):
    g=g0 if seg is None else densify_coverage(g0,max_segment_length=seg)
    v=g["pop"].to_numpy(float); gdf=g[["geometry"]].copy(); gdf["v"]=v
    for r0,L in ((128,5),(256,4),(512,3)):
        t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution=r0,levels=L,options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
        c=w.last; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
        print(f"seg {str(seg):5s} ladder {r0}x{L} {c.status.name:9s} {time.time()-t:5.1f}s mean {e.mean():7.2f} med {np.median(e):6.2f} invalid {int((~shapely.is_valid(o)).sum())}",flush=True)
