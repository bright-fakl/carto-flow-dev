import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness, pw2
import carto_flow.flow_cartogram.algorithm as alg
bits = float(os.environ.get("BITS", "6")); h = pw2.Hook(2.0 ** -bits, insert=True)
h.tol = float(os.environ.get("TOL", "0.02")); h.safe = os.environ.get("SAFE") == "1"
if os.environ.get("COV"): h.cov = float(os.environ["COV"]); h.tol = 0
alg.PW_HOOK = h
def extra(): return f"windows {len(h.nverts)} maxverts {max(h.nverts)} pruned {h.pruned} safe_restored {getattr(h,'safe_restored',0)} build {h.t_build:.1f}s"
harness.run(sys.argv[1], int(sys.argv[2]), os.environ.get("LABEL", "pw"), extra)
