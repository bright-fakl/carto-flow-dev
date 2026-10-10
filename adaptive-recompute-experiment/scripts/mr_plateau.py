import warnings, numpy as np
import carto_flow.data as ex
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.workflow import CartogramWorkflow
warnings.filterwarnings("ignore")
g = ex.load_us_census(population=True).reset_index(drop=True)
def score(res, o):
    c = res.convergence
    return np.maximum(c.mean_log_errors / np.log2(1 + o.mean_tol), c.max_log_errors / np.log2(1 + o.max_tol))
cases = {
  "MorphOptions() defaults":              MorphOptions(show_progress=False, stall_patience=None, n_iter=300),
  "preset_balanced":                       MorphOptions.preset_balanced().copy_with(show_progress=False, stall_patience=None, n_iter=300),
  "preset_balanced + area_scale=1e-6":     MorphOptions.preset_balanced().copy_with(show_progress=False, stall_patience=None, n_iter=300, area_scale=1e-6),
}
for name, o in cases.items():
    print(f"== {name}: dt={o.dt} recompute_every={o.recompute_every} grid_size={o.grid_size} mean_tol={o.mean_tol} max_tol={o.max_tol} area_scale={o.area_scale}")
    r = morph_gdf(g, "Population", options=o.copy_with(grid_size=128))
    s = score(r, r.options)
    print(f"   single grid_size=128:  {r.status.name:10s} it={r.niterations:3d} min score {s.min():.2f} final {s[-1]:.2f}")
    wf = CartogramWorkflow(g, "Population", None, None, o)
    wf.morph_multiresolution(min_resolution=128, levels=3, options=o)
    for res in wf.results[1:]:
        s = score(res, res.options)
        print(f"   multires level {res.grid.sx}x{res.grid.sy}: {res.status.name:10s} it={res.niterations:3d} min score {s.min():.2f} final {s[-1]:.2f}")
