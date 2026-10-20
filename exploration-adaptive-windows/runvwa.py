"""Runner for the adaptive validated windows. env: HOOK=none|vwa, POLICY, N, NCAP, R0, Q, DMAX, START, F32, BUDGET, MINLEN, STOPR, SKIPS, MORPH_OPTS, CLOG"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness, vwa
import carto_flow.flow_cartogram.algorithm as alg
dataset = sys.argv[1] if len(sys.argv) > 1 else "county"
n_iter = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
E = os.environ.get
hook = None
if E("HOOK", "vwa") == "vwa":
    hook = vwa.VWA(min_len=float(E("MINLEN", "1e-6")), stop_rounds=int(E("STOPR", "3")), f32=E("F32", "1") == "1", mem_budget_mb=float(E("BUDGET", "128")),
                   skip_s_cross=E("SKIPS", "1") == "1", policy=E("POLICY", "fixed"), n=int(E("N", "10")), n_cap=int(E("NCAP", "10")), r0=float(E("R0", "2")),
                   q=float(E("Q", "0.99")), dmax=float(E("DMAX", "20")), start=int(E("START", "1")))
    hook.verbose = E("VERBOSE") == "1"
    alg.VW_HOOK = hook
def extra():
    if hook is None: return ""
    if E("CLOG"):
        json.dump(hook.clog, open(E("CLOG"), "w"))
    return (f"windows {hook.n_windows} checks {hook.n_checks} repaired {hook.n_windows_repaired} inserted {hook.n_inserted} maxnwin {hook.max_nwin} "
            f"maxfield {hook.max_field_bytes/2**20:.0f}MB unresolved {hook.unresolved} t_detect {hook.t_detect:.1f}s t_repair {hook.t_repair:.1f}s t_stats {hook.t_stats:.1f}s")
harness.run(dataset, n_iter, E("LABEL", "run"), extra)
