import warnings,time,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow, DensitySmooth
g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
for dt in (0.18,0.20,0.22):
    for sig in (0,2000,4000,8000):
        t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False)
        w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,dt=dt,show_progress=False,density_mod=DensitySmooth(sigma=sig) if sig else None))
        el=time.time()-t; c=w[-1]; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); val=shapely.is_valid(o)
        T=v/v[val].sum()*a[val].sum(); e=abs(a-T)/T*100
        lv=" ".join(f"{x.niterations}{x.status.name[0]}" for x in w if x.grid is not None)
        print(f"dt {dt} sigma {sig:5d} m: {el:4.0f}s levels {lv:14s} invalid {int((~val).sum()):3d} valid mean {e[val].mean():.2f} median {np.median(e[val]):.3f} p95 {np.percentile(e[val],95):.2f} >10%: {int((e[val]>10).sum()):3d}  max {e[val].max():.0f}",flush=True)
