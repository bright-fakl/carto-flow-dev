import sys, os, time, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, harness, pw, pw2, xing
import carto_flow.flow_cartogram.algorithm as alg
T = collections.defaultdict(float); N = collections.defaultdict(int)
def wrap(obj, name, label=None):
    f = getattr(obj, name); label = label or f"{obj.__name__ if hasattr(obj,'__name__') else obj.__class__.__name__}.{name}"
    def g(*a, **k):
        t = time.perf_counter(); r = f(*a, **k); T[label] += time.perf_counter() - t; N[label] += 1; return r
    setattr(obj, name, g)
for n in ("build", "_locate", "_apply"): wrap(pw, n)
for n in ("_count", "_fill", "_prune_mask", "_match"): wrap(pw2, n)
wrap(pw2.Hook, "_restructure"); wrap(pw2.Hook, "begin"); wrap(pw2.Hook, "advance")
import xing as X
orig_grid = X.Grid.__init__
def gi(self, *a, **k):
    t = time.perf_counter(); orig_grid(self, *a, **k); T["xing.Grid.build"] += time.perf_counter() - t; N["xing.Grid.build"] += 1
X.Grid.__init__ = gi
wrap(X.Grid, "crossing", "xing.crossing")
bits = float(os.environ.get("BITS", "6")); h = pw2.Hook(2.0 ** -bits, insert=True); h.tol = float(os.environ.get("TOL", "0.02")); h.safe = os.environ.get("SAFE") == "1"
if os.environ.get("COV"): h.cov = float(os.environ["COV"]); h.tol = 0
alg.PW_HOOK = h
ds = sys.argv[1]
t0 = time.time()
harness.run(ds, 1000, "prof")
tot = time.time() - t0
print(f"total {tot:.1f}s windows {len(h.nverts)}")
for k, v in sorted(T.items(), key=lambda x: -x[1]): print(f"  {k:28s} {v:7.2f}s  calls {N[k]}")
