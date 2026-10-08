import sys
sys.path.insert(0, "/home/fakl/carto-flow/visual_checks/mosaic-options-sweep")
import inputs as IN
from verify import run
for case in IN.CASES:
    for m in (False, True):
        print(f"{case} morph={int(m)} {run(case, m, {})}", flush=True)
