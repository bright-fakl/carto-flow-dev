import json, numpy as np
d = json.load(open("continue_valid.json")); shrink = np.array(d["shrink"])
rows = d["rows"]; E = np.array([r["errors"] for r in rows]); it = np.array([r["it"] for r in rows])
tol = 10.0
print("time", d["time"], "snapshots", len(rows), "invalid", [r["invalid"] for r in rows][:3], "...")
def line(i):
    e = E[i]; return dict(it=int(it[i]), mean=round(e.mean(), 3), median=round(float(np.median(e)), 3), p95=round(float(np.percentile(e, 95)), 2), max=round(e.max(), 1),
                          n10=int((e > 10).sum()), n5=int((e > 5).sum()), n1=int((e > 1).sum()), excess=round(float(np.log2(1 + e[e > tol] / 100).sum()), 2))
for i in list(range(0, len(it), 5)) + [len(it) - 1]: print(line(i))
# of the counties above 10 % at the first snapshot: who is left at the end
e0 = E[0] > tol; print("lagging at start", e0.sum(), "of which above 10% at end", int((E[-1][e0] > tol).sum()), "median", np.median(E[0][e0]), "->", np.median(E[-1][e0]))
last = E[-1] > tol; print("above 10% at end", last.sum(), "shrink>10x:", int((shrink[last] < 0.1).sum()) if shrink.min() < 1 else "")
# replay: cycles of 20 iterations. rule S0: mean/max ratios (as in StallMonitor, here on the snapshot values, max_tol 10 %, mean_tol 5 %)
def monitor(measure, patience=4, eff=0.05):
    best = np.inf; none = 0
    for i in range(1, len(it)):
        m = measure(i)
        if m < best * (1 - eff * 0.1): none = 0
        else: none += 1
        best = min(best, m)
        if none >= patience: return int(it[i])
    return None
print("stall at (iterations after the start), by measure:")
print(" max ratio:", monitor(lambda i: E[i].max()))
print(" count above 10%:", monitor(lambda i: (E[i] > 10).sum() + 1e-9))
print(" excess (sum log2 over regions above 10%):", monitor(lambda i: np.log2(1 + E[i][E[i] > 10] / 100).sum()))
print(" median of lagging:", monitor(lambda i: np.median(E[i][E[0] > 10])))
