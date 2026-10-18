import warnings,sys; warnings.filterwarnings("ignore")
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import adapt as A, adapt2 as B
cty=data.load_us_census(level="county").reset_index(drop=True)
outs,cell=B.pilot(cty); g2=B.adaptive_max(cty,outs,cell,0.25); v=g2["Population"].to_numpy(float)
w=CartogramWorkflow(g2[["geometry"]].assign(v=v),"v",validate=False)
w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False,snapshot_every=5))
prev=set()
for li,c in enumerate(w):
    if li==0: continue
    its=list(c.snapshots.get_iterations())
    for it in its:
        sn=c.snapshots.get_snapshot(it); o=np.array(sn.geometry,dtype=object); inv=set(np.flatnonzero(~shapely.is_valid(o)))
        new=inv-prev
        if new: print(f"level {li} (grid {c.grid.sx}) iteration {it}: {len(inv)} invalid, {len(new)} new: {[cty['County Name'][i][:18] for i in sorted(new)[:5]]}")
        prev=inv
