"""Unified runner. env: HOOK=none|vw ; INV=1 (density-field repair) ; EVERY, MAXLEN, MINLEN, DEPTH, STOPR, F32, BUDGET, FLAT, FLATREL, MORPH_OPTS, LABEL, MSL"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness, vwd as vw, inv
import carto_flow.flow_cartogram.algorithm as alg
dataset = sys.argv[1] if len(sys.argv) > 1 else "county"
n_iter = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
E = os.environ.get
hook = None
if E("HOOK", "vw") == "vw":
    hook = vw.VW(min_len=float(E("MINLEN", "1e-7")), depth=int(E("DEPTH", "14")), check_every=int(E("EVERY", "1")), stop_rounds=int(E("STOPR", "0")),
                 f32=E("F32") == "1", mem_budget_mb=float(E("BUDGET", "0")), flat_gate=float(E("FLAT", "0")), flat_rel=float(E("FLATREL", "0.03")), flat_abs=float(E("FLATABS", "0.005")), skip_s_cross=E("SKIPS") == "1", mode=E("MODE", "replay"),
                 factor=float(E("GF", "6.0")), local=E("LOCAL", "1") == "1", max_len=float(E("MAXLEN", "0")))
    hook.verbose = E("VERBOSE") == "1"
    hook.dump_fail = E("DUMPFAIL")
    alg.VW_HOOK = hook
if E("INV") == "1":
    alg.INV_HOOK = inv.InvHook(repair=True, exclude=False)
def extra():
    if hook is None: return ""
    return (f"windows {hook.n_windows} repaired {hook.n_windows_repaired} rounds {hook.n_rounds} inserted {hook.n_inserted} +long {hook.n_inserted_long} flat {hook.n_flat} "
            f"maxfield {hook.max_field_bytes/2**20:.0f}MB unresolved {hook.unresolved} t_detect {hook.t_detect:.1f}s t_repair {hook.t_repair:.1f}s " + str({k: round(v, 1) for k, v in hook.tm.items()}))
harness.run(dataset, n_iter, E("LABEL", "run"), extra)
if hook is not None and E('LEFTOVER'):
    for row in hook.leftover_log[:60]: print('  leftover step %d nflag %d S-len min %.4g max %.4g E-len min %.4g rounds %d cell %.0f' % row)
