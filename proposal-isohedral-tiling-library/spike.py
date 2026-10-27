"""Spike: is the lattice adjacency table of a type independent of its parameters?"""
import itertools, numpy as np
from tactile import IsohedralTiling as IH, tiling_types

def tiles(ih, R=4):
    t1, t2 = ih.t1, ih.t2
    out = []
    for a, b in itertools.product(range(-R, R + 1), repeat=2):
        for k, M in enumerate(ih.aspects):
            T = np.array(M, float).reshape(2, 3)
            V = np.array([[v.x, v.y] for v in ih.vertices])
            P = V @ T[:, :2].T + T[:, 2] + a * np.array([t1.x, t1.y]) + b * np.array([t2.x, t2.y])
            out.append(((a, b, k), P))
    return out

def table(ih, tol=1e-6):
    """(aspect) -> set of (da, db, aspect', kind) with kind 'edge' or 'vertex'."""
    T = tiles(ih)
    key = {k: P for k, P in T}
    res = {}
    for k in range(ih.num_aspects):
        P = key[(0, 0, k)]
        s = set()
        for (a, b, k2), Q in T:
            if (a, b, k2) == (0, 0, k):
                continue
            d = np.linalg.norm(P[:, None] - Q[None], axis=2)
            n = int((d.min(axis=1) < tol).sum())
            if n >= 2: s.add((a, b, k2, 'edge'))
            elif n == 1: s.add((a, b, k2, 'vertex'))
        res[k] = frozenset(s)
    return res

rng = np.random.default_rng(0)
bad = []
for t in tiling_types:
    ih = IH(t)
    base = table(ih)
    ok = True
    for _ in range(4):
        ih = IH(t)
        p = list(np.array(ih.parameters) + rng.uniform(-0.15, 0.15, ih.num_parameters))
        try:
            ih.parameters = p
        except Exception:
            continue
        if table(ih) != base:
            ok = False
    n_edge = {k: sum(1 for x in v if x[3] == 'edge') for k, v in base.items()}
    nv = ih.num_vertices
    if not ok or any(n != nv for n in n_edge.values()):
        bad.append((t, ok, nv, n_edge))
print(len(tiling_types), "types; anomalies:", len(bad))
for b in bad: print(b)
