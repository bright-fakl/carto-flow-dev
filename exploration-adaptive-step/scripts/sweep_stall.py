"""Stall rule x controller: runs with stall_patience in {None, 4, 2, 1} (tag = patience)."""

import os
import sys

os.environ["NUMBA_NUM_THREADS"] = "2"
import runlib as r

if __name__ == "__main__":
    out, workers = sys.argv[1], int(sys.argv[2])
    jobs = []
    for case in ("states", "states_t", "districts", "horiz", "tang", "tilt", "counties"):
        for dt in (0.2, 0.6):
            for rr in ("off", "on"):
                for v in ("base", "A_r10_m0.05", "B_0.1", "AB_r10_f0.05"):
                    for p in (None, 4, 2, 1):
                        jobs.append(dict(case=case, variant=v, dt=dt, rr=rr, stall_patience=p, tag=str(p)))
    r.pool_run(jobs, out, workers=workers)
