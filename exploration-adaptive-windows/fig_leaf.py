"""Figure: three leaves whose fan inverted (dumps of pwo3_run.py with DUMP=1): deformed leaf polygon, fan with the mean of the corners as center, kernel and the kernel centroid."""
import pickle, sys, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
D = sys.argv[1]
def kernel(P):
    x0, y0 = P.min(0); x1, y1 = P.max(0)
    poly = [np.array(p, float) for p in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    m = len(P)
    for e in range(m):
        a = P[e]; b = P[(e + 1) % m]; ex, ey = b - a
        out = []
        for i in range(len(poly)):
            p = poly[i]; q = poly[(i + 1) % len(poly)]
            sp = ex * (p[1] - a[1]) - ey * (p[0] - a[0]); sq = ex * (q[1] - a[1]) - ey * (q[0] - a[0])
            if sp >= 0: out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq); out.append(p + t * (q - p))
        poly = out
        if len(poly) < 3: return None
    return np.array(poly)
def centroid(K):
    x, y = K[:, 0], K[:, 1]; x2, y2 = np.roll(x, -1), np.roll(y, -1); w = x * y2 - x2 * y; A = w.sum() / 2
    return np.array([((x + x2) * w).sum(), ((y + y2) * w).sum()]) / (6 * A)
cases = []
for f, lab in (("dump_q4_msl800.pkl", "q4, max_segment_length 800"), ("dump_q1_dt024.pkl", "q1, dt 0.24")):
    for P, P0, c in pickle.load(open(D + "/" + f, "rb"))[:2 if "q4" in f else 1]:
        cases.append((lab, P, c))
fig, axs = plt.subplots(1, len(cases), figsize=(4.2 * len(cases), 4.2))
for ax, (lab, P, c) in zip(np.atleast_1d(axs), cases):
    m = len(P)
    ax.add_patch(Polygon(P, closed=True, fc="#dde6f0", ec="k", lw=1.5))
    mean = P[:4].mean(0)
    for t in range(m):
        a = P[t]; b = P[(t + 1) % m]
        cr = (a[0] - mean[0]) * (b[1] - mean[1]) - (a[1] - mean[1]) * (b[0] - mean[0])
        ax.add_patch(Polygon([mean, a, b], closed=True, fc=("#e8a0a0" if cr <= 0 else "none"), ec="#c04040", lw=0.8, alpha=0.8))
    K = kernel(P)
    if K is not None:
        ax.add_patch(Polygon(K, closed=True, fc="#9bd19b", ec="#2a7a2a", lw=1.2, alpha=0.8))
        g = centroid(K); ax.plot(*g, "o", color="#2a7a2a", ms=7, label="kernel centroid")
        for t in range(m):
            ax.plot([g[0], P[t][0]], [g[1], P[t][1]], color="#2a7a2a", lw=0.7)
    ax.plot(*mean, "s", color="#c04040", ms=7, label="mean of corners")
    ax.plot(P[:, 0], P[:, 1], "ko", ms=4)
    ax.set_aspect("equal"); ax.set_title(lab, fontsize=9); ax.legend(fontsize=7, loc="best")
    ax.set_xticks([]); ax.set_yticks([])
fig.tight_layout(); fig.savefig("fig_leaf_kernel.png", dpi=130)
