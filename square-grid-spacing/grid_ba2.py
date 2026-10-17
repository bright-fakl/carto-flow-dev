import warnings,time,sys,json; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
cty=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
sets={"states":(data.load_us_census().reset_index(drop=True),"Population"),"districts":(data.load_us_census(level="congressional_district").reset_index(drop=True),"Population"),"counties":(cty,"pop")}
out=[]
for name,grids in [("states",[64,128,256,512]),("districts",[128,256,512,1024]),("counties",[256,512,1024])]:
    g,col=sets[name]; v=g[col].to_numpy(float)
    for G in grids:
        t=time.time(); c=morph_geometries(list(g.geometry),v,options=MorphOptions(grid=G,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=1500,show_progress=False,stall_patience=None))
        o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
        out.append(dict(set=name,grid=G,status=str(c.status).split('.')[-1],it=int(c.niterations),sec=round(time.time()-t,1),mean=round(float(e.mean()),2),med=round(float(np.median(e)),2),max=round(float(e.max()),1),inv=int((~shapely.is_valid(o)).sum())))
        print(out[-1],flush=True)
json.dump(out,open(sys.argv[1],"w"))
