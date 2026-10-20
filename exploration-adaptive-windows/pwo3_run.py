import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness, pwo3, resource
import carto_flow.flow_cartogram.algorithm as alg
E = os.environ.get
h = pwo3.PWO3N(2.0 ** -float(E("BITS", "6")), prune_tol=float(E("TOL", "0.02")), prune_every=int(E("PEVERY", "1")), budget=int(E("VBUDGET", "0")), factor=float(E("PF", "6")), rebuild_every=int(E("REBUILD", "1")), diag=E("DIAG") == "1", substep=E("SUBSTEP", "1") == "1", min_ratio=float(E("MINRATIO", "0")), dist_test=E("NODIST") != "1", maxring=int(E("MAXRING", "64")), fix=E("FIX", "kernel"), dump=E("DUMP") == "1", rof=E("ROF") == "1", limit=E("LIMIT") == "1", net=E("NET") == "1")
alg.PW_HOOK = h
if h.net: alg.VW_HOOK = h.hook
def extra():
    if h.dumps:
        import pickle; pickle.dump(h.dumps, open(E("DUMPFILE", "/tmp/dumps.pkl"), "wb"))
    return (f"windows {h.nwin} rebuilds {h.n_rebuilds} forced {h.n_forced} raw_iters {h.raw_iters} raw_tri {h.raw_tri} raw_leaves {h.raw_leaves} kernel {h.n_kernel} kfail {h.n_kernel_fail} dp {h.n_dp} dpfail {h.n_dp_fail} retry {h.n_retry} retryfail {h.n_retry_fail} surv_iters {h.surv_iters} surv_leaves {h.surv_leaves} remaps {h.n_remap} rof {h.n_rof} limit {h.n_limit} limitfail {h.n_limit_fail}" + (f" net_checks {h.hook.n_checks} net_repairs {h.hook.n_repairs} net_inserted {h.hook.nv.n_inserted}" if h.net else "") + f" " + str({k: round(v, 1) for k, v in h.t.items() if k in ('resolve', 'advance', 'begin')}))
harness.run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1000, E("LABEL", "pwo3"), extra)
