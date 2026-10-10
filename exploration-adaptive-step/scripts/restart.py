"""Restarts from an existing geometry (issue #94 point 2): second run on the output of a first run.

Start states: 'conv' = converged at the tight tolerances; 'loose' = converged at 5 %/20 %
(first stage of a two-phase schedule); 'stall' = best iterate of a run with refresh_on_rise off
at dt 0.6 that did not converge. The second run uses the tight tolerances (mean 0.5 %, max 1 %).
"""

import json
import os
import sys

os.environ["NUMBA_NUM_THREADS"] = "2"
import runlib as r

VARIANTS = ["base", "A_r3_m0.05", "A_r10_m0.05", "A_r30_m0.05", "C_r3", "C_r10", "B_0.1", "AB_r10_f0.05"]
LOOSE = dict(mean_tol=0.05, max_tol=0.2)


def start_geoms(case, grid, kind):
    if kind == "conv":
        o = r.run(case, grid=grid, rr="on")
    elif kind == "loose":
        o = r.run(case, grid=grid, rr="on", extra=LOOSE)
    else:
        o = r.run(case, grid=grid, rr="off", dt=0.6)
    res = o.pop("_res")
    return list(res.get_geometry()), o


if __name__ == "__main__":
    out = []
    for case, grid in (("states_t", 256), ("states_t", 512), ("districts_t", 256), ("districts_t", 512)):
        for kind in ("conv", "loose", "stall"):
            g0, first = start_geoms(case, grid, kind)
            print(case, grid, kind, "start:", first["status"], first["it"], round(first["out_max"], 2), flush=True)
            for rr in ("on", "off"):
                for v in VARIANTS:
                    o = r.run(case, grid=grid, variant=v, rr=rr, geoms=g0, keep_score=True)
                    o.pop("_res")
                    o.update(kind=kind, start_status=first["status"], start_out_max=first["out_max"], start_it=first["it"], start_best=first["best"])
                    # worst score within the first 5 iterations, relative to the score of the start state
                    sc = o["score"]
                    o["first5_max"] = max(sc[:5])
                    o.pop("dt_trace")
                    out.append(o)
                    print("  ", rr, v, o["cls"], o["it"], o["rec"], "s0", round(o["s0"], 2), "first5", round(o["first5_max"], 2), "out_max", round(o["out_max"], 2), flush=True)
    json.dump(out, open(sys.argv[1], "w"))
