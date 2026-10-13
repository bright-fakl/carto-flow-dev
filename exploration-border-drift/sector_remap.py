"""Variants of the distance remap (#86): fewer reference points, and sectors around the centroid.

    NUMBA_NUM_THREADS=8 uv run python distance_remap.py   # once, writes data/states_morph.pkl
    uv run python sector_remap.py

Sectors: the nearest border point of a dot is assigned to one of K equal angular sectors around the centroid of the
morphed region, and the distance remap is built per (region, sector) from the tracers whose nearest border point lies
in that sector (K = 1 is the per-region remap). The reference distribution F is the distance distribution of a dense
uniform sample of the morphed region in the same sector.
"""
import json
import pickle
import warnings
from pathlib import Path

import numpy as np
import shapely

import border_band as bb
import distance_remap as dr

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(5)


def nearest_border(poly, P):
    pts = shapely.points(P)
    c = shapely.get_coordinates(shapely.shortest_line(pts, poly.boundary)).reshape(-1, 2, 2)
    q = c[:, 1, :]
    v = c[:, 0, :] - q
    d = np.linalg.norm(v, axis=1)
    inside = shapely.contains(poly, pts)
    return q, np.where(inside, d, -d), v / np.maximum(d, 1e-300)[:, None]


def sector_of(poly, q, K):
    cx, cy = poly.centroid.x, poly.centroid.y
    th = np.arctan2(q[:, 1] - cy, q[:, 0] - cx)
    return np.minimum(((th + np.pi) / (2 * np.pi) * K).astype(int), K - 1)


class SectorRemap:
    def __init__(self, geoms, tracers, owner_t, K, n_tracers=None, n_ref=20000):
        self.geoms, self.K = geoms, K
        self.table = {}
        for r, poly in enumerate(geoms):
            T = tracers[owner_t == r]
            if n_tracers:
                T = T[:n_tracers]
            q, d, _ = nearest_border(poly, T)
            sec = sector_of(poly, q, K)
            ref = dr.uniform_in(poly, n_ref)
            qr, dref, _ = nearest_border(poly, ref)
            secr = sector_of(poly, qr, K)
            for k in range(K):
                gd = np.sort(d[(sec == k) & (d >= 0)])
                fd = np.sort(dref[secr == k])
                self.table[(r, k)] = (gd, fd, len(T), len(ref))

    def apply(self, P, owner):
        Q = P.copy()
        for r in np.unique(owner):
            sel = np.where(owner == r)[0]
            poly = self.geoms[r]
            q, d, u = nearest_border(poly, P[sel])
            sec = sector_of(poly, q, self.K)
            for k in range(self.K):
                m = (sec == k) & (d > 0)
                gd, fd, nt, nr = self.table[(r, k)]
                if not m.any() or len(gd) < 5 or len(fd) < 5:
                    continue
                # share of the tracers (reference sample) in this sector scales both cdfs to the same sector mass
                uq = np.searchsorted(gd, d[m], side="right") / (len(gd) + 1)
                dn = np.interp(uq, (np.arange(len(fd)) + 0.5) / len(fd), fd)
                sel_k = sel[m]
                Q[sel_k] = P[sel_k] + (dn - d[m])[:, None] * u[m]
        return Q


if __name__ == "__main__":
    z = pickle.load(open(HERE / "data" / "states_morph.pkl", "rb"))
    L, owner_t, dot_sets = z["L"], z["owner_t"], z["dot_sets"]
    geoms = [shapely.from_wkb(x) for x in z["geoms"]]
    cuts = np.cumsum([0] + [len(P) for _, P in dot_sets])
    tracers = L[cuts[-1]:]
    results = []
    for K, n_tr in [(1, 2000), (1, 500), (1, 200), (1, 100), (1, 50), (4, 2000), (8, 2000), (16, 2000), (8, 500), (8, 200)]:
        m = SectorRemap(geoms, tracers, owner_t, K, n_tracers=n_tr)
        zs, med, p95 = [], [], []
        for k, (owner, _) in enumerate(dot_sets):
            P = L[cuts[k]:cuts[k + 1]]
            bb.owner = owner
            Q = m.apply(P, owner)
            zs.append(bb.band_z(geoms, Q)[2])
            sc = np.array([np.sqrt(geoms[o].area) for o in owner])
            s = np.linalg.norm(Q - P, axis=1) / sc
            med.append(np.median(s)); p95.append(np.percentile(s, 95))
        row = {"sectors": K, "tracers_per_region": n_tr, "z_mean": round(float(np.mean(zs)), 2), "z_sd": round(float(np.std(zs)), 2), "z_max": round(float(np.max(zs)), 2),
               "shift_median": round(float(np.mean(med)), 4), "shift_p95": round(float(np.mean(p95)), 4)}
        print(row, flush=True)
        results.append(row)
    before = []
    for k, (owner, _) in enumerate(dot_sets):
        bb.owner = owner
        before.append(bb.band_z(geoms, L[cuts[k]:cuts[k + 1]])[2])
    print("before: mean %.2f sd %.2f" % (np.mean(before), np.std(before)))
    (HERE / "data" / "sector_remap.json").write_text(json.dumps({"before_mean": float(np.mean(before)), "rows": results}))
