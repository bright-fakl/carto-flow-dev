import warnings,time,sys,json; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
from carto_flow.flow_cartogram import algorithm as alg
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
cty=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
sets={"states":(data.load_us_census().reset_index(drop=True),"Population"),"districts":(data.load_us_census(level="congressional_district").reset_index(drop=True),"Population"),"counties":(cty,"pop")}
rules={"none":lambda mi,res:mi,"one-way":lambda mi,res:mi*min(1.0,256/res),"symmetric":lambda mi,res:mi*256/res}
cases=[("states",64,3),("states",32,5),("districts",128,3),("districts",64,4),("districts",32,5),("counties",512,3),("counties",256,4),("counties",128,5),("counties",64,6)]
for rname,fn in rules.items():
    alg.scaled_min_improvement=fn
    for name,r0,L in cases:
        g,col=sets[name]; v=g[col].to_numpy(float); gdf=g[["geometry"]].copy(); gdf["v"]=v
        t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution=r0,levels=L,options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
        c=w.last; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
        tot=sum(r.niterations for r in w)
        print(f"{rname:10s} {name:9s} {r0:3d}x{L} {str(c.status).split('.')[-1]:9s} levels {len(w)-1} total it {tot:5d} {time.time()-t:5.1f}s mean {e.mean():7.2f} med {np.median(e):6.2f} max {e.max():7.0f} inv {int((~shapely.is_valid(o)).sum())}",flush=True)
