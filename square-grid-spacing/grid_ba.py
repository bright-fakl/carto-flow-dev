import warnings,time,sys,json; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow, carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
print(carto_flow.__file__,file=sys.stderr)
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
cty=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
sets={"states":(data.load_us_census().reset_index(drop=True),"Population"),"districts":(data.load_us_census(level="congressional_district").reset_index(drop=True),"Population"),"counties":(cty,"pop")}
cases=[("states",64,3),("districts",128,3),("districts",64,4),("counties",512,3),("counties",256,4),("counties",128,5)]
out=[]
for name,r0,L in cases:
    g,col=sets[name]; v=g[col].to_numpy(float); gdf=g[["geometry"]].copy(); gdf["v"]=v
    t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution=r0,levels=L,options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
    c=w.last; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
    out.append(dict(case=f"{name} ladder {r0}x{L}",status=str(c.status).split('.')[-1],it=int(c.niterations),sec=round(time.time()-t,1),mean=round(float(e.mean()),2),med=round(float(np.median(e)),2),max=round(float(e.max()),1),inv=int((~shapely.is_valid(o)).sum())))
    print(out[-1],flush=True)
json.dump(out,open(sys.argv[1],"w"))
