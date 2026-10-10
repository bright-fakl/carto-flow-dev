"""Wall time on an otherwise idle machine: best of 3 repeats per run, run one after the other (NUMBA_NUM_THREADS=4)."""
import json

from common import *

R = 0.01
rows = []
g, col, sc, extra, n0 = load_case("states")
run_one("states", 64, 0.2, R, g=g.iloc[:30])
for case, grid in (("states", 256), ("states", 512), ("districts", 256), ("districts", 512)):
    for dt in (0.2, 0.3, 0.4, 0.6):
        ts = []
        for _ in range(3):
            rec, _, _ = run_one(case, grid, dt, R)
            ts.append(rec["wall"])
        rows.append(dict(case=case, grid=grid, dt=dt, it=rec["it"], rec=rec["rec"], wall_best=min(ts), walls=ts, load=rec["load"]))
        print(rows[-1], flush=True)
json.dump(rows, open(os.path.join(DATA, "timing.json"), "w"))
