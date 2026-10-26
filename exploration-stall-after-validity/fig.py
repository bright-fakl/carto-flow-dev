import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
d = json.load(open("continue_valid.json")); E = np.array([r["errors"] for r in d["rows"]]); it = np.array([r["it"] for r in d["rows"]])
keep = it != 992  # the extra snapshot of the best iterate is not on the 20-iteration grid
E, it = E[keep], it[keep]
INK, MUTED, GRID, BLUE, RED = "#1f2933", "#6b7785", "#e4e7eb", "#2a62a3", "#c0392b"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})
fig, axs = plt.subplots(1, 3, figsize=(13, 3.9))
axs[0].plot(it, (E > 10).sum(1), color=BLUE, lw=2, label="above 10 %"); axs[0].plot(it, (E > 5).sum(1), color=MUTED, lw=2, label="above 5 %")
axs[0].set_ylabel("valid counties"); axs[0].set_title("counties above tolerance keep falling", loc="left", fontsize=10); axs[0].legend(frameon=False)
axs[1].plot(it, E.max(1), color=RED, lw=2); axs[1].set_yscale("log"); axs[1].set_ylabel("max error (%)"); axs[1].set_title("the max is held by one sub-cell county", loc="left", fontsize=10)
axs[2].plot(it, E.mean(1), color=BLUE, lw=2, label="mean"); axs[2].plot(it, np.median(E, 1), color=MUTED, lw=2, label="median")
axs[2].set_ylabel("error (%)"); axs[2].set_title("mean and median stay below 1 %", loc="left", fontsize=10); axs[2].legend(frameon=False)
for a in axs: a.set_xlabel("iterations after the stall (finest level)")
fig.tight_layout(); fig.savefig("fig1_continue_valid.png", dpi=150)
