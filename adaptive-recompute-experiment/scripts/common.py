import sys, time, json, numpy as np
sys.path.insert(0, "/home/fakl/carto-flow/.claude/worktrees/agent-a26a9a5577467ffc5/src")
import carto_flow.data as data
import carto_flow.flow_cartogram.algorithm as alg
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor
assert "worktrees" in alg.__file__, alg.__file__

def score_hist(res, o):
    c = res.convergence
    return np.maximum(c.mean_log_errors/np.log2(1+o.mean_tol), c.max_log_errors/np.log2(1+o.max_tol))

def summarize(res, o, st, grid):
    s = score_hist(res, o)
    rises = int(np.sum(s[1:] > s[:-1]))
    rises20 = int(np.sum((s[1:] > s[:-1]) & (s[:-1] < 20)))
    e = res.latest.errors
    return dict(status=str(res.status.value if hasattr(res.status,'value') else res.status), it=int(len(s)), rec=st["recomputes"], rises=rises, rises20=rises20,
                mean=float(e.mean_error_pct), max=float(e.max_error_pct), best=float(s.min()), final=float(s[-1]),
                rb=st["rollbacks"], wall=float(res.duration), rec_s=st["recompute_s"])

POLICIES = {}
for R in (10,5,2,1): POLICIES[f"fixed{R}"] = dict(recompute_every=R)
for tol in (0.0,0.01,0.05):
    for mi in (1,2,3):
        POLICIES[f"adapt_t{tol}_m{mi}"] = dict(adaptive_tol_rise=tol, adaptive_min_interval=mi, recompute_every=10)
for tol in (0.0,0.01,0.05):
    for mi in (1,2):
        for rb in ("best","prev"):
            POLICIES[f"adSC_t{tol}_m{mi}_{rb}"] = dict(adaptive_tol_rise=tol, adaptive_min_interval=mi, recompute_every=10, step_control=True, step_rollback=rb)

def run(g, col, base, policy, grid=256, stall=None):
    kw = dict(base); kw.update(POLICIES[policy]); 
    o = MorphOptions(**{**dict(show_progress=False, grid_size=grid, stall_patience=None), **kw})
    alg.LAST_STATS.clear()
    res = morph_gdf(g, col, options=o)
    return summarize(res, o, dict(alg.LAST_STATS), grid), res
