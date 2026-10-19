import warnings,sys,pickle; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,".")
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import carto_flow.flow_cartogram.algorithm as alg
import inv
g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v); A0=shapely.area(g.geometry.values)
res={}
for mode in ("base","repair"):
    alg.INV_HOOK=inv.InvHook(repair=True,exclude=False) if mode=="repair" else None
    w=CartogramWorkflow(gdf,"v",validate=False)
    w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
    c=w[-1]; o=np.array(c.get_geometry(),dtype=object); inv_ladder=~shapely.is_valid(o)
    a=shapely.area(o); val=~inv_ladder; T=v/v[val].sum()*a[val].sum()
    c2=w.morph(options=MorphOptions(area_scale=1e-6,grid=2048,n_iter=1500,stall_patience=None,snapshot_every=50,show_progress=False))
    tl=[]
    for sn in c2.snapshots.snapshots:
        oo=np.array(sn.geometry,dtype=object); tl.append((sn.iteration,~shapely.is_valid(oo)))
    res[mode]=dict(ladder=inv_ladder,timeline=tl,T=T,area=a)
pickle.dump(dict(res=res,A0=A0,v=v,state=g["State Abbreviation"].to_numpy(),name=g["County Name"].to_numpy() if "County Name" in g else None,cols=list(g.columns)),open("invsets.pkl","wb"))
print("done")
