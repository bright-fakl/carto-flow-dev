import warnings,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely, pickle, carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
A0=shapely.area(g.geometry.values)
c2=w.morph(options=MorphOptions(area_scale=1e-6,grid=2048,n_iter=1500,stall_patience=None,snapshot_every=50,show_progress=False))
snaps={}
for sn in c2.snapshots.snapshots:
    o=np.array(sn.geometry,dtype=object)
    snaps[sn.iteration]=dict(area=shapely.area(o),valid=shapely.is_valid(o),nverts=shapely.get_num_coordinates(o))
pickle.dump(dict(v=v,A0=A0,snaps=snaps,names=g["NAME"].to_numpy() if "NAME" in g else None,state=g["State Abbreviation"].to_numpy()),open("cont2.pkl","wb"))
print("saved",len(snaps))
