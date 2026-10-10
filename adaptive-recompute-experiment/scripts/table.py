import sys, pickle
D = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/adaptive/"
RATIO = {  # recompute cost / step cost, measured
    ("states", 256): 12.0, ("states", 512): 24.2, ("states", 1024): 70.9,
    ("districts", 256): 20.9, ("districts", 512): 23.1, ("districts", 1024): 46.8,
    ("counties", 256): 47.5, ("counties", 512): 28.5}
case, grid = sys.argv[1], int(sys.argv[2])
key = "states" if case in ("horiz", "tang", "tilt") else case
ratio = RATIO[(key, grid)]
res = pickle.load(open(D + f"out_{case}_{grid}.pkl", "rb"))
print(f"{case} grid {grid}  (recompute = {ratio} steps)")
print(f"{'policy':26s} {'status':10s} {'it':>4s} {'rec':>4s} {'rise':>4s} {'r<20':>4s} {'rb':>3s} {'mean%':>6s} {'max%':>6s} {'best':>6s} {'cost':>6s} {'wall':>5s}")
for p, r in res.items():
    cost = r["it"] + r["rec"] * ratio
    print(f"{p:26s} {r['status']:10s} {r['it']:4d} {r['rec']:4d} {r['rises']:4d} {r['rises20']:4d} {r['rb']:3d} {r['mean']:6.2f} {r['max']:6.1f} {r['best']:6.2f} {cost:6.0f} {r['wall']:5.1f}")
