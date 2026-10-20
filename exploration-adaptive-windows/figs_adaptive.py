"""Figures of the page: validated-window check policies over the perturbation protocol (B2) and quadtree rebuild rules (B4, B4b)."""
import sys, json, collections, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ad_parse
R = sys.argv[1]
def load(*fs):
    d = {}
    for f in fs: d.update(ad_parse.load(R + "/" + f))
    return d
d = load("resB2.jsonl")
inputs = ["county", "mid2000", "mid3000", "coarse6000"]
pols = ["base", "f3", "f10", "f20", "dens2", "bo"]
fig, axs = plt.subplots(2, len(inputs), figsize=(3.6 * len(inputs), 5.6), sharex=True)
cols = {"base": "#888888", "f3": "#7fa6d8", "f10": "#2c6fbb", "f20": "#1a4a82", "dens2": "#e0a050", "bo": "#c0603a"}
for j, inp in enumerate(inputs):
    inv = []; tm = []
    for p in pols:
        rows = [v for k, v in d.items() if k.split("/")[1] == inp and k.split("/")[3] == p]
        inv.append(sum(v["inv"] for v in rows)); tm.append(np.median([v["time"] for v in rows]))
    axs[0, j].bar(pols, [max(x, 0.5) for x in inv], color=[cols[p] for p in pols]); axs[0, j].set_yscale("log"); axs[0, j].set_title(inp, fontsize=10)
    for i, x in enumerate(inv): axs[0, j].text(i, max(x, 0.5) * 1.15, str(x), ha="center", fontsize=8)
    axs[1, j].bar(pols, tm, color=[cols[p] for p in pols])
    for i, x in enumerate(tm): axs[1, j].text(i, x + 0.5, f"{x:.0f}", ha="center", fontsize=8)
    axs[1, j].tick_params(axis="x", labelrotation=45)
axs[0, 0].set_ylabel("invalid polygons, all runs"); axs[1, 0].set_ylabel("median time (s)")
fig.suptitle("Validated windows: check policies over the perturbation protocol (7 configurations for counties, 3 for the others)", fontsize=10)
fig.tight_layout(); fig.savefig("fig_vw_policies.png", dpi=130)

d = load("resB4.jsonl", "resB4b.jsonl")
inputs = ["county", "cd", "coarse", "mid2000", "mid3000"]
vars_ = ["q1", "q4", "q8", "r8", "r6", "r4", "r2", "r2RL", "r0", "r0RL"]
fig, axs = plt.subplots(1, len(inputs), figsize=(3.4 * len(inputs), 3.8), sharey=False)
for j, inp in enumerate(inputs):
    ax = axs[j]
    for i, v in enumerate(vars_):
        k = f"B4/{inp}/{v}"
        if k not in d: continue
        r = d[k]
        ax.bar(i, r["time"], color="#c04040" if r["inv"] else "#2c6fbb")
        ax.text(i, r["time"] + 0.5, f"{r.get('rebuilds',0):.0f}", ha="center", fontsize=7)
    ax.set_xticks(range(len(vars_))); ax.set_xticklabels(vars_, rotation=60, fontsize=8); ax.set_title(inp, fontsize=10)
axs[0].set_ylabel("time (s); label = mesh rebuilds; red = invalid polygons")
fig.suptitle("Quadtree windows: rebuild rules, 1,000 iterations (qN: reuse N windows, area ratio 0.6; rX: area ratio 0.X without a window cap; RL: rebuild after a fix + step limiter)", fontsize=9)
fig.tight_layout(); fig.savefig("fig_qt_rebuild.png", dpi=130)
