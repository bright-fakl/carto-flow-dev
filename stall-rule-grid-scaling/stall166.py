import warnings,time,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely
from carto_flow.data import load_us_census
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
st=load_us_census(); di=load_us_census(level="congressional_district"); co=load_us_census(level="county",race=True)
az=co[co["State Abbreviation"]=="AZ"]; tx=co[co["State Abbreviation"]=="TX"]
rng=np.random.default_rng(0)
cases={"AZ counties":(az,"Population"),"TX counties":(tx,"Population"),"states pop":(st,"Population"),"districts pop":(di,"Population"),
       "counties pop":(co,"Population"),"counties asian":(co,"Asian")}
def run(name,grid,rule,mult=None):
    g,col=cases[name]; v=g[col].to_numpy(float)
    if col=="Asian": v=np.maximum(v,1.0)
    mi=0.02 if rule=="default" else 0.02*min(1.0,256/grid)
    o=MorphOptions(grid=grid,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=3000,show_progress=False,stall_min_improvement=mi,stall_patience=None if rule=="off" else 4)
    t=time.time(); c=morph_geometries(list(g.geometry),v,options=o)
    a=shapely.area(np.array(c.get_geometry(),dtype=object)); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
    print(f"{name:14s} grid {grid:5d} {rule:8s} {str(c.status).split('.')[-1]:9s} it {c.niterations:5d} {time.time()-t:6.1f}s mean {e.mean():7.2f} max {e.max():8.1f}",flush=True)
if __name__=="__main__":
    for name,grids in [("AZ counties",[256,512,1024]),("TX counties",[512,1024]),("states pop",[256,512,1024,2048]),("districts pop",[256,512,1024,2048]),("counties pop",[1024,2048])]:
        for grid in grids:
            for rule in ("default","scaled","off"):
                run(name,grid,rule)
