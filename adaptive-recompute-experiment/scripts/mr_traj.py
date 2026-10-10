import sys, warnings
from common import *
from carto_flow.flow_cartogram.workflow import CartogramWorkflow
warnings.filterwarnings("ignore")
case = sys.argv[1]
g = data.load_us_census(population=True).reset_index(drop=True) if case == "states" else data.load_us_census(level="congressional_district").reset_index(drop=True)
for p in sys.argv[2:]:
    o = MorphOptions(show_progress=False, stall_patience=None, n_iter=300, **POLICIES[p])
    alg.ALL_STATS.clear()
    wf = CartogramWorkflow(g, "Population", None, None, o)
    wf.morph_multiresolution(min_resolution=128, levels=3, options=o)
    res = wf.results[1]
    s = score_hist(res, o)
    ref = alg.ALL_STATS[0]["refresh_iters"]
    print(p, "level0 grid", res.grid.sx, "refreshes", len(ref), "min", s.min(), "at", int(s.argmin()))
    print(" ".join(f"{x:.1f}{'*' if i in ref else ''}" for i, x in enumerate(s) if 150 <= i < 190))
    print(" ".join(f"{x:.0f}" for x in s[::15]))
