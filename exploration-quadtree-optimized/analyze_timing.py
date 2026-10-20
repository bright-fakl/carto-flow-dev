import os, json, numpy as np, collections
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
import sys
PR = sys.argv[1] if len(sys.argv) > 1 else "t"
rs = [json.loads(l) for l in open(d + "protocol.jsonl")]
rs = [r for r in rs if r["proto"] == PR]
G = collections.OrderedDict()
for r in rs: G.setdefault(r["method"], []).append(r)
print(f"{'input_method':16s} n  time median [min-max]  rss MB  invalid (reps)  vertices end   mean/med/p95 (median over reps)  >10%")
for k, v in G.items():
    t = np.array([x["time"] for x in v]); inv = [x["invalid"] for x in v]
    print(f"{k:16s} {len(v)}  {np.median(t):6.1f} [{t.min():.1f}-{t.max():.1f}]  {np.median([x['rss_mb'] for x in v]):5.0f}  {inv}  {int(np.median([x['nv'] for x in v])):>9,d}  {np.median([x['mean'] for x in v]):.2f}/{np.median([x['med'] for x in v]):.3f}/{np.median([x['p95'] for x in v]):.2f}  {int(np.median([x['gt10'] for x in v]))}")

import re
print()
print("iterations and time per iteration (median over repeats)")
for k, v in G.items():
    its = [sum(int(x) for x in re.findall(r"(\d+)it", r["levels"])) for r in v]
    t = [r["time"] for r in v]
    print(f"{k:16s} iterations {its}  s per 1000 iterations {np.median([a / max(b,1) * 1000 for a, b in zip(t, its)]):.1f}")
