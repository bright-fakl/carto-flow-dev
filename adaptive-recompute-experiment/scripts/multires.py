import sys, warnings, json
from common import *
from carto_flow.flow_cartogram.workflow import CartogramWorkflow
warnings.filterwarnings("ignore")
case, levels = sys.argv[1], int(sys.argv[2])
pols = sys.argv[3].split(",")
RATIO = {"states": {128: 9.2, 256: 12.0, 512: 24.2, 1024: 70.9}, "districts": {128: 18.2, 256: 20.9, 512: 23.1, 1024: 46.8}}[case]
if case == "states":
    g = data.load_us_census(population=True).reset_index(drop=True)
else:
    g = data.load_us_census(level="congressional_district").reset_index(drop=True)
for p in pols:
    kw = dict(POLICIES[p])
    o = MorphOptions(show_progress=False, stall_patience=None, n_iter=300, **kw)
    alg.ALL_STATS.clear()
    wf = CartogramWorkflow(g, "Population", None, None, o)
    wf.morph_multiresolution(min_resolution=128, levels=levels, options=o)
    rows, cost, tit, trec = [], 0.0, 0, 0
    for st, res in zip(alg.ALL_STATS, wf.results[1:]):
        sx = res.grid.sx
        it, rec = st["n"], st["recomputes"]
        c = it + rec * RATIO[sx]
        cost += c; tit += it; trec += rec
        e = res.latest.errors
        rows.append(f"{sx}:{res.status.value[:4]} it={it} rec={rec} mean={e.mean_error_pct:.2f} max={e.max_error_pct:.1f}")
    e = wf.latest.latest.errors
    print(f"{case} L{levels} {p:22s} levels_run={len(rows)} it={tit} rec={trec} cost={cost:.0f} final mean={e.mean_error_pct:.2f} max={e.max_error_pct:.1f} | " + " | ".join(rows), flush=True)
