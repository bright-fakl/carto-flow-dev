import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet")
s1=gpd.read_parquet(f"{S}/h_512_512_1024_s1.parquet")
for st in ["04","08","53"]:
  idx=np.flatnonzero(g.STATEFP.to_numpy()==st)
  for name,geo in [("orig",g.geometry.values[idx]),("stage1",s1.geometry.values[idx])]:
    for grid in [128,256,512,1024]:
      o=MorphOptions(grid=grid,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=300,show_progress=False)
      c=morph_geometries(list(geo),g["pop"].to_numpy(float)[idx],options=o)
      a=shapely.area(np.array(c.get_geometry(),dtype=object)); t=g["pop"].to_numpy(float)[idx]; t=t/t.sum()*a.sum()
      e=abs(a-t)/t*100
      A=shapely.area(np.array(geo,dtype=object)); sm=(t/ (shapely.area(np.array(geo,dtype=object)).sum()) ).min()
      print(st,name,grid,str(c.status).split('.')[-1],c.niterations,f"mean {e.mean():.1f} max {e.max():.1f}",flush=True)
