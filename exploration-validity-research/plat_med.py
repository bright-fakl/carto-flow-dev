import os, json, numpy as np
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
rs = [json.loads(l) for l in open(d + "protocol.jsonl")]
rs = [r for r in rs if r["proto"] == "p4" and "plat_mean" in r]
for m in ("base", "vw1", "vw10"):
    x = [r for r in rs if r["method"] == m]
    print(m, len(x), "plateau mean %.2f med %.4f p95 %.2f gt10 %.0f inv %.0f" % tuple(np.median([r[k] for r in x]) for k in ("plat_mean", "plat_med", "plat_p95", "plat_gt10", "plat_inv")))
