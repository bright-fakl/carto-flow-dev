import warnings,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely, carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
di=data.load_us_census(level="congressional_district").reset_index(drop=True); v=di["Population"].to_numpy(float)
w=CartogramWorkflow(di[["geometry"]].assign(v=v),"v",validate=False); w.morph_multiresolution(min_resolution=64,levels=4,options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
for i,c in enumerate(w):
    o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); t=v/v.sum()*a.sum(); e=abs(a-t)/t*100
    print(i, 64*2**(i-1) if i else "start", str(c.status).split('.')[-1], c.niterations, f"mean {e.mean():.2f} max {e.max():.1f} inv {int((~shapely.is_valid(o)).sum())}")
