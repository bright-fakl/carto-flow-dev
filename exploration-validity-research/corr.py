import os, json, numpy as np
from scipy.stats import spearmanr
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
rs = [json.loads(l) for l in open(d + 'protocol.jsonl')]
rs = [r for r in rs if r['proto'] == 'p4' and 'plat_med' in r]
x = np.array([r['plat_inv'] for r in rs]); y = np.array([r['plat_med'] for r in rs]); z = np.array([r['plat_p95'] for r in rs])
print(len(rs), "spearman(plateau invalid count, plateau median) = %.2f p=%.1e" % tuple(spearmanr(x, y)), "; with p95: %.2f p=%.1e" % tuple(spearmanr(x, z)))
for lo, hi in ((0, 5), (5, 30), (30, 500)):
    m = (x >= lo) & (x < hi); print(f"invalid {lo}-{hi}: n={m.sum()} plateau median geometric mean {np.exp(np.log(y[m]+1e-6).mean()):.4f} p95 mean {z[m].mean():.2f}")
