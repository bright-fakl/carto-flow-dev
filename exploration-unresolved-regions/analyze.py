"""Tables and figures of measure.json: what each threshold excuses (offline, from the baseline levels) and what the runs did."""
import json, sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import carto_flow.data as data
out = sys.argv[1]
M = json.load(open(f"{out}/measure.json"))
g = data.load_us_census(level="county", max_segment_length=1000).reset_index(drop=True)
T = np.asarray(g.geometry.area).sum() * g["Population"].to_numpy(float) / g["Population"].sum()
mean_tol, max_tol = np.log2(1.05), np.log2(1.10)
ks = (0.25, 0.5, 1, 2, 4, 8)
print("== offline, baseline levels: regions excused, and would the level converge")
rows = []
for L in M["county_0"]["levels"]:
    le = np.array(L["log_errors"]); cell = L["cell"]; diff = T * np.abs(2.0 ** le - 1) / cell; rel = np.abs(le)
    r = dict(grid=L["grid"], status=L["status"], n10=int((rel >= max_tol).sum()))
    for k in ks:
        ex = (diff <= k) & (rel >= max_tol); eff = np.where(diff <= k, 0, rel)
        sub = T / cell < k; keep = ~sub; eff2 = rel[keep]
        r[k] = dict(abs_excused=int(ex.sum()), abs_conv=bool(eff.mean() < mean_tol and eff.max() < max_tol), still_above=int(((eff >= max_tol)).sum()),
                    sub_cells=int(sub.sum()), sub_excused=int((sub & (rel >= max_tol)).sum()), sub_conv=bool(eff2.mean() < mean_tol and eff2.max() < max_tol), sub_still=int((eff2 >= max_tol).sum()))
    rows.append(r); print(json.dumps(r))
json.dump(rows, open(f"{out}/offline.json", "w"), indent=1)
print("== runs")
for key, R in M.items():
    print(key, round(R["time"]), [(l["grid"], l["status"], l["niter"], l["n_unresolved"], round(l["mean_pct"], 2), round(l["max_pct"], 1), l["n10"]) for l in R["levels"]])
INK, MUTED, GRID, BLUE, RED = "#1f2933", "#6b7785", "#e4e7eb", "#2a62a3", "#c0392b"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
last = rows[-1]
axs[0].plot(ks, [last[k]["abs_excused"] for k in ks], "o-", color=BLUE, lw=2, label="absolute tolerance: excused above 10 %")
axs[0].plot(ks, [last[k]["sub_excused"] for k in ks], "o-", color=RED, lw=2, label="exclude targets below k cells: above 10 % excluded")
axs[0].axhline(last["n10"], color=MUTED, ls="--", lw=1); axs[0].text(ks[0], last["n10"] + 2, "above 10 % in the baseline", color=MUTED, fontsize=9)
axs[0].set_xscale("log", base=2); axs[0].set_xlabel("k (cells)"); axs[0].set_ylabel("counties"); axs[0].set_title(f"finest level ({last['grid']}): what each rule excuses", loc="left", fontsize=10); axs[0].legend(frameon=False, fontsize=8)
ks_run = [k for k in (0, 1, 2, 4, 8, 16) if f"county_{k}" in M]
axs[1].plot(ks_run, [M[f"county_{k}"]["time"] for k in ks_run], "o-", color=BLUE, lw=2); axs[1].set_xlabel("area_tol_cells"); axs[1].set_ylabel("ladder time (s)")
axs[1].set_title("ladder time per tolerance", loc="left", fontsize=10)
fig.tight_layout(); fig.savefig(f"{out}/fig1_excused.png", dpi=150)
