import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
gdf, v = harness.load("county")
w = CartogramWorkflow(gdf, "v", validate=False)
w.morph_multiresolution(min_resolution="auto", levels="auto", options=MorphOptions(area_scale=1e-6, n_iter=1000, show_progress=False, benchmark=True))
for c in w:
    b = c.benchmark
    if b is None: continue
    print(f"grid {c.grid.sx}x{c.grid.sy}: its {c.niterations} density {b.density_s:.2f}s in {b.density_calls} calls ({b.density_s/max(b.density_calls,1)*1000:.0f} ms), velocity {b.velocity_s:.2f}s ({b.velocity_s/max(b.density_calls,1)*1000:.0f} ms per call), displacement {b.displacement_s:.2f}s, areas {b.areas_s:.2f}s")
