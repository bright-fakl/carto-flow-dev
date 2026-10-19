import warnings,time,sys,os; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,".")
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import carto_flow.flow_cartogram.algorithm as alg
import inv
mode=sys.argv[1]; nit=int(sys.argv[2]) if len(sys.argv)>2 else 1000
if mode!="base":
    alg.INV_HOOK=inv.InvHook(repair=mode in("repair","both","pointset"),exclude=mode in("exclude","both"),pointset=mode=="pointset")
g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v); A0=shapely.area(g.geometry.values)
t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False)
w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=nit,show_progress=False))
dt=time.time()-t
c=w[-1]; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); val=shapely.is_valid(o)
T=v/v[val].sum()*a[val].sum(); e=abs(a-T)/T*100
tr=shapely.STRtree(o); nb=np.zeros(len(o),bool)
for i in np.flatnonzero(~val):
    for j in tr.query(o[i],predicate="intersects"):
        if j!=i: nb[j]=True
nb&=val
lv=" ".join(f"{x.niterations}{x.status.name[0]}" for x in w if x.grid is not None)
print(f"{mode:8s} nit {nit}: {dt:5.1f}s levels {lv} | invalid {int((~val).sum()):3d}  valid: mean {e[val].mean():.3f}% median {np.median(e[val]):.3f}% p95 {np.percentile(e[val],95):.2f}% >10%: {int((e[val]>10).sum())} >5%: {int((e[val]>5).sum())} | neighbors of invalid (n={int(nb.sum())}) median {np.median(e[nb]):.3f}% >5%: {int((e[nb]>5).sum())}",flush=True)
