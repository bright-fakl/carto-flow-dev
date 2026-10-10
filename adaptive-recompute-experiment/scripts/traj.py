import pickle, sys
D = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/adaptive/"
case, grid = sys.argv[1], int(sys.argv[2])
res = pickle.load(open(D + f"out_{case}_{grid}.pkl", "rb"))
lo, hi = int(sys.argv[3]), int(sys.argv[4])
for p in sys.argv[5:]:
    r = res[p]; s = r["score"]; ref = set(r["refresh_iters"])
    print(p, "refresh at", [i for i in r["refresh_iters"] if lo <= i < hi])
    print(" ".join(f"{s[i]:.1f}{'*' if i in ref else ''}{'^' if i>0 and s[i]>s[i-1] else ''}" for i in range(lo, min(hi, len(s)))))
