import warnings,time,sys,os; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
cty=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
st=data.load_us_census().reset_index(drop=True); di=data.load_us_census(level="congressional_district").reset_index(drop=True)
cases={"AZ":(cty[cty["State Abbreviation"]=="AZ"].reset_index(drop=True),"pop",None),"TX":(cty[cty["State Abbreviation"]=="TX"].reset_index(drop=True),"pop",None),"states":(st,"Population",None),"districts":(di,"Population",None),
       "counties":(cty,"pop",None),"districts lognormal1":(di,"Population",1.0),"districts lognormal2":(di,"Population",2.0),"states lognormal2":(st,"Population",2.0)}
for name,grids in (("AZ",[256,512,1024]),("TX",[512,1024]),("states",[64,256,1024,2048]),("districts",[64,256,1024]),("counties",[1024,2048]),("districts lognormal1",[256,512]),("districts lognormal2",[256,512]),("states lognormal2",[256])):
    g,col,sig=cases[name]; v=g[col].to_numpy(float)
    if sig: v=np.exp(np.random.default_rng(0).normal(0,sig,len(v)))
    for grid in grids:
        t=time.time(); c=morph_geometries(list(g.geometry),v,options=MorphOptions(grid=grid,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=3000,show_progress=False))
        o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
        print(f"ETA={os.environ.get('ETA','0'):5s} {name:21s} grid {grid:5d} {c.status.name:9s} it {c.niterations:5d} {time.time()-t:5.1f}s mean {e.mean():8.2f} max {e.max():8.0f}",flush=True)
