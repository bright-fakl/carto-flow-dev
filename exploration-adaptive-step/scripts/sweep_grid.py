"""Robustness grid: dt x recompute_every x refresh_on_rise x variant (stall rule at its default)."""

import os
import sys

os.environ["NUMBA_NUM_THREADS"] = "2"
import runlib as r

FINAL = ["base", "A_r3_m0.05", "A_r10_m0.05", "A_r30_m0.05", "B_0.05", "B_0.1", "C_r10", "AB_r10_f0.05"]


def jobs_for(cases, variants=FINAL, dts=(0.1, 0.2, 0.4, 0.6, 0.8), Rs=(10, 5), rrs=("off", "on")):
    return [
        dict(case=c, variant=v, dt=dt, R=R, rr=rr)
        for c in cases
        for v in variants
        for dt in dts
        for R in Rs
        for rr in rrs
    ]


if __name__ == "__main__":
    out, workers = sys.argv[1], int(sys.argv[2])
    cases = sys.argv[3].split(",")
    r.pool_run(jobs_for(cases), out, workers=workers)
