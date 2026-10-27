import time, itertools, numpy as np
exec(open("spike.py").read().split("rng = ")[0])
from collections import Counter
mx = 0; nbr = Counter(); vn = Counter(); na = Counter(); npar = Counter()
for t in tiling_types:
    ih = IH(t); tb = table(ih)
    na[ih.num_aspects] += 1; npar[ih.num_parameters] += 1
    for k, s in tb.items():
        e = [x for x in s if x[3] == 'edge']; v = [x for x in s if x[3] == 'vertex']
        nbr[len(e)] += 1; vn[len(v)] += 1
        mx = max([mx] + [max(abs(x[0]), abs(x[1])) for x in s])
print("max lattice offset", mx); print("edge neighbours per aspect", dict(nbr)); print("vertex-only", dict(sorted(vn.items())))
print("aspects per type", dict(sorted(na.items()))); print("params per type", dict(sorted(npar.items())))
# timing: table lookup vs current geometric method on a ~5000 tile patch
t = 7; ih = IH(t); tb = table(ih)
R = 35
idx = {}; n = 0
for a, b in itertools.product(range(-R, R+1), repeat=2):
    for k in range(ih.num_aspects): idx[(a, b, k)] = n; n += 1
t0 = time.perf_counter()
rows = []; cols = []
arr = np.array([(a, b, k) for (a, b, k) in idx])
for k, s in tb.items():
    sel = arr[arr[:, 2] == k]
    for da, db, k2, kind in s:
        if kind != 'edge': continue
        tgt = sel + np.array([da, db, 0]); tgt[:, 2] = k2
        # dict-free: encode
        enc = lambda A: ((A[:, 0] + R) * (2*R+1) + (A[:, 1] + R)) * ih.num_aspects + A[:, 2]
        ok = (np.abs(tgt[:, 0]) <= R) & (np.abs(tgt[:, 1]) <= R)
        rows.append(enc(sel)[ok]); cols.append(enc(tgt)[ok])
t_lat = time.perf_counter() - t0
print("tiles", n, "lattice table lookup %.4f s" % t_lat, "edges", sum(len(r) for r in rows))
from shapely.geometry import Polygon
from shapely import STRtree
polys = [Polygon(P) for (a, b, k), P in tiles(ih, R=35 if False else 20)]
t0 = time.perf_counter()
sys_path = "/home/fakl/carto-flow/src"
import sys; sys.path.insert(0, sys_path)
from carto_flow.symbol_cartogram.tiling import _compute_adjacency_matrices
_compute_adjacency_matrices(polys, tol=1e-6)
print("geometric, %d tiles: %.2f s" % (len(polys), time.perf_counter() - t0))
