"""Remove the zero-width loops of a ring set: for every pair of segments of one ring that cross, drop the vertices of the shorter loop
between them and put the intersection point (computed from lexicographically ordered end points, so twins on shared boundaries get the
same point) in their place. Applied to every ring that has the crossing, so shared boundaries stay shared."""
import numpy as np, shapely
import xing


def _inter(p, q, r, s):
    # intersection of segments pq and rs (proper crossing assumed), end points ordered lexicographically for symmetry
    def order(a, b):
        return (a, b) if (a[0], a[1]) <= (b[0], b[1]) else (b, a)
    p, q = order(p, q); r, s = order(r, s)
    if (p[0], p[1], q[0], q[1]) > (r[0], r[1], s[0], s[1]):
        p, q, r, s = r, s, p, q
    d1 = q - p; d2 = s - r
    den = d1[0] * d2[1] - d1[1] * d2[0]
    t = ((r[0] - p[0]) * d2[1] - (r[1] - p[1]) * d2[0]) / den
    return p + t * d1


def fix(coords, offs, max_pass=20):
    """Returns new coords, offs and the list of removed vertex counts per pass."""
    coords = coords.copy(); offs = np.asarray(offs, dtype=np.int64).copy()
    removed_total = 0
    for it in range(max_pass):
        G = xing.Grid(coords, offs, 6.0)
        fl = G.crossing()
        if not fl.any():
            break
        first = G.first
        ring_of = np.searchsorted(offs, first, side="right") - 1
        rings = np.unique(ring_of[fl])
        new_c = []; new_offs = [0]; pos = 0
        edits = {}
        for r in rings:
            segs = first[fl & (ring_of == r)]
            pair = None
            for a in range(len(segs)):
                for b in range(a + 1, len(segs)):
                    i, j = segs[a], segs[b]
                    if xing._cross(coords, i, i + 1, j, j + 1):
                        pair = (i, j) if i < j else (j, i); break
                if pair: break
            if pair is None: continue
            i, j = pair
            lo, hi = offs[r], offs[r + 1]
            n = hi - lo - 1                      # distinct vertices of the closed ring
            inner = j - i                        # vertices i+1..j removed
            outer = n - inner
            X = _inter(coords[i], coords[i + 1], coords[j], coords[j + 1])
            ring = coords[lo:hi - 1]
            li, lj = i - lo, j - lo
            def sh(p):
                x, y = p[:, 0], p[:, 1]
                return abs(0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
            A_in = sh(np.vstack([X[None], ring[li + 1:lj + 1]]))
            A_out = sh(np.vstack([ring[:li + 1], X[None], ring[lj + 1:]]))
            if A_in <= A_out:
                keep = np.concatenate([ring[:li + 1], X[None], ring[lj + 1:]])
            else:
                keep = np.concatenate([X[None], ring[li + 1:lj + 1]])
            edits[r] = np.vstack([keep, keep[:1]])
            removed_total += (hi - lo) - len(edits[r])
        if not edits:
            break
        parts = []; no = [0]
        for r in range(len(offs) - 1):
            seg = edits[r] if r in edits else coords[offs[r]:offs[r + 1]]
            parts.append(seg); no.append(no[-1] + len(seg))
        coords = np.vstack(parts); offs = np.array(no, dtype=np.int64)
    return coords, offs, removed_total


if __name__ == "__main__":
    import sys, os
    d = os.path.dirname(os.path.abspath(__file__)) + "/out/"
    o = shapely.from_wkb(np.load(d + sys.argv[1] + "_wkb.npy", allow_pickle=True))
    gt, c, offs = shapely.to_ragged_array(o)
    print("invalid before", (~shapely.is_valid(o)).sum(), "verts", len(c))
    c2, of2, rem = fix(c, offs[0])
    o2 = shapely.from_ragged_array(gt, c2, (of2,) + tuple(offs[1:]))
    inv = np.flatnonzero(~shapely.is_valid(o))
    a0, a1 = shapely.area(o), shapely.area(o2)
    print("invalid after", (~shapely.is_valid(o2)).sum(), "verts", len(c2), "removed", rem, "max rel area change", np.max(np.abs(a1 - a0) / a0))
    print("area change of the formerly invalid:", np.abs(a1[inv] - a0[inv]) / a0[inv])
    v = shapely.is_valid(o)
    print("coverage invalid edges after (polygons):", int((~shapely.is_empty(shapely.coverage_invalid_edges(o2))).sum()))
    for i in np.flatnonzero(~shapely.is_valid(o2))[:5]: print(" still invalid", i, shapely.is_valid_reason(o2[i])[:60])
