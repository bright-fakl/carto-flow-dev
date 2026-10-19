import warnings; warnings.filterwarnings("ignore")
import numpy as np, shapely, pickle, carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v); A0=shapely.area(g.geometry.values)
w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
c2=w.morph(options=MorphOptions(area_scale=1e-6,grid=2048,n_iter=1500,stall_patience=None,snapshot_every=1500,show_progress=False))
res={}
for sn in c2.snapshots.snapshots:
    if sn.iteration in (1,1500):
        o=np.array(sn.geometry,dtype=object); res[sn.iteration]=o
pickle.dump(dict(geoms={k:shapely.to_wkb(x) for k,x in res.items()},v=v,A0=A0,state=g["State Abbreviation"].to_numpy()),open("nbr.pkl","wb"))
print(list(res))
