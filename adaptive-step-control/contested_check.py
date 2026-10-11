"""Check of the contested-regions condition that was tried and dropped: constant dt, the rule with CONTESTED_FRACTION = 0 (dead band only) and 0.8.

The branch no longer has the constant; this script needs a checkout where stepsize.CONTESTED_FRACTION exists
(commit 1a70e9d of the earlier head of the branch). Run from there:
    NUMBA_NUM_THREADS=8 uv run python contested_check.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_figures import options_for, source, true_errors
import carto_flow.flow_cartogram.stepsize as ss
from carto_flow.flow_cartogram import CartogramWorkflow, morph_gdf
from carto_flow.flow_cartogram.grid import build_multilevel_grids
modes = [("constant", False, None), ("c=0 (dead band only)", True, 0.0), ("c=0.8", True, 0.8)]
def mres(name, tol, dt):
    gdf = source(name); res = []
    for lab, ad, c in modes:
        if c is not None: ss.CONTESTED_FRACTION = c
        o = options_for(name, ad, 256, dt, tol, n_iter=300); wf = CartogramWorkflow(gdf, "Population", options=o); out = []
        for lvl, grid in enumerate(build_multilevel_grids(wf._original_gdf.total_bounds, 128, 3, margin=o.grid_margin, square=True)):
            lo = o.copy_with(grid=grid)
            if lvl > 0: lo.prescale_components = False
            r = wf.morph(options=lo); out.append(f"{int(grid.sx)}:{r.status.value[0]}{r.niterations}")
            if r.status.value == "converged": break
        res.append(" ".join(out) + f" /{true_errors(wf.last.get_geometry(), gdf['Population']).max()*100:.1f}%")
    return res
print("== multiresolution: constant | c=0 | c=0.8")
for name, tol, dt in [("districts",(.005,.01),.2),("districts",(.002,.004),.2),("districts",None,.4),("districts",(.005,.01),.4),("states",(.005,.01),.2)]:
    print(name, tol, dt, "|", " | ".join(mres(name, tol, dt)), flush=True)
cases = [("states",128,.2,(.002,.004),.01),("states",256,.2,(.002,.004),.01),("states",512,.4,(.002,.004),.01),("states",128,.2,(.001,.002),.01),("states",256,.2,(.001,.002),.01),("states",128,.2,(.002,.004),None),
         ("districts",256,.2,(.005,.01),.01),("districts",256,.4,(.005,.01),.01),("states",256,.6,None,.01),("districts",256,.4,None,.01),("districts",128,.2,(.002,.004),.01),("districts",128,.4,(.01,.02),.01),("districts",256,.4,(.005,.01),None)]
tot = {m[0]: 0 for m in modes}
print("== single runs: constant | c=0 | c=0.8   (status+iterations/true max %)")
for name,grid,dt,tol,rise in cases:
    gdf = source(name); row = []
    for lab, ad, c in modes:
        if c is not None: ss.CONTESTED_FRACTION = c
        r = morph_gdf(gdf, "Population", options=options_for(name, ad, grid, dt, tol, recompute_on_rise=rise))
        row.append(f"{r.status.value[0]}{r.niterations}/{true_errors(r.get_geometry(), gdf['Population']).max()*100:.2f}%"); tot[lab] += r.niterations
    print(name, grid, dt, tol, rise, "|", " | ".join(row), flush=True)
print("total iterations", tot)
