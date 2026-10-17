import warnings,sys,json; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/acs_county.parquet"); v=g["pop"].to_numpy(float)
c=morph_geometries(list(g.geometry),v,options=MorphOptions(grid=128,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=200,show_progress=False,stall_patience=None,snapshot_every=5))
inv={}
for it in c.snapshots.get_iterations(): inv[int(it)]=int((~shapely.is_valid(np.array(c.snapshots.get_snapshot(it).geometry,dtype=object))).sum())
json.dump(inv,open(sys.argv[1]+".json","w"))
gpd.GeoDataFrame({"NAME":g.NAME},geometry=list(c.snapshots.get_snapshot(11).geometry),crs=g.crs).to_parquet(sys.argv[1]+"_it10.parquet")
