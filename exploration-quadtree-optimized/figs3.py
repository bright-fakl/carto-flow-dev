import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "#888", "axes.grid": True, "grid.color": "#e5e5e5", "font.size": 9})
d = os.path.dirname(os.path.abspath(__file__))
rows = {
 "prototype, checked pruning (102.8 s)": [("shared flow pipeline (density, FFT, areas)", 20.0), ("shapely round trip per window", 43.0), ("crossing test: grid build + scan", 21.1), ("mesh, location, insertion", 8.6), ("node advection + apply", 4.4), ("other", 5.5)],
 "optimized, mesh reuse 8 (30.0 s)": [("shared flow pipeline (density, FFT, areas)", 15.1), ("shapely round trip per window", 0.0), ("crossing test: grid build + scan", 6.0), ("mesh, location, insertion", 3.1), ("node advection + apply", 3.8), ("other", 2.0)],
 "baseline, no hook (20.6 s)": [("shared flow pipeline (density, FFT, areas)", 20.6)],
}
cols = ["#999", "#c66", "#e9a", "#58a", "#3a7", "#ccc"]
fig, ax = plt.subplots(figsize=(8.5, 3.0))
labels = []
for i, (k, parts) in enumerate(rows.items()):
    left = 0
    for (name, v), c in zip(parts, cols):
        ax.barh(i, v, left=left, color=c, label=name if i == 0 else None); left += v
    labels.append(k)
ax.set_yticks(range(len(rows))); ax.set_yticklabels(labels); ax.invert_yaxis(); ax.set_xlabel("seconds, 3,108 counties at 1 km, n_iter 1000")
ax.legend(fontsize=7, loc="lower right")
fig.tight_layout(); fig.savefig(d + "/fig_time_composition.png", dpi=130)
