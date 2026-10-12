"""dt and tolerance for the high-quality preset (grid 512; n_iter 1000, everything else at the defaults)."""
import itertools
import json
from pathlib import Path

from common import MorphOptions, fmt, run

HERE = Path(__file__).resolve().parent
rows = []
for name in ("states", "districts"):
    for dt, (mt, xt) in itertools.product((0.1, 0.15, 0.2), ((0.01, 0.03), (0.005, 0.01))):
        o = MorphOptions(grid_size=512, dt=dt, n_iter=1000, mean_tol=mt, max_tol=xt)
        r = run(name, o)
        r.update(dt=dt, tol=f"{mt * 100:g}/{xt * 100:g} %")
        rows.append(r)
        print(f"{name:9s} grid 512 dt {dt} tol {r['tol']:9s}: {fmt(r)}", flush=True)
(HERE / "data" / "hq_dt.json").write_text(json.dumps(rows))
