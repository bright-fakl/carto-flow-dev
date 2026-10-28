"""Compare layout runs: python layout_compare.py <old.pkl> <new.pkl> [phase_old.json phase_new.json]

Prints (1) whether the assignments are identical, (2) a metric table with the acceptance rule of the step 1 page: the
change of the mean region-to-tile distance must stay within the larger of 25 percent of the old value and, for the
states grid layouts, the range of the same metric over six lattice offsets (old and new pin together).
"""

import json
import pickle
import sys

import numpy as np

old = pickle.load(open(sys.argv[1], "rb"))
new = pickle.load(open(sys.argv[2], "rb"))
rng = {}
if len(sys.argv) > 4:
    po, pn = json.load(open(sys.argv[3])), json.load(open(sys.argv[4]))
    rng = {t: (min(po[t] + pn[t]), max(po[t] + pn[t])) for t in po}


def same(a, b):
    return (
        a["n_tiles"] == b["n_tiles"]
        and np.array_equal(a["assignments"], b["assignments"])
        and (a["source_indices"] is None) == (b["source_indices"] is None)
        and (a["source_indices"] is None or np.array_equal(a["source_indices"], b["source_indices"]))
    )


print(
    "| case | lattice tiles old / new | identical | split regions old / new | unassigned core old / new "
    "| mean distance old / new | change | tolerance | within | wall s old / new |"
)
print("|---|---|---|---|---|---|---|---|---|---|")
for name, a in old.items():
    b = new[name]
    tiling = name.split()[2]
    spread = (rng[tiling][1] - rng[tiling][0]) if name.split()[1] == "grid" and name.startswith("states") and tiling in rng else 0.0
    tol = max(0.25 * a["disp_mean"], spread)
    d = b["disp_mean"] - a["disp_mean"]
    nc = f"{a['mosaic_noncontiguous']} / {b['mosaic_noncontiguous']}" if a["mosaic_noncontiguous"] is not None else f"{a['split']} / {b['split']}"
    uc = f"{a['unassigned_core']} / {b['unassigned_core']}" if a["unassigned_core"] is not None else "-"
    print(
        f"| {name} | {a['lattice_tiles']} / {b['lattice_tiles']} | {'yes' if same(a, b) else 'no'} | {nc} | {uc} | "
        f"{a['disp_mean']:.3f} / {b['disp_mean']:.3f} | {100 * d / a['disp_mean']:+.0f} % | {tol:.3f} | "
        f"{'yes' if abs(d) <= tol else 'NO'} | {a['seconds']:.1f} / {b['seconds']:.1f} |"
    )
