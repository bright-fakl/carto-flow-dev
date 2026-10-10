"""Score histories (and refresh iterations, step sizes) of selected runs -> data/traces.json."""

import json
import os
import sys

os.environ["NUMBA_NUM_THREADS"] = "2"
import runlib as r

CASES = [("states_t", 0.2), ("horiz", 0.2), ("horiz", 0.6), ("tang", 0.6), ("districts", 0.2), ("districts", 0.6), ("counties", 0.2)]
VARIANTS = ["base", "A_r3_m0.05", "A_r10_m0.05", "A_r30_m0.05", "B_0.05", "B_0.1", "C_r10", "AB_r10_f0.05"]

if __name__ == "__main__":
    out = []
    for case, dt in CASES:
        for rr in ("off", "on"):
            for v in VARIANTS:
                # Stall rule off: the traces show the dynamics, not where the rule stops them.
                o = r.run(case, variant=v, dt=dt, rr=rr, keep_score=True, stall_patience=None)
                o.pop("_res")
                out.append(o)
                print(case, dt, rr, v, o["cls"], o["it"], o["rec"], flush=True)
    json.dump(out, open(sys.argv[1], "w"))
