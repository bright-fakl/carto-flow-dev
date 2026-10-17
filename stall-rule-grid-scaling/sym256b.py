import warnings,time; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
from carto_flow.flow_cartogram import algorithm as alg
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
cty=gpd.read_parquet(f"{S}/cty/acs_county.parquet"); az=cty[cty["State Abbreviation"]=="AZ"]
st=data.load_us_census().reset_index(drop=True); di=data.load_us_census(level="congressional_district").reset_index(drop=True)
sets={"states":(st,"Population"),"districts":(di,"Population"),"AZ counties":(az,"pop")}
rules={"one-way":lambda mi,res:mi*min(1.0,256/res),"symmetric":lambda mi,res:mi*256/res}
for rname,fn in rules.items():
    alg.scaled_min_improvement=fn
    for name,grids in (("states",[32,64,128]),("districts",[64,96,128]),("AZ counties",[32,64,128])):
        g,col=sets[name]; v=g[col].to_numpy(float)
        for G in grids:
            c=morph_geometries(list(g.geometry),v,options=MorphOptions(grid=G,area_scale=1e-6,show_progress=False,n_iter=1000))
            o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); t=v/v.sum()*a.sum(); e=abs(a-t)/t*100
            print(f"{rname:10s} {name:12s} grid {G:3d} {c.status.name:9s} it {c.niterations:4d} mean {e.mean():6.2f} max {e.max():6.1f}",flush=True)
