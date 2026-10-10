"""Exploration sweep: controller parameters on states, tight states, horizontal anisotropy, districts."""
import os, sys
os.environ["NUMBA_NUM_THREADS"] = "2"
import runlib as r

if __name__ == "__main__":
    out = sys.argv[1]
    variants = ["base"] + [v for v in r.VARIANTS if v != "base"]
    jobs = []
    for case in ("states", "states_t", "horiz", "districts"):
        for v in variants:
            for rr in ("on", "off"):
                jobs.append(dict(case=case, variant=v, rr=rr, keep_score=False))
    r.pool_run(jobs, out, workers=int(sys.argv[2]) if len(sys.argv) > 2 else 4)
