import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness, vw
import carto_flow.flow_cartogram.algorithm as alg
dataset = sys.argv[1] if len(sys.argv) > 1 else "county"
n_iter = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
hook = vw.VW(min_len=float(os.environ.get("MINLEN", "1e-7")), depth=int(os.environ.get("DEPTH", "14")), check_every=int(os.environ.get("EVERY", "1")), stop_rounds=int(os.environ.get("STOPR", "0")), factor=float(os.environ.get("GF", "6.0")), local=os.environ.get("LOCAL", "1") == "1", max_len=float(os.environ.get("MAXLEN", "0")))
hook.verbose = os.environ.get('VERBOSE') == '1'
hook.dump_fail = os.environ.get('DUMPFAIL')
alg.VW_HOOK = hook
def extra():
    return (f"windows {hook.n_windows} repaired {hook.n_windows_repaired} rounds {hook.n_rounds} inserted {hook.n_inserted} +long {hook.n_inserted_long} "
            f"unresolved {hook.unresolved} t_detect {hook.t_detect:.1f}s t_repair {hook.t_repair:.1f}s " + str({k: round(v,1) for k,v in hook.tm.items()}))
harness.run(dataset, n_iter, os.environ.get("LABEL", "vw"), extra)
