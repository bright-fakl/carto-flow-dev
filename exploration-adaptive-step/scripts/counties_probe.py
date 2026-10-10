"""One counties run, to estimate the time per run: python counties_probe.py [variant]"""

import os
import sys

os.environ["NUMBA_NUM_THREADS"] = "2"
import runlib as r

if __name__ == "__main__":
    v = sys.argv[1] if len(sys.argv) > 1 else "base"
    o = r.run("counties", variant=v)
    o.pop("_res")
    print({k: o[k] for k in ("status", "cls", "it", "rec", "redo", "best", "final", "s0", "out_mean", "out_max", "out_share10", "wall", "load")})
