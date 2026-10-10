import sys, warnings, pickle
from common import *
warnings.filterwarnings("ignore")
case = sys.argv[1]
g = data.load_us_census(population=True).reset_index(drop=True) if case == "states" else data.load_us_census(level="congressional_district").reset_index(drop=True)
for p in sys.argv[2:]:
    r, full = run(g, "Population", dict(n_iter=300), p, grid=128)
    s = score_hist(full, full.options)
    ref = alg.ALL_STATS[-1]["refresh_iters"] if alg.ALL_STATS else []
    print(p, {k: v for k, v in r.items()}, flush=True)
    print(" ".join(f"{x:.1f}" for x in s[::10]), flush=True)
    print("min score at it", int(s.argmin()), s.min(), "last 12:", " ".join(f"{x:.1f}" for x in s[-12:]))
