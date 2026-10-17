import warnings,time; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet"); pop=g["pop"].to_numpy(float); geo=list(g.geometry.values)
for tag,kw in [("default",{}),("min_improvement 0.002",dict(stall_min_improvement=0.002)),("min_improvement 0.0005, patience 6",dict(stall_min_improvement=0.0005,stall_patience=6))]:
    t=time.time(); c=morph_geometries(geo,pop,options=MorphOptions(grid=1024,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=3000,show_progress=False,**kw))
    o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=pop/pop.sum()*a.sum(); e=abs(a-tt)/tt*100
    print(f"{tag:36s} {str(c.status).split('.')[-1]:9s} it {c.niterations:5d} {time.time()-t:5.0f}s mean {e.mean():7.2f} median {np.median(e):6.2f} max {e.max():7.0f}",flush=True)
