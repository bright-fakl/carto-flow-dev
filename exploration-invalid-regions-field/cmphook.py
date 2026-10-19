import warnings,time,sys,os,json; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,".")
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import carto_flow.flow_cartogram.algorithm as alg
import inv, pw2
mode=sys.argv[1]; nit=int(sys.argv[2]); inp=sys.argv[3] if len(sys.argv)>3 else "1km"
hook=None
if mode=="repair": alg.INV_HOOK=inv.InvHook(repair=True,exclude=False)
if mode.startswith("hook"):
    hook=pw2.Hook(2.0**-6,insert=True); hook.tol=0; hook.cov=float(mode[4:] or 0.02); alg.PW_HOOK=hook
if inp=="1km":
    g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
else:
    from carto_flow.geo_utils import simplify_coverage
    g=simplify_coverage(data.load_us_census(level="county").reset_index(drop=True),tolerance=4000.0)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
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
print(f"{mode:9s} {inp:6s} nit {nit}: {dt:5.0f}s levels {lv} | vertices {int(shapely.get_num_coordinates(o).sum())} invalid {int((~val).sum()):3d} valid: mean {e[val].mean():.3f}% median {np.median(e[val]):.4f}% p95 {np.percentile(e[val],95):.2f}% >10%: {int((e[val]>10).sum())} >5%: {int((e[val]>5).sum())} | neighbors median {np.median(e[nb]) if nb.any() else 0:.4f}%",flush=True)
