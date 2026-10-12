"""Grid size, dt and tolerance sets on states and districts (n_iter 500, everything else at the defaults)."""
import itertools
import json
from pathlib import Path

from common import MorphOptions, fmt, run

HERE = Path(__file__).resolve().parent
TOLS = {"loose 15/25 %": (0.15, 0.25), "default 5/10 %": (0.05, 0.10), "tight 1/3 %": (0.01, 0.03)}
rows = []
for name in ("states", "districts"):
    for grid, dt, (tl, (mt, xt)) in itertools.product((128, 256, 512), (0.2, 0.3, 0.4), TOLS.items()):
        o = MorphOptions(grid_size=grid, dt=dt, n_iter=500, mean_tol=mt, max_tol=xt)
        r = run(name, o)
        r.update(dt=dt, tol=tl)
        rows.append(r)
        print(f"{name:9s} grid {grid} dt {dt} {tl:15s}: {fmt(r)}", flush=True)
(HERE / "data" / "preset_matrix.json").write_text(json.dumps(rows))
