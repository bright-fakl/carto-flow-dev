import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet")
idx=np.flatnonzero(g.STATEFP.to_numpy()=="04"); geo=list(g.geometry.values[idx]); v=g["pop"].to_numpy(float)[idx]
def run(tag,**kw):
    base=dict(grid=512,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=300,show_progress=False); base.update(kw)
    c=morph_geometries(geo,v,options=MorphOptions(**base))
    a=shapely.area(np.array(c.get_geometry(),dtype=object)); t=v/v.sum()*a.sum(); e=abs(a-t)/t*100
    print(f"{tag:32s} {str(c.status).split('.')[-1]:10s} it {c.niterations:4d} mean {e.mean():8.1f} max {e.max():8.1f}",flush=True)
run("default")
run("adaptive_dt off",adaptive_dt=False)
run("dt 0.05",dt=0.05)
run("dt 0.05 adaptive off",dt=0.05,adaptive_dt=False)
run("recompute_every 1",recompute_every=1)
run("margin default",grid_margin=None,grid_square=None)
run("no stall rule",stall_patience=None)
run("density_rasterization center",density_rasterization="center")
