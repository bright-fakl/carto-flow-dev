"""Multiresolution runs (min_resolution=128, levels 3): per-level status, iterations, recomputes, cost.

Each level continues from the previous level's returned (best) iterate, as in
CartogramWorkflow.morph_multiresolution, which stops at the first converged level. The loop is
repeated here to read the counters per level.
"""

import copy
import json
import os
import sys

os.environ.setdefault("NUMBA_NUM_THREADS", "2")
import runlib as r
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.options import MorphStatus
from carto_flow.flow_cartogram.workflow import CartogramWorkflow


def multires(case, variant="base", rr="on", levels=3, min_res=128, stall=4, n_iter=300, dt=0.2, R=10):
    g, col, base = r.load_case(case)
    kw = dict(show_progress=False, n_iter=n_iter, dt=dt, recompute_every=R, stall_patience=stall)
    kw.update({k: v for k, v in base.items() if k != "n_iter"})
    kw["refresh_on_rise"] = 0.01 if rr == "on" else None
    kw.update(r.VARIANTS[variant])
    o = MorphOptions(**kw)
    wf = CartogramWorkflow(g, col, None, None, o)
    from carto_flow.flow_cartogram.grid import build_multilevel_grids

    grids = build_multilevel_grids(wf._original_gdf.total_bounds, min_res, levels, margin=o.grid_margin, square=o.grid_square)
    rows, cost, tit, trec, wall = [], 0.0, 0, 0, 0.0
    for lev, grid in enumerate(grids):
        lo = copy.deepcopy(o)
        lo.grid = grid
        if lev > 0:
            lo.prescale_components = False
        r.CNT.update(rec=0, disp=0, refresh_iters=[], disp_dt=[])
        res = wf.morph(options=lo)
        sx = grid.sx
        it, rec = res.niterations, r.CNT["rec"]
        c = it + rec * r.RATIO[case][sx]
        cost += c
        tit += it
        trec += rec
        wall += res.duration
        s = r.score_of(res.convergence, lo)
        rows.append(dict(grid=sx, status=res.status.value, it=it, rec=rec, best=float(s.min()), s0=float(s[0]), cost=c))
        if res.status == MorphStatus.CONVERGED:
            break
    mean_s, max_s, share10 = r.share_errors(list(wf.latest.get_geometry()), g[col].values)
    return dict(case=case, variant=variant, rr=rr, stall=stall, dt=dt, R=R, levels=rows, it=tit, rec=trec, cost=cost,
                wall=wall, out_mean=mean_s * 100, out_max=max_s * 100, out_share10=share10 * 100,
                final=rows[-1]["status"])


if __name__ == "__main__":
    out = sys.argv[1]
    done = set()
    if os.path.exists(out):
        done = {(d["case"], d["variant"], d["rr"], d["stall"], d["dt"]) for d in map(json.loads, open(out))}
    variants = ["base", "A_r3_m0.05", "A_r10_m0.05", "A_r30_m0.05", "B_0.1", "C_r10", "C_r3", "AB_r10_f0.05"]
    with open(out, "a") as f:
        for case in ("states", "districts", "states_t"):
            for stall in (4, None):
                for rr in ("on", "off"):
                    for dt in (0.2, 0.4):
                        for v in variants:
                            if (case, v, rr, stall, dt) in done:
                                continue
                            d = multires(case, v, rr, stall=stall, dt=dt)
                            f.write(json.dumps(d) + "\n")
                            f.flush()
                            print(case, v, rr, stall, dt, d["final"], d["it"], d["rec"], round(d["cost"]), round(d["out_max"], 1), [(x["grid"], x["status"][:4], x["it"]) for x in d["levels"]], flush=True)
