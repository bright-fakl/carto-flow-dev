"""Compare methods over the perturbed configurations. Metrics on the counties valid in all methods of a configuration (common set),
targets normalized on that set; also own-valid metrics and invalid counts from out/protocol.jsonl."""
import sys, os, json, numpy as np
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
proto = sys.argv[1] if len(sys.argv) > 1 else "p1"
spec = sys.argv[2].split(",") if len(sys.argv) > 2 else ["base", "vw1", "vw10"]
spec = [(x.split(":")[0], x.split(":")[1]) if ":" in x else (proto, x) for x in spec]
methods = [f"{p}:{m}" if p != proto else m for p, m in spec]
pm = dict(zip(methods, spec))
recs = [json.loads(l) for l in open(d + "protocol.jsonl")]
recs = [r for r in recs if r["proto"] in {p for p, _ in spec}]
cfgs = []
for r in recs:
    c = (r["cfg"]["MSL"], r["cfg"]["MORPH_OPTS"], r["cfg"]["n_iter"])
    if c not in cfgs: cfgs.append(c)
def cname(c):
    msl, mo, n = c
    s = []
    if mo: s.append("dt%.2f" % json.loads(mo).get("dt"))
    if msl: s.append("msl" + msl)
    if n != 1000: s.append(f"n{n}")
    return "_".join(s) or "default"
rows = {}
for c in cfgs:
    cn = cname(c)
    z = {}
    for m in methods:
        f = d + f"{pm[m][0]}_{cn}_{pm[m][1]}_county.npz"
        if os.path.exists(f): z[m] = np.load(f)
    if len(z) < len(methods): continue
    v = next(iter(z.values()))["v"]
    I = np.all([z[m]["valid"] for m in methods], axis=0)
    for m in methods:
        a = z[m]["area"]; T = v / v[I].sum() * a[I].sum(); e = (np.abs(a - T) / T * 100)[I]
        ev = z[m]["valid"]; Tv = v / v[ev].sum() * a[ev].sum(); eo = (np.abs(a - Tv) / Tv * 100)[ev]
        rows[(cn, m)] = dict(n_common=int(I.sum()), inv=int((~z[m]["valid"]).sum()), mean=e.mean(), med=np.median(e), p95=np.percentile(e, 95), gt10=int((e > 10).sum()),
                             own_mean=eo.mean(), own_gt10=int((eo > 10).sum()))
print(f"{'config':14s} {'common':>6s} | " + " | ".join(f"{m:>5s}: inv  mean   med   p95  >10%" for m in methods))
for c in cfgs:
    cn = cname(c)
    if (cn, methods[0]) not in rows: continue
    print(f"{cn:14s} {rows[(cn, methods[0])]['n_common']:6d} | " + " | ".join(
        f"{'':>5s}  {rows[(cn,m)]['inv']:3d} {rows[(cn,m)]['mean']:5.2f} {rows[(cn,m)]['med']:5.3f} {rows[(cn,m)]['p95']:5.2f} {rows[(cn,m)]['gt10']:4d}" for m in methods))
cn_list = [cname(c) for c in cfgs if (cname(c), methods[0]) in rows]
print()
for k in ("inv", "mean", "med", "p95", "gt10", "own_mean", "own_gt10"):
    line = f"{k:9s}"
    for m in methods:
        x = np.array([rows[(c, m)][k] for c in cn_list], float)
        line += f" | {m}: median {np.median(x):7.3f} min {x.min():7.3f} max {x.max():7.3f}"
    if len(methods) > 1:
        for m in methods[1:]:
            x0 = np.array([rows[(c, methods[0])][k] for c in cn_list], float); x1 = np.array([rows[(c, m)][k] for c in cn_list], float)
            line += f" | {m} better in {(x1 < x0).sum()} of {len(x0)}"
    print(line)

# paired statistics over the independent configurations (n400, n800, n900 are degenerate or duplicates)
excl = {"n400", "n800", "n900"}
use = [c for c in cn_list if c not in excl]
print(f"\npaired log-ratio statistics over {len(use)} configurations (common valid set), ratio = method / {methods[0]}")
rng = np.random.default_rng(0)
try:
    from scipy.stats import wilcoxon
except Exception:
    wilcoxon = None
for m in methods[1:]:
    for k in ("mean", "med", "p95", "gt10"):
        x0 = np.array([rows[(c, methods[0])][k] for c in use], float); x1 = np.array([rows[(c, m)][k] for c in use], float)
        lr = np.log((x1 + 1e-3) / (x0 + 1e-3))
        bs = [np.median(rng.choice(lr, len(lr))) for _ in range(4000)]
        p = wilcoxon(lr).pvalue if wilcoxon is not None and np.any(lr != 0) else float("nan")
        print(f"  {m:6s} {k:5s}: median ratio {np.exp(np.median(lr)):.2f} (95% bootstrap {np.exp(np.percentile(bs,2.5)):.2f}-{np.exp(np.percentile(bs,97.5)):.2f}), geometric mean ratio {np.exp(lr.mean()):.2f}, lower in {(lr<0).sum()}, higher in {(lr>0).sum()}, equal {(lr==0).sum()}, Wilcoxon p {p:.2f}")
