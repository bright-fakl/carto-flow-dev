import warnings,time,sys,os; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,".")
import carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import carto_flow.flow_cartogram.algorithm as alg
import pw2
mode=sys.argv[1]
if mode!="base":
    h=pw2.Hook(2.0**-6,insert=True); h.tol=0
    if mode.startswith("cov"): h.cov=float(mode[3:])
    alg.PW_HOOK=h
if mode=="base":
    g=data.load_us_census(level="county",max_segment_length=1000).reset_index(drop=True)
else:
    from carto_flow.geo_utils import simplify_coverage
    g=simplify_coverage(data.load_us_census(level="county").reset_index(drop=True),tolerance=4000.0)
v=g["Population"].to_numpy(float); gdf=g[["geometry"]].assign(v=v)
w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution="auto",levels="auto",options=MorphOptions(area_scale=1e-6,n_iter=int(os.environ.get("NIT","1000")),stall_min_efficiency=float(os.environ.get("EFF","0.05")),show_progress=False))
print(mode)
for c in w:
    if c.grid is None: continue
    cv=c.convergence; m=np.asarray(cv.mean_log_error) if hasattr(cv,"mean_log_error") else None
    e=c.get_errors()
    print(f"  cell {c.grid.dx:7.0f} m  {c.niterations:4d} it  {c.status.name:9s} best_it {c.best_iteration}  mean {e.mean_error_pct:6.2f}%  max {e.max_error_pct:7.1f}%")
