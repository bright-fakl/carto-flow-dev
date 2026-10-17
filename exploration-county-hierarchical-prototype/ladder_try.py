import warnings,time,sys; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.api import multiresolution_morph
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet"); pop=g["pop"].to_numpy(float)
gdf=g[["pop","geometry"]].copy()
def run(tag,r0,L,**kw):
    base=dict(area_scale=1e-6,n_iter=1000,show_progress=False); base.update(kw)
    t=time.time(); c=multiresolution_morph(gdf,"pop",min_resolution=r0,levels=L,options=MorphOptions(**base))
    o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=pop/pop.sum()*a.sum(); e=abs(a-tt)/tt*100
    print(f"{tag:44s} {str(c.status).split('.')[-1]:9s} it {c.niterations:5d} {time.time()-t:5.0f}s mean {e.mean():7.2f} med {np.median(e):6.2f} p95 {np.percentile(e,95):6.1f} max {e.max():6.0f} inv {int((~shapely.is_valid(o)).sum())}",flush=True)
    return c
run("ladder 128x4 default",128,4)
run("ladder 128x4 min_impr 0.002",128,4,stall_min_improvement=0.002)
run("ladder 128x4 stall off, 500/level",128,4,stall_patience=None,n_iter=500)
run("ladder 128x5 (to 2048) min_impr 0.002",128,5,stall_min_improvement=0.002)
run("ladder 256x4 (to 2048) min_impr 0.002",256,4,stall_min_improvement=0.002)
run("ladder 64x6 (to 2048) min_impr 0.002",64,6,stall_min_improvement=0.002)
