import warnings, numpy as np
import carto_flow.data as ex
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.workflow import CartogramWorkflow
warnings.filterwarnings("ignore")
g = ex.load_us_census(population=True).reset_index(drop=True)
names = g["State Abbreviation"].to_numpy()
o = MorphOptions(show_progress=False, stall_patience=None, n_iter=300)
r = morph_gdf(g, "Population", options=o.copy_with(grid_size=128))
wf = CartogramWorkflow(g, "Population", None, None, o)
wf.morph_multiresolution(min_resolution=128, levels=2, options=o)
tot = g.geometry.area.sum()
target_share = g["Population"].to_numpy() / g["Population"].sum()
def report(label, res):
    e = res.latest.errors
    a = np.array([x.area for x in res.latest.geometry]); cell = res.grid.dx * res.grid.dy
    order = np.argsort(-np.abs(e.log_errors))[:5]
    print(f"{label}: grid {res.grid.sx}x{res.grid.sy}, cell area {cell/1e6:.0f} km2, {res.status.name}, it={res.niterations}")
    for i in order:
        print(f"   {names[i]:3s} err {e.errors_pct[i]:+8.1f}%  area {a[i]/1e6:9.0f} km2 ({a[i]/cell:6.2f} cells)  target {target_share[i]*a.sum()/1e6:9.0f} km2 ({target_share[i]*a.sum()/cell:6.2f} cells)")
report("single grid_size=128", r)
report("multires level 1   ", wf.results[1])
