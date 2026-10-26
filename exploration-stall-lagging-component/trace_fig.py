"""Plot trace.json: the three stall-rule measures over the iterations of the finest county level, and when each rule would stall.
usage: trace_fig.py <dir>"""
import sys, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from carto_flow.flow_cartogram.stall import StallMonitor, cycle_length
from carto_flow.flow_cartogram import MorphOptions
d = sys.argv[1]; t = json.load(open(f"{d}/trace.json"))
run = np.array([[np.nan if v is None else v for v in r] for r in t["runs"][-1]], float)  # step, mean, max, moved, lag
step, mean, mx, moved, lag = run.T
cycle = cycle_length(MorphOptions().recompute_every)
def stall_step(use_lag):
    m = StallMonitor(4, 0.05, cycle)
    for s, a, b, mv, l in run:
        if m.update(int(s), a, b, mv, l if use_lag else None): return int(s) + 1
    return None
old, new = stall_step(False), stall_step(True)
lv = t["levels"][-1]; print("levels", t["levels"], "old stall", old, "new stall", new, "cycle", cycle)
INK, MUTED, GRID, BLUE, RED, GREEN = "#1f2933", "#6b7785", "#e4e7eb", "#2a62a3", "#c0392b", "#2e8b57"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})
fig, axs = plt.subplots(1, 3, figsize=(14, 4.1))
for ax, y, title, ylabel, color in ((axs[0], mean, "old: mean error / mean_tol", "ratio (1 = on tolerance)", MUTED), (axs[1], mx, "old: max error / max_tol", "ratio (1 = on tolerance)", MUTED), (axs[2], lag, "new: lagging error", "total log2 excess", BLUE)):
    ax.plot(step + 1, y, color=color, lw=1.6); ax.set_yscale("log"); ax.set_title(title, loc="left", fontsize=10); ax.set_ylabel(ylabel); ax.set_xlabel("iteration of the finest level")
    if old: ax.axvline(old, color=RED, lw=1.4, ls="--")
    if new: ax.axvline(new, color=GREEN, lw=1.4, ls="--")
    elif lv["status"] != "stalled": ax.axvline(lv["niter"], color=GREEN, lw=1.4, ls="--")
axs[0].axhline(1, color=INK, lw=0.8); axs[1].axhline(1, color=INK, lw=0.8)
axs[2].text(0.02, 0.04, f"red dashed: old rule stalls (iteration {old})\ngreen dashed: new rule ends the run ({lv['status']}, iteration {lv['niter']})", transform=axs[2].transAxes, ha="left", va="bottom", fontsize=8.5, color=INK)
fig.tight_layout(); fig.savefig(f"{d}/fig2_trace.png", dpi=150)
json.dump(dict(old=old, new=new, cycle=cycle, level=lv), open(f"{d}/trace_summary.json", "w"))
