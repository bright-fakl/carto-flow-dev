import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet")
idx=np.flatnonzero(g.STATEFP.to_numpy()=="04"); geo=list(g.geometry.values[idx]); v=g["pop"].to_numpy(float)[idx]
for grid in [128,256,512,1024]:
    c=morph_geometries(geo,v,options=MorphOptions(grid=grid,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=2000,show_progress=False,stall_patience=None))
    print(grid,str(c.status).split('.')[-1],c.niterations,round(c.duration,1),"s",flush=True)
