"""Converged runs per variant and dt: python bydt.py file.jsonl [case]"""

import collections
import json
import sys

rows = [json.loads(line) for line in open(sys.argv[1])]
if len(sys.argv) > 2:
    rows = [r for r in rows if r["case"] == sys.argv[2]]
d = collections.defaultdict(lambda: [0, 0])
for r in rows:
    k = (r["variant"], r["rr"], r["dt"])
    d[k][1] += 1
    d[k][0] += r["cls"] == "converged"
vs = sorted({r["variant"] for r in rows}, key=lambda v: (v != "base", v))
dts = sorted({r["dt"] for r in rows})
for rr in ("off", "on"):
    print("refresh_on_rise", rr, "dt:", dts)
    for v in vs:
        print(f"{v:14s}", " ".join(f"{d[(v, rr, dt)][0]:2d}/{d[(v, rr, dt)][1]:2d}" for dt in dts))
