import warnings,time,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import carto_flow, carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import carto_flow.flow_cartogram.algorithm as alg
import pw2
bits=float(sys.argv[1]); ins=sys.argv[2]=="ins"; dataset=sys.argv[3] if len(sys.argv)>3 else "county"
print(carto_flow.__file__)
hook=pw2.Hook(2.0**-bits,insert=ins) if bits>0 else None
if hook and len(sys.argv)>4: hook.tol=float(sys.argv[4])
if hook and len(sys.argv)>5: hook.dbg=True
alg.PW_HOOK=hook
g=data.load_us_census(level=dataset,max_segment_length=1000 if dataset!="state" else None).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
c=w[-1]; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
nv=len(shapely.get_coordinates(o))
print(sys.argv[1:],f"{time.time()-t:.1f}s iters {sum(x.niterations for x in w)} mean {e.mean():.2f} med {np.median(e):.3f} max {e.max():.0f} invalid {int((~shapely.is_valid(o)).sum())} vertices {len(shapely.get_coordinates(g.geometry.values))}->{nv}", (f"build {hook.t_build:.1f}s insert {hook.t_insert:.1f}s windows {len(hook.nverts)} pruned {hook.pruned} maxverts {max(hook.nverts)}" if hook else ""),flush=True)

if hook and hook.dbg:
    import collections
    prev=-1
    for k,row in enumerate(hook.log):
        if row[2]!=prev: print('window',k,row); prev=row[2]
    print('inverted triangles (bad,total) per window:',[x for x in hook.inv if x[1][0]>0][:40])
