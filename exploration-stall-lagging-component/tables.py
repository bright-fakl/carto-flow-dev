import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def L(f):
    try: return json.load(open(f))
    except Exception: return {}
rows = []
def row(tag, validity, budget, d):
    if not d: return
    f = d["final"]; lv = d["levels"]
    rows.append((validity, budget, tag, d["total_iter"], " / ".join(f"{l['status'][:4]} {l['niter']}" for l in lv), f["invalid"], f["mean"], f["median"], f["max"], f["n10"], f["n5"]))
for validity in ("repair-crossings", "check"):
    full = L(f"compare_counties-{validity}.json"); fin = L(f"compare_counties-{validity}-finest.json"); fb = L(f"compare_counties-{validity}-finest-bestexcess.json")
    for b in (1000, 3000):
        row("baseline (mean, max)", validity, b, full.get(f"{b}-None"))
        for m, name in (("count1", "(a) count above max_tol, all levels"), ("count", "(a') count, by efficiency, all levels"), ("excess", "(b) excess, all levels"), ("median", "(c) median of lagging, all levels")):
            row(name, validity, b, full.get(f"{b}-{m}"))
        for m, name in (("count1", "(a) count, finest level only"), ("excess", "(b) excess, finest level only")):
            row(name, validity, b, fin.get(f"{b}-{m}"))
        for m, name in (("count1", "(a) count, finest only, best by excess"), ("excess", "(b) excess, finest only, best by excess = chosen")):
            row(name, validity, b, fb.get(f"{b}-{m}"))
print("| validity | budget | design | iterations | levels (status, iterations) | invalid | mean % | median % | max % | above 10 % | above 5 % |\n|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows: print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]:.2f} | {r[7]:.2f} | {r[8]:.0f} | {r[9]} | {r[10]} |")
json.dump(rows, open("table_rows.json", "w"))
INK, MUTED, GRID, BLUE, RED = "#1f2933", "#6b7785", "#e4e7eb", "#2a62a3", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True})
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
for ax, b in zip(axs, (1000, 3000)):
    for r in rows:
        if r[0] != "repair-crossings" or r[1] != b: continue
        base = r[2].startswith("baseline"); chosen = "chosen" in r[2]
        ax.scatter(r[3], r[6], s=60 if chosen or base else 30, color=RED if chosen else (INK if base else BLUE), zorder=3)
        ax.annotate(r[2].split(",")[0].replace("baseline (mean, max)", "baseline")[:24] + ("*" if "finest" in r[2] else ""), (r[3], r[6]), fontsize=7, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("iterations of the ladder"); ax.set_ylabel("mean error (%)"); ax.set_title(f"counties, repair-crossings, n_iter {b}", loc="left", fontsize=10)
fig.text(0.01, 0.01, "* finest level only; red: chosen design", fontsize=7, color=MUTED)
fig.tight_layout(); fig.savefig("fig1_designs.png", dpi=150)
