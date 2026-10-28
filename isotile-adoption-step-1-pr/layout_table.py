"""Markdown table of the layout metrics: python layout_table.py layouts_old.pkl layouts_new.pkl phase_old.json phase_new.json"""

import json
import pickle
import sys

old = pickle.load(open(sys.argv[1], "rb"))
new = pickle.load(open(sys.argv[2], "rb"))
po, pn = json.load(open(sys.argv[3])), json.load(open(sys.argv[4]))
rng = {t: (min(po[t] + pn[t]), max(po[t] + pn[t])) for t in po}
print("| case | lattice tiles old / new | assigned | split old / new | mean distance old / new | change | tolerance | within | largest distance old / new |")
print("|---|---|---|---|---|---|---|---|---|")
for name, a in old.items():
    b = new[name]
    tiling = name.split()[2]
    spread = (rng[tiling][1] - rng[tiling][0]) if name.split()[1] == "grid" and tiling in rng and name.startswith("states") else 0.0
    tol = max(0.25 * a["disp_mean"], spread)
    d = b["disp_mean"] - a["disp_mean"]
    print(
        f"| {name} | {a['lattice_tiles']} / {b['lattice_tiles']} | {a['assigned']} | {a['split']} / {b['split']} | "
        f"{a['disp_mean']:.3f} / {b['disp_mean']:.3f} | {100 * d / a['disp_mean']:+.0f} % | {tol:.3f} | {'yes' if abs(d) <= tol else 'NO'} | "
        f"{a['disp_max']:.2f} / {b['disp_max']:.2f} |"
    )
