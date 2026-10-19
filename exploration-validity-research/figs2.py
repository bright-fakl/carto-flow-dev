import os, re, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "#888", "axes.grid": True, "grid.color": "#e5e5e5", "font.size": 9})
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
rs = [json.loads(l) for l in open(d + "protocol.jsonl")]
rs = [r for r in rs if r["proto"] == "p4" and "plat_med" in r]
col = {"base": "#777", "vw1": "#58a", "vw10": "#3a7"}
fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.8))
for ax, k, lab in zip(axs, ("plat_med", "plat_p95"), ("median error of the valid counties (%)", "p95 error of the valid counties (%)")):
    for m in col:
        xs = [r["plat_inv"] + 0.5 for r in rs if r["method"] == m]; ys = [r[k] + 1e-4 for r in rs if r["method"] == m]
        ax.scatter(xs, ys, s=22, color=col[m], label={"base": "baseline", "vw1": "validated windows, every window", "vw10": "validated windows, every 10"}[m], alpha=0.85)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("invalid polygons present (mean over the plateau snapshots, +0.5)"); ax.set_ylabel(lab)
axs[0].legend(fontsize=7, loc="lower left")
fig.suptitle("Fixed schedule (600/150/400 iterations, stall rule off), 13 perturbed configurations: plateau error against the number of invalid polygons", fontsize=9)
fig.tight_layout(); fig.savefig(d + "../fig3_plateau_vs_invalid.png", dpi=130); plt.close(fig)

# fig4: trace
def read(f):
    out = []
    for l in open(d + f):
        m = re.search(r" L3 it\s+(\d+) inv\s+(\d+) mean\s+([\d.]+) med\s+([\d.]+) p95\s+([\d.]+)", l)
        if m: out.append(tuple(float(x) for x in m.groups()))
    return np.array(out)
b = read("trace_base020.log"); v = read("trace_vw1020.log")
fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.4))
for ax, j, lab in zip(axs, (3, 4), ("median error (%)", "p95 error (%)")):
    ax.semilogy(b[:, 0], b[:, j], "o-", ms=3, color="#777", label="baseline"); ax.semilogy(v[:, 0], v[:, j], "o-", ms=3, color="#58a", label="validated windows, every window")
    ax.set_xlabel("iteration of the finest level"); ax.set_ylabel(lab)
axs[0].legend(fontsize=7)
fig.suptitle("Finest level at dt 0.20, fixed schedule: error of the valid polygons at snapshots every 25 iterations", fontsize=9)
fig.tight_layout(); fig.savefig(d + "../fig4_trace.png", dpi=130); plt.close(fig)
print("ok")
