import warnings,time; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g0=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
for seg in (None,2000,1000,500):
    g=g0 if seg is None else densify_coverage(g0,max_segment_length=seg)
    v=g["pop"].to_numpy(float); n=sum(shapely.get_num_coordinates(x) for x in g.geometry)
    t=time.time(); c=morph_geometries(list(g.geometry),v,options=MorphOptions(grid=128,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=300,show_progress=False,stall_patience=None,snapshot_every=100))
    o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
    print(f"max segment {str(seg):5s} vertices {n:8d} {time.time()-t:5.1f}s mean {e.mean():7.1f} med {np.median(e):6.1f} invalid {int((~shapely.is_valid(o)).sum())}",flush=True)
