import warnings,sys,json; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/acs_county.parquet"); v=g["pop"].to_numpy(float)
c=morph_geometries(list(g.geometry),v,options=MorphOptions(grid=1024,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=3000,show_progress=False))
gpd.GeoDataFrame({"s":g["STATE"]},geometry=list(c.get_geometry()),crs=g.crs).to_parquet(f"{S}/st_{sys.argv[1]}.parquet"); json.dump([c.status.name,int(c.niterations)],open(f"{S}/st_{sys.argv[1]}.json","w"))
