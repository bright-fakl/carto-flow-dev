import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness
g, v = harness.load("county")
geo = np.array(g.geometry.values, dtype=object); cen = shapely.centroid(geo); cx = shapely.get_x(cen); cy = shapely.get_y(cen)
d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
tree = shapely.STRtree(geo)
cfgs = ["dt0.16", "dt0.18", "dt0.20", "dt0.22", "dt0.24", "msl800", "msl1100"]
res = {m: {"near": [], "far": []} for m in ("base", "vw1", "vw10")}
for c in cfgs:
    z = {m: np.load(d + f"p4_{c}_{m}_county.npz") for m in res}
    I = np.all([z[m]["valid"] for m in z], axis=0)
    # hard counties: invalid in base
    hard = np.flatnonzero(~z["base"]["valid"])
    dist = np.array([np.min(np.hypot(cx[hard] - cx[i], cy[hard] - cy[i])) if len(hard) else 1e9 for i in range(len(geo))])
    # neighbors (touching) of hard counties in the original geometry
    near = np.zeros(len(geo), bool)
    for h in hard:
        for j in tree.query(geo[h], predicate="intersects"): near[j] = True
    for m in res:
        a = z[m]["area"]; T = v / v[I].sum() * a[I].sum(); e = np.abs(a - T) / T * 100
        res[m]["near"].append(np.median(e[I & near])); res[m]["far"].append(np.median(e[I & ~near]))
        res[m].setdefault("p95n", []).append(np.percentile(e[I & near], 95)); res[m].setdefault("p95f", []).append(np.percentile(e[I & ~near], 95))
for m in res:
    print(m, "median error of touching-a-baseline-invalid counties (median over configs): %.4f, others: %.4f | p95 touching %.3f others %.3f" % (np.median(res[m]["near"]), np.median(res[m]["far"]), np.median(res[m]["p95n"]), np.median(res[m]["p95f"])))
