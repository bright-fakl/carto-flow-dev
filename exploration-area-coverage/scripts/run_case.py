"""Run variants on one case and grid; results are appended to data/out_<case>_<grid>.pkl.

Usage: NUMBA_NUM_THREADS=4 uv run python run_case.py <case> <grid> <set>
  case: states horiz tang tilt districts counties; set: main (coverage x refresh), rob (robustness), min (center/exact only)
"""

import pickle
import sys
from pathlib import Path

from common import COV_NAME, key, load_case, run

HERE = Path(__file__).resolve().parent.parent
case, grid, vset = sys.argv[1], int(sys.argv[2]), sys.argv[3]
covs = [None, 2, 4, 8, "exact"]
variants = []
if vset == "main":
    variants = [dict(cov=c, ro=ro) for ro in (0.01, None) for c in covs]
elif vset == "ro1":
    variants = [dict(cov=c, ro=0.01) for c in covs]
elif vset == "min":
    variants = [dict(cov=c, ro=ro) for ro in (0.01,) for c in (None, "exact")]
elif vset == "rob":
    for c in (None, 4, "exact"):
        for ro in (0.01, None):
            for re in (10, 5):
                for dt in (0.1, 0.2, 0.4, 0.6):
                    variants.append(dict(cov=c, ro=ro, re=re, dt=dt))
out = HERE / "data" / f"out_{case}_{grid}.pkl"
out.parent.mkdir(exist_ok=True)
res = pickle.load(open(out, "rb")) if out.exists() else {}
g, col, base = load_case(case)
for v in variants:
    k = key(v)
    if k in res:
        continue
    r, _ = run(g, col, base, v, grid)
    res[k] = r
    print(case, grid, k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in r.items() if a not in ("score", "refresh_iters", "worst")}, flush=True)
    pickle.dump(res, open(out, "wb"))
