import os, sys, json, numpy as np
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
proto = sys.argv[1] if len(sys.argv) > 1 else "p4"
recs = [json.loads(l) for l in open(d + "protocol.jsonl")]
recs = [r for r in recs if r["proto"] == proto and "plat_mean" in r]
def cname(r):
    c = r["cfg"]; s = []
    if c["MORPH_OPTS"]: s.append("dt%.2f" % json.loads(c["MORPH_OPTS"])["dt"])
    if c["MSL"]: s.append("msl" + c["MSL"])
    return "_".join(s)
cfgs = []
for r in recs:
    if cname(r) not in cfgs: cfgs.append(cname(r))
methods = ["base", "vw1", "vw10"]
T = {(cname(r), r["method"]): r for r in recs}
cfgs = [c for c in cfgs if all((c, m) in T for m in methods)]
print("plateau = mean over the snapshots of the last 100 iterations of the finest level (valid polygons of each snapshot)")
print(f"{'config':10s} | " + " | ".join(f"{m:>5s}: inv  mean   med   p95  >10%" for m in methods))
for c in cfgs:
    print(f"{c:10s} | " + " | ".join(f"{'':>5s}  {T[(c,m)]['plat_inv']:4.0f} {T[(c,m)]['plat_mean']:5.2f} {T[(c,m)]['plat_med']:5.3f} {T[(c,m)]['plat_p95']:5.2f} {T[(c,m)]['plat_gt10']:4.0f}" for m in methods))
rng = np.random.default_rng(1)
try:
    from scipy.stats import wilcoxon
except Exception:
    wilcoxon = None
print(f"\npaired over {len(cfgs)} configurations: ratio method/base, plateau metrics")
for m in methods[1:]:
    for k in ("plat_mean", "plat_med", "plat_p95", "plat_gt10"):
        x0 = np.array([T[(c, "base")][k] for c in cfgs]); x1 = np.array([T[(c, m)][k] for c in cfgs])
        lr = np.log((x1 + 1e-3) / (x0 + 1e-3)); bs = [np.median(rng.choice(lr, len(lr))) for _ in range(4000)]
        p = wilcoxon(lr).pvalue if wilcoxon else float("nan")
        print(f"  {m:5s} {k:9s}: median ratio {np.exp(np.median(lr)):.2f} (95% {np.exp(np.percentile(bs,2.5)):.2f}-{np.exp(np.percentile(bs,97.5)):.2f}), geometric mean {np.exp(lr.mean()):.2f}, lower in {(lr<0).sum()}, higher in {(lr>0).sum()}, Wilcoxon p {p:.3f}")
print("\nfinal-iterate (own valid set) invalid counts: " + ", ".join(f"{m}: median {np.median([T[(c,m)]['invalid'] for c in cfgs]):.0f} max {max(T[(c,m)]['invalid'] for c in cfgs)}" for m in methods))
