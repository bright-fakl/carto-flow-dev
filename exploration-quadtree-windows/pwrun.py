import warnings,time,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,".")
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
mode=sys.argv[1]; frac=2.0**-float(sys.argv[2]) if len(sys.argv)>2 else 2.0**-8
import pw
if mode=="pw": pw.install(frac)
g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
t=time.time(); w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
c=w[-1]; o=np.array(c.get_geometry(),dtype=object); a=shapely.area(o); tt=v/v.sum()*a.sum(); e=abs(a-tt)/tt*100
print(mode,frac,f"{time.time()-t:.1f}s iters {sum(x.niterations for x in w)} mean {e.mean():.2f} med {np.median(e):.3f} max {e.max():.1f} invalid {int((~shapely.is_valid(o)).sum())}", "mesh nodes/leaves (last):",pw.State.stats[-1] if pw.State.stats else None, f"build {pw.State.t_build:.1f}s",flush=True)
