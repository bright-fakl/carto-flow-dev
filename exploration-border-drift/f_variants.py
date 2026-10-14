"""Deterministic, cheap distributions F of the distance to the border (#86): cost, smoothness and accuracy.

    uv run python f_variants.py        # needs data/frames.pkl from `SKIP=1 python jitter.py`

F(s) is the share of the area of a region within the distance s x sqrt(area) of its border. Candidates:
  buffers        : exact, areas of the polygon shrunk by s x sqrt(area), 14 distance points;
  simplified     : the same on the polygon simplified with a tolerance of 0.003 x sqrt(area);
  raster         : distance transform of a raster of the polygon with a pixel of 0.005 x sqrt(area);
  final, reused  : the buffers F of the last frame for every frame (the distance in units of sqrt(area)).
The remap is the one of PR 133 with the profile from the dots.
"""
import json
import pickle
import time
import warnings
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage

import distance_remap as dr

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
EDGES = np.array([0, 0.01, 0.02, 0.04, 0.06, 0.1, 0.2, 0.4, 0.6])
SGRID = np.array([0, 0.005, 0.01, 0.02, 0.03, 0.045, 0.06, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5])


def F_buffers(poly, simplify=None):
    sc = np.sqrt(poly.area)
    if simplify:
        poly = shapely.simplify(poly, simplify * sc, preserve_topology=True)
    A = np.array([poly.buffer(-s * sc).area if s > 0 else poly.area for s in SGRID])
    return 1 - A / A[0]


def F_raster(poly, pixel=0.005):
    sc = np.sqrt(poly.area)
    p = pixel * sc
    minx, miny, maxx, maxy = poly.bounds
    nx, ny = int((maxx - minx) / p) + 3, int((maxy - miny) / p) + 3
    xs = minx - p + (np.arange(nx) + 0.5) * p
    ys = miny - p + (np.arange(ny) + 0.5) * p
    X, Y = np.meshgrid(xs, ys)
    mask = shapely.contains_xy(poly, X.ravel(), Y.ravel()).reshape(X.shape)
    dist = ndimage.distance_transform_edt(mask) * p
    d = dist[mask] / sc
    return np.searchsorted(np.sort(d), SGRID, side="right") / len(d)


def remap(geoms, P, owner, cdot, F_of):
    Q = P.copy()
    centers = 0.5 * (EDGES[:-1] + EDGES[1:])
    for r in np.unique(owner):
        sel = np.where(owner == r)[0]
        poly = geoms[r]
        sc = np.sqrt(poly.area)
        d = dr.signed_distance(poly, P[sel]) / sc
        ins = d > 0
        if ins.sum() < 3:
            continue
        chat = np.full(len(centers), np.nan)
        for b in range(len(centers)):
            m = ins & (d >= EDGES[b]) & (d < EDGES[b + 1])
            if m.any():
                chat[b] = 1.0 / np.mean(1.0 / cdot[sel][m])
        ok = np.isfinite(chat)
        if ok.sum() < 2:
            continue
        F = F_of(r, poly)
        cfun = np.interp(SGRID, centers[ok], chat[ok])
        G = np.concatenate([[0], np.cumsum(np.diff(F) * 0.5 * (cfun[1:] + cfun[:-1]))])
        G = G / G[-1] * F[-1]
        keep = np.concatenate([[True], np.diff(F) > 1e-9])
        move = ins & (d <= SGRID[-1])
        dn = np.interp(np.interp(d[move], SGRID, G), F[keep], SGRID[keep]) * sc
        u = dr.inward_direction(poly, P[sel][move])
        Q[sel[move]] = P[sel][move] + (dn - d[move] * sc)[:, None] * u
    return Q


def main():
    z = pickle.load(open(HERE / "data" / "frames.pkl", "rb"))
    owner = z["owner"]
    orig = [shapely.from_wkb(x) for x in z["orig"]]
    frames = []
    for i in range(len(z["frames"])):
        geoms = [shapely.from_wkb(x).buffer(0) for x in z["geoms"][i]]
        ratio = np.array([geoms[r].area / orig[r].area for r in range(len(orig))])
        frames.append((geoms, z["dots"][i], ratio[owner] / np.exp(z["logJ"][i])))
    last_F = {}
    for r, poly in enumerate(frames[-1][0]):
        last_F[r] = F_buffers(poly)
    first_F = {r: F_raster(shapely.buffer(poly, 0)) for r, poly in enumerate(orig)}
    variants = {
        "buffers": lambda r, poly: F_buffers(poly),
        "simplified buffers": lambda r, poly: F_buffers(poly, 0.003),
        "raster": lambda r, poly: F_raster(poly),
        "final frame, reused": lambda r, poly: last_F[r],
        "original geometry, reused": lambda r, poly: first_F[r],
    }
    out = {"frames": z["frames"], "variants": {}}
    deltas = {}
    seconds = {}
    for name, fn in variants.items():
        t = time.perf_counter()
        deltas[name] = [remap(geoms, P, owner, c, fn) - P for geoms, P, c in frames]
        seconds[name] = (time.perf_counter() - t) / len(frames)
        print(name, "seconds per frame %.2f" % seconds[name], flush=True)
    sc_final = np.array([np.sqrt(frames[-1][0][o].area) for o in owner])
    carried = np.array([f[1] for f in frames])
    ref = np.array(deltas["buffers"])
    for name, dl in deltas.items():
        D = np.array(dl)
        sec = np.linalg.norm(D[2:] - 2 * D[1:-1] + D[:-2], axis=2) / sc_final[None, :]
        inc = np.linalg.norm(D[1:] - D[:-1], axis=2)
        mot = np.maximum(np.linalg.norm(carried[1:] - carried[:-1], axis=2), 1e-12)
        active = np.linalg.norm(ref, axis=2).max(axis=0) > 1e-6 * sc_final
        diff = np.linalg.norm(D - ref, axis=2) / sc_final[None, :]
        out["variants"][name] = {"seconds_per_frame": round(seconds[name], 3),
                                 "second_difference_median_pct": round(float(100 * np.median(sec[:, active])), 3), "second_difference_p95_pct": round(float(100 * np.percentile(sec[:, active], 95)), 3),
                                 "increment_over_motion_p95": round(float(np.percentile((inc / mot)[:, active], 95)), 3),
                                 "difference_to_buffers_median_pct": round(float(100 * np.median(diff[:, active])), 3), "difference_to_buffers_p95_pct": round(float(100 * np.percentile(diff[:, active], 95)), 3)}
        print(name, out["variants"][name], flush=True)
    (HERE / "data" / "f_variants.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
