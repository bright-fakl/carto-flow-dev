import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet")
idx=np.flatnonzero(g.STATEFP.to_numpy()=="04"); geo=list(g.geometry.values[idx]); v=g["pop"].to_numpy(float)[idx]
def terr(geoms):
    a=shapely.area(np.array(geoms,dtype=object)); t=v/v.sum()*a.sum(); return abs(a-t)/t*100
e0=terr(geo); print("start mean %.1f max %.1f"%(e0.mean(),e0.max()))


for grid in [256,512]:
    c=morph_geometries(geo,v,options=MorphOptions(grid=grid,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=120,show_progress=False,stall_patience=None,snapshot_every=1))
    its=list(c.snapshots.get_iterations())
    out=[]
    for it in its:
        if it in (0,1,2,5,10,20,30,50,80,119):
            e=c.snapshots.get_snapshot(it).errors
            out.append((it, round(e.mean_error_pct,1), round(e.max_error_pct,1)))
    print("grid",grid,out,flush=True)
