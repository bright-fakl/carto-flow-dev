"""Post-morph correction of co-advected dots (#86): match the advected positions of each region to fresh uniform points
in the morphed region (minimum total squared distance), and report how far the dots have to move.

    NUMBA_NUM_THREADS=8 uv run python ot_correction.py
"""
import warnings

import numpy as np
import shapely
from scipy.optimize import linear_sum_assignment

import border_band as bb
import carto_flow.flow_cartogram as flow

warnings.filterwarnings("ignore")
rng = np.random.default_rng(1)


def uniform_points(poly, n):
    out = []
    minx, miny, maxx, maxy = poly.bounds
    while len(out) < n:
        c = np.column_stack([rng.uniform(minx, maxx, 4 * n), rng.uniform(miny, maxy, 4 * n)])
        out.extend(c[shapely.contains_xy(poly, c[:, 0], c[:, 1])].tolist())
    return np.array(out[:n])


def correct(geoms, P, owner):
    Q = P.copy()
    shift = np.zeros(len(P))
    for r in np.unique(owner):
        sel = np.where(owner == r)[0]
        target = uniform_points(geoms[r].buffer(0), len(sel))
        cost = ((P[sel][:, None, :] - target[None, :, :]) ** 2).sum(-1)
        i, j = linear_sum_assignment(cost)
        Q[sel[i]] = target[j]
        shift[sel[i]] = np.sqrt(cost[i, j]) / np.sqrt(geoms[r].area)
    return Q, shift


opts = flow.MorphOptions(area_scale=1e-6, snapshot_every=1, n_iter=400, show_progress=False)
cart = flow.create_flow_cartogram(bb.g, "Population", landmarks=bb.landmarks, options=opts)
fin = cart.snapshots[-1]
P = np.array([[p.x, p.y] for p in fin.landmarks])
geoms = list(fin.geometry)
Q, shift = correct(geoms, P, bb.owner)
# displacement of the dots by the morph itself, for scale
P0 = np.array([[p.x, p.y] for p in bb.landmarks])
morph_move = np.linalg.norm(P - P0, axis=1) / np.sqrt(np.array([geoms[o].area for o in bb.owner]))
print("states, defaults")
print("  border band z before / after:", round(bb.band_z(geoms, P)[2], 2), "/", round(bb.band_z(geoms, Q)[2], 2))
print("  correction / sqrt(area): median %.3f, 95th pct %.3f, max %.3f" % (np.median(shift), np.percentile(shift, 95), shift.max()))
print("  morph displacement / sqrt(area): median %.3f, 95th pct %.3f" % (np.median(morph_move), np.percentile(morph_move, 95)))
