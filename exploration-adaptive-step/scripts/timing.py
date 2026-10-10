"""Wall times of the final candidates: sequential runs, NUMBA_NUM_THREADS=4, two repetitions (minimum reported)."""

import json
import os
import sys

os.environ["NUMBA_NUM_THREADS"] = "4"
import runlib as r

CASES = [("states", 0.2), ("states_t", 0.2), ("horiz", 0.6), ("districts", 0.6), ("counties", 0.2)]
VARIANTS = ["base", "A_r3_m0.05", "A_r10_m0.05", "B_0.1", "AB_r10_f0.05"]

if __name__ == "__main__":
    out = []
    # warm-up (numba compilation, caches)
    r.run("states", variant="base")
    for case, dt in CASES:
        for rr in ("off", "on"):
            for v in VARIANTS:
                reps = []
                for _ in range(2):
                    o = r.run(case, variant=v, dt=dt, rr=rr)
                    o.pop("_res")
                    reps.append(o)
                o = min(reps, key=lambda x: x["wall"])
                o["walls"] = [x["wall"] for x in reps]
                o["loads"] = [x["load"] for x in reps]
                out.append(o)
                print(case, dt, rr, v, o["cls"], o["it"], o["rec"], [round(w, 2) for w in o["walls"]], [round(x, 1) for x in o["loads"]], flush=True)
    json.dump(out, open(sys.argv[1], "w"))
