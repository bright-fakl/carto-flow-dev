import warnings,time,sys,copy; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet"); pop=g["pop"].to_numpy(float); gdf=g[["pop","geometry"]].copy()
def stats(c):
    o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); t=pop/pop.sum()*a.sum(); e=abs(a-t)/t*100
    return f"{str(c.status).split('.')[-1][:5]:5s} it {c.niterations:4d} mean {e.mean():7.2f} med {np.median(e):6.2f} max {e.max():6.0f} inv {int((~shapely.is_valid(o)).sum()):4d}"
def run(tag,r0,L,dts=None,**kw):
    base=dict(area_scale=1e-6,n_iter=1000,show_progress=False); base.update(kw)
    opts=[]
    for i in range(L):
        o=MorphOptions(**base)
        if dts: o.dt=dts[i]
        opts.append(o)
    t=time.time(); w=CartogramWorkflow(gdf,"pop",validate=False); w.morph_multiresolution(min_resolution=r0,levels=L,options=opts)
    print(f"== {tag}: {time.time()-t:.0f}s",flush=True)
    for i,c in enumerate(w): print(f"   level {("start" if i==0 else r0*2**(i-1)):>5} {stats(c)}",flush=True)
def H(): run("256x4 min_impr 0.0003, patience 6",256,4,stall_min_improvement=0.0003,stall_patience=6)
for a in sys.argv[1:]:
    if a=="A": run("256x4 default stall",256,4)
    if a=="B": run("256x4 min_impr 0.002",256,4,stall_min_improvement=0.002)
    if a=="C": run("512x3 min_impr 0.002",512,3,stall_min_improvement=0.002)
    if a=="D": run("256x4 stall off n_iter 600",256,4,stall_patience=None,n_iter=600)
    if a=="E": run("256x4 min_impr 0.002, dt x2 per level (~const physical (cap 1))",256,4,dts=[0.2,0.4,0.8,1.0],stall_min_improvement=0.002)
    if a=="H": H()
    if a=="G": run("256x4 min_impr 0.002, dt 0.05..0.4",256,4,dts=[0.05,0.1,0.2,0.4],stall_min_improvement=0.002)
    if a=="F": run("256x4 min_impr 0.002, dt 0.1..0.8 (const physical step)",256,4,dts=[0.1,0.2,0.4,0.8],stall_min_improvement=0.002)
