import pickle, sys
import numpy as np
D = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/adaptive/"
grid = int(sys.argv[1]); ratio = {256: 47.5, 512: 28.5}[grid]
res = pickle.load(open(D + f"out_counties_{grid}.pkl", "rb"))
print(f"counties {grid}: best score within a budget (recomputes R / iterations I / cost units C)")
print(f"{'policy':22s} {'R<=10':>6s} {'R<=20':>6s} {'R<=30':>6s} {'I<=100':>7s} {'I<=200':>7s} {'I<=300':>7s} {'C<=1000':>8s} {'C<=1700':>8s} {'C<=2400':>8s}")
for p, r in res.items():
    s = np.array(r["score"]); ref = np.array(r["refresh_iters"])
    # recomputes done before iteration i (refresh at step i happens before iteration i's score)
    nrec = np.searchsorted(ref, np.arange(len(s)), side="right")
    cost = np.arange(1, len(s) + 1) + nrec * ratio
    def bR(R):
        m = nrec <= R; return s[m].min() if m.any() else np.nan
    def bI(I): return s[:I].min()
    def bC(C):
        m = cost <= C; return s[m].min() if m.any() else np.nan
    print(f"{p:22s} {bR(10):6.1f} {bR(20):6.1f} {bR(30):6.1f} {bI(100):7.1f} {bI(200):7.1f} {bI(300):7.1f} {bC(1000):8.1f} {bC(1700):8.1f} {bC(2400):8.1f}")
