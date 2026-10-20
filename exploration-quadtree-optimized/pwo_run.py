import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness, pwo, resource
import carto_flow.flow_cartogram.algorithm as alg
E = os.environ.get
h = pwo.PWO(2.0 ** -float(E("BITS", "6")), prune_tol=float(E("TOL", "0.02")), prune_every=int(E("PEVERY", "1")), budget=int(E("VBUDGET", "0")), factor=float(E("PF", "6")), rebuild_every=int(E("REBUILD", "1")), diag=E("DIAG") == "1", substep=E("SUBSTEP", "1") == "1", min_ratio=float(E("MINRATIO", "0")), dist_test=E("NODIST") != "1", maxring=int(E("MAXRING", "64")))
alg.PW_HOOK = h
def extra():
    return (f"windows {h.nwin} maxverts {max(h.nverts)} inserted {h.n_inserted} pruned {h.n_pruned} restoredruns {h.n_restored_runs} rebuilds {h.n_rebuilds} forced {h.n_forced} retry {h.n_retry} retryfail {h.n_retry_fail} inv_iters {h.inv_iters} inv_tri {h.inv_tri} " + str({k: round(v, 1) for k, v in h.t.items()}))
harness.run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1000, E("LABEL", "pwo"), extra)
