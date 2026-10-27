import sys, numpy as np, shapely
from isotile import IsohedralTiling, get_type, tiling_types, check_prototile
from isotile.edges import enforce_symmetry

def rand_curve(rng, amp, m):
    x = np.sort(rng.uniform(0.05, 0.95, m))
    pts = np.column_stack([x, rng.uniform(-amp, amp, m)])
    return np.vstack([[0, 0], pts, [1, 0]])

def trial(number, amp, rng):
    t = get_type(number)
    base = IsohedralTiling(number)
    for _ in range(20):
        try:
            p = base.parameters + rng.uniform(-0.1, 0.1, t.n_params)
            IsohedralTiling(number, p); break
        except ValueError: pass
    else: p = base.parameters
    curves = {sid: rand_curve(rng, amp, rng.integers(1, 5)) for sid, s in enumerate(t.shape_types) if s != "I" and sid in set(t.edge_shape_ids.tolist())}
    return p, curves

def multiplicity(tiling, rng, n=1500):
    # region: a box around centroid of size ~ 4 tiles
    s = np.sqrt(tiling.area)
    c = tiling.centroid
    box = (c[0] - 2.5*s, c[1] - 2.5*s, c[0] + 2.5*s, c[1] + 2.5*s)
    tiles = tiling.cover((box[0]-6*s, box[1]-6*s, box[2]+6*s, box[3]+6*s)) # generous
    polys = shapely.polygons(tiles.outlines())
    pts = rng.uniform([box[0], box[1]], [box[2], box[3]], (n, 2))
    tree = shapely.STRtree(polys)
    pi, ti = tree.query(shapely.points(pts), predicate="within")
    counts = np.bincount(pi, minlength=n)
    return counts, polys

if __name__ == "__main__":
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    for amp in (0.1, 0.3, 0.6, 1.0, 2.0):
        nvalid = ninvalid = 0; bad_valid = []; bad_invalid = 0
        for number in tiling_types():
            for rep in range(3):
                p, curves = trial(number, amp, rng)
                rep_ = check_prototile(number, p, edge_curves=curves)
                if rep_.valid:
                    tiling = IsohedralTiling(number, p, edge_curves=curves)
                    counts, polys = multiplicity(tiling, rng)
                    nvalid += 1
                    if not np.all(counts == 1):
                        bad_valid.append((number, int((counts == 0).sum()), int((counts > 1).sum())))
                else:
                    ninvalid += 1
        print(f"amp {amp}: valid {nvalid} invalid {ninvalid}; valid-but-not-a-tiling {len(bad_valid)} {bad_valid[:8]}", flush=True)
