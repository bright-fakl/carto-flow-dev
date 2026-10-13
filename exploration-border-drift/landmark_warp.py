"""Reference-point warp for the dots of #86: each region is warped by a thin-plate spline through a few existing points
(boundary vertices and carried interior points) from their original to their morphed positions, and the dots, which are
uniform in the original region, are mapped with it instead of with the flow.

    NUMBA_NUM_THREADS=8 uv run python distance_remap.py   # once, writes data/states_morph.pkl
    uv run python landmark_warp.py

Writes data/landmark_warp.json: z-scores, displacement against the flow, fraction of dots inside their region, and the
pooled distance profile (observed / expected) of the original dots, the flow, the distance remap and the warp.
"""
import json
import pickle
import warnings
from pathlib import Path

import numpy as np
import shapely
from scipy.interpolate import RBFInterpolator

import border_band as bb
import distance_remap as dr

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
EDGES = np.array([0, 0.01, 0.02, 0.04, 0.06, 0.1, 0.2, 0.4, 0.6])


def boundary_pairs(orig, final, m):
    a, b = shapely.get_coordinates(orig), shapely.get_coordinates(final)
    assert a.shape == b.shape
    _, keep = np.unique(a.round(9), axis=0, return_index=True)
    keep = np.sort(keep)
    idx = keep[np.unique(np.linspace(0, len(keep) - 1, min(m, len(keep))).astype(int))]
    return a[idx], b[idx]


def warp_region(orig, final, m, k_interior, tr_o, tr_f):
    src, dst = boundary_pairs(orig, final, m)
    if k_interior:
        c = np.array([orig.centroid.x, orig.centroid.y])
        j = np.argsort(np.linalg.norm(tr_o - c, axis=1))[:k_interior]
        src, dst = np.vstack([src, tr_o[j]]), np.vstack([dst, tr_f[j]])
    scale = np.sqrt(orig.area)
    f = RBFInterpolator(src / scale, (dst - src) / scale, kernel="thin_plate_spline", smoothing=1e-9)
    return lambda X: X + f(X / scale) * scale


def pooled_profile(geoms, P, owner):
    obs = np.zeros(len(EDGES) - 1)
    exp = np.zeros(len(EDGES) - 1)
    for r in np.unique(owner):
        poly = geoms[r]
        sc = np.sqrt(poly.area)
        sel = owner == r
        d = shapely.distance(shapely.points(P[sel]), poly.boundary) / sc
        inside = shapely.contains(poly, shapely.points(P[sel]))
        obs += np.histogram(d[inside], EDGES)[0]
        A = np.array([poly.buffer(-e * sc).area if e > 0 else poly.area for e in EDGES])
        exp += sel.sum() * (A[:-1] - A[1:]) / poly.area
    return obs / exp


if __name__ == "__main__":
    z = pickle.load(open(HERE / "data" / "states_morph.pkl", "rb"))
    L, owner_t, tr_orig, dot_sets = z["L"], z["owner_t"], z["tr_orig"], z["dot_sets"]
    final = [shapely.from_wkb(x) for x in z["geoms_raw"]]
    geoms = [shapely.from_wkb(x) for x in z["geoms"]]
    orig = [x for x in bb.g.geometry]
    cuts = np.cumsum([0] + [len(P) for _, P in dot_sets])
    tracers_f = L[cuts[-1]:]
    remap = dr.Remap(geoms, tracers_f, owner_t, False)
    out = {"original_z": [], "flow_z": [], "variants": [], "profiles": {"edges": EDGES.tolist()}}
    prof = {"original": [], "flow": [], "distance remap": []}
    for k, (owner, P0) in enumerate(dot_sets):
        P = L[cuts[k]:cuts[k + 1]]
        bb.owner = owner
        out["original_z"].append(round(bb.band_z(orig, P0)[2], 2))
        out["flow_z"].append(round(bb.band_z(geoms, P)[2], 2))
        prof["original"].append(pooled_profile(orig, P0, owner))
        prof["flow"].append(pooled_profile(geoms, P, owner))
        prof["distance remap"].append(pooled_profile(geoms, remap.apply(P, owner), owner))
    variants = [(8, 0), (16, 0), (32, 0), (64, 0), (128, 0), (32, 1), (64, 1), (64, 5), (128, 5)]
    best = None
    for m, ki in variants:
        warps = {}
        for r in range(len(orig)):
            sel = owner_t == r
            warps[r] = warp_region(orig[r], final[r], m, ki, tr_orig[sel], tracers_f[sel])
        zs, inside, med, p95, tmed, tp95, profs = [], [], [], [], [], [], []
        for k, (owner, P0) in enumerate(dot_sets):
            P = L[cuts[k]:cuts[k + 1]]
            bb.owner = owner
            Q = P0.copy()
            for r in np.unique(owner):
                s = owner == r
                Q[s] = warps[r](P0[s])
            zs.append(bb.band_z(geoms, Q)[2])
            sc = np.array([np.sqrt(geoms[o].area) for o in owner])
            inside.append(float(np.mean([shapely.contains(geoms[o], shapely.Point(q)) for o, q in zip(owner, Q)])))
            s_ = np.linalg.norm(Q - P, axis=1) / sc
            med.append(np.median(s_)); p95.append(np.percentile(s_, 95))
            profs.append(pooled_profile(geoms, Q, owner))
        # fidelity to the flow: the warp of the tracers against their carried positions
        diffs = []
        for r in range(len(orig)):
            sel = owner_t == r
            diffs.append(np.linalg.norm(warps[r](tr_orig[sel]) - tracers_f[sel], axis=1) / np.sqrt(geoms[r].area))
        diffs = np.concatenate(diffs)
        row = {"boundary_vertices": m, "interior_points": ki, "z_mean": round(float(np.mean(zs)), 2), "z_sd": round(float(np.std(zs)), 2),
               "inside": round(float(np.mean(inside)), 4), "shift_vs_flow_median": round(float(np.mean(med)), 4), "shift_vs_flow_p95": round(float(np.mean(p95)), 4),
               "tracer_diff_median": round(float(np.median(diffs)), 4), "tracer_diff_p95": round(float(np.percentile(diffs, 95)), 4)}
        print(row, flush=True)
        out["variants"].append(row)
        if (m, ki) == (16, 0):
            prof["warp (16 boundary vertices)"] = profs
        if (m, ki) == (64, 1):
            prof["warp (64 boundary vertices, 1 interior point)"] = profs
    out["profiles"]["rows"] = {k: np.mean(v, axis=0).round(3).tolist() for k, v in prof.items()}
    (HERE / "data" / "landmark_warp.json").write_text(json.dumps(out))
    print("original z", out["original_z"], "mean", np.mean(out["original_z"]))
    print("flow z", out["flow_z"], "mean", np.mean(out["flow_z"]))
    print({k: v for k, v in out["profiles"]["rows"].items()})
