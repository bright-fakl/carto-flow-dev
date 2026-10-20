import sys, numpy as np; sys.path.insert(0, '.')
import ad_parse, collections
def table(path, keyfn, label):
    d = ad_parse.load(path)
    g = collections.defaultdict(list)
    for k, v in d.items():
        g[keyfn(k)].append((k, v))
    print(label)
    print("| group | runs | runs with raw inversions | raw inverted triangles (total) | substep retries | retry failed | surviving iterations | surviving leaves | runs with invalid | invalid polygons (total) | time median [min-max] | mean error median |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for key in sorted(g):
        rows = [v for _, v in g[key]]
        f = lambda n: sum(r.get(n, 0) for r in rows)
        tm = [r["time"] for r in rows]
        print(f"| {key} | {len(rows)} | {sum(1 for r in rows if r.get('raw_iters', 0) > 0)} | {int(f('raw_tri'))} | {int(f('retry'))} | {int(f('retryfail'))} | {int(f('surv_iters'))} | {int(f('surv_leaves'))} | {sum(1 for r in rows if r['inv'] > 0)} | {int(f('inv'))} | {np.median(tm):.1f} [{min(tm):.1f}-{max(tm):.1f}] | {np.median([r['mean'] for r in rows]):.2f} |")
if __name__ == "__main__":
    path = sys.argv[1]; mode = sys.argv[2]
    if mode == "A":  # id A/v/q/cfg/n
        table(path, lambda k: "/".join(k.split("/")[1:3]) + " n=" + k.split("/")[4], "A")
    elif mode == "A2":
        table(path, lambda k: k.split("/")[1] + " " + k.split("/")[2] , "A2")
