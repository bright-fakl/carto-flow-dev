import sys, numpy as np, shapely
sys.path.insert(0, ".")
from evidence_fit import *
from isotile.curves import outline, native_edge_transforms, normalize_curves, check_outline
rng = np.random.default_rng(5)
dis = []; n = 0; nv = 0
for amp in (0.1, 0.3, 0.6, 1.0, 2.0):
    for number in tiling_types():
        for rep in range(4):
            p, curves = trial(number, amp, rng)
            t = get_type(number)
            if not check_prototile(number, p).valid: continue
            cs = normalize_curves(t, curves, None)
            pts, starts = outline(t, native_edge_transforms(t, p), cs)
            bad, msg = check_outline(pts, starts)
            poly = shapely.Polygon(pts)
            n += 1
            if (not bad) != poly.is_valid:
                dis.append((number, amp, msg, shapely.is_valid_reason(poly)))
            nv += not bad
print(n, nv, len(dis)); print(dis[:10])
