import warnings,sys,re; warnings.filterwarnings("ignore")
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import adapt as A, adapt2 as B
cty=data.load_us_census(level="county").reset_index(drop=True)
outs,cell=B.pilot(cty); g2=B.adaptive_max(cty,outs,cell,0.25); v=g2["Population"].to_numpy(float)
w=CartogramWorkflow(g2[["geometry"]].assign(v=v),"v",validate=False)
base=dict(area_scale=1e-6,show_progress=False)
w.morph_multiresolution(min_resolution="auto",levels="auto",options=[MorphOptions(n_iter=1000,**base),MorphOptions(n_iter=100,snapshot_every=1,**base),MorphOptions(n_iter=1,**base)])
c=w[2]; gr=c.grid; print("level grid",gr.sx,"cell km",gr.dx/1e3)
name="Washington County, Colorado"; k=int(np.flatnonzero(cty["County Name"]==name)[0])
its=list(c.snapshots.get_iterations()); first=None
for it in its:
    o=c.snapshots.get_snapshot(it).geometry[k]
    if not shapely.is_valid(o): first=it; break
print("first invalid iteration",first)
oi=c.snapshots.get_snapshot(first).geometry[k]; op=c.snapshots.get_snapshot(first-1).geometry[k]
m=re.search(r"\[([\d.\-e+]+) ([\d.\-e+]+)\]",shapely.is_valid_reason(oi)); P=np.array([float(m.group(1)),float(m.group(2))])
for pi,pp in zip(shapely.get_parts(oi),shapely.get_parts(op)):
    for ri,rp in zip((pi.exterior,*pi.interiors),(pp.exterior,*pp.interiors)):
        ci=np.asarray(ri.coords); cp=np.asarray(rp.coords)
        A_=ci[:-1]; Bv=ci[1:]; AB=Bv-A_; t=np.clip(np.einsum('ij,ij->i',P-A_,AB)/np.maximum(np.einsum('ij,ij->i',AB,AB),1e-18),0,1)
        d=np.hypot(*(A_+AB*t[:,None]-P).T)
        if d.min()>cell*0.01: continue
        idx=np.argsort(d)[:2]; lo=min(idx); hi=max(idx)+2
        print("crossing segments",idx,"ring size",len(ci))
        for j in range(lo-1,hi+1):
            j%=len(ci)
            print(f" v{j}: prev ({cp[j][0]:.0f},{cp[j][1]:.0f})  now ({ci[j][0]:.0f},{ci[j][1]:.0f})  step ({(ci[j]-cp[j])[0]:.1f},{(ci[j]-cp[j])[1]:.1f}) m = {np.hypot(*(ci[j]-cp[j]))/gr.dx:.3f} cell")
        break
