import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, xing
z = np.load(os.path.dirname(os.path.abspath(__file__)) + "/out/fail.npz")
S1, E1, offs1 = z["S1"], z["E1"], z["offs1"]
print("step", z["step"], "nverts", len(S1), "dts", z["dts"][:3], len(z["dts"]), "dx", z["dx"])
gS = xing.Grid(S1, offs1, 6.0); fS = gS.crossing(); print("crossings at S1:", fS.sum())
gE = xing.Grid(E1, offs1, 6.0); fE = gE.crossing(); print("crossings at E1:", fE.sum())
first = gE.first
bad = first[fE]
LS = np.hypot(*(S1[bad+1]-S1[bad]).T); LE = np.hypot(*(E1[bad+1]-E1[bad]).T)
print("flagged seg lengths S: quantiles", np.quantile(LS,[0,.25,.5,.75,1]), "E:", np.quantile(LE,[0,.25,.5,.75,1]))
# S0 / E0 (before the rounds)
S0, E0, offs0 = z["S"], z["E0"], z["offs0"]
g0 = xing.Grid(S0, offs0, 6.0); print("crossings at S0:", g0.crossing().sum())
# pairs: brute force among flagged segments in E1 to find actual pairs
idx = np.flatnonzero(fE)
pairs = []
for a in range(len(idx)):
    p = first[idx[a]]
    for b in range(a+1, len(idx)):
        q = first[idx[b]]
        if xing._cross(E1, p, p+1, q, q+1): pairs.append((p, q))
print("pairs", len(pairs))
for p, q in pairs[:5]:
    print("seg", p, "S", S1[p], S1[p+1], "E", E1[p], E1[p+1])
    print("seg", q, "S", S1[q], S1[q+1], "E", E1[q], E1[q+1])
    print(" S dist between segs", "len", np.hypot(*(S1[p+1]-S1[p])), np.hypot(*(S1[q+1]-S1[q])))
