"""Velocity field of the flow against the distance to the border of a region (#86).

    NUMBA_NUM_THREADS=8 uv run python velocity_profile.py

For a field that scales a region uniformly, the divergence is constant inside the region and the normal velocity is
linear in the distance to the border (for a disk; other shapes only roughly). The saved internals of the morph (the
effective velocity field at every recompute) are sampled at uniform points of each region at the time of the
recompute. Reported, pooled over the regions and in units of sqrt(area):
  div(d) / div_interior : the divergence relative to its value deep inside the region (1 = uniform scaling)
  v_n(d) / (div_interior * sqrt(area)) : the normal velocity (positive outward) relative to the same scale.
"""
import json
import warnings
from pathlib import Path

import numpy as np
import shapely

import border_band as bb
import carto_flow.flow_cartogram as flow
import distance_remap as dr

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
EDGES = np.array([0, 0.01, 0.02, 0.04, 0.06, 0.1, 0.15, 0.2, 0.3, 0.4])
N_PTS = 3000
rng = np.random.default_rng(0)


def sample(field, grid, pts):
    """Bilinear interpolation of a grid field at points (x, y)."""
    xs, ys = grid.x_coords, grid.y_coords
    fx = np.clip((pts[:, 0] - xs[0]) / grid.dx, 0, len(xs) - 1.001)
    fy = np.clip((pts[:, 1] - ys[0]) / grid.dy, 0, len(ys) - 1.001)
    ix, iy = fx.astype(int), fy.astype(int)
    tx, ty = fx - ix, fy - iy
    return ((1 - tx) * (1 - ty) * field[iy, ix] + tx * (1 - ty) * field[iy, ix + 1] + (1 - tx) * ty * field[iy + 1, ix] + tx * ty * field[iy + 1, ix + 1])


def profiles(geoms, grid, vx, vy):
    div = np.gradient(vx, grid.dx, axis=1) + np.gradient(vy, grid.dy, axis=0)
    per_div, per_vn = [], []
    for poly in geoms:
        poly = poly.buffer(0)
        sc = np.sqrt(poly.area)
        P = dr.uniform_in(poly, N_PTS)
        pts = shapely.points(P)
        line = shapely.shortest_line(pts, poly.boundary)
        c = shapely.get_coordinates(line).reshape(-1, 2, 2)
        v = c[:, 0, :] - c[:, 1, :]
        d = np.linalg.norm(v, axis=1)
        n_out = -v / np.maximum(d, 1e-300)[:, None]
        dv = sample(div, grid, P)
        vn = sample(vx, grid, P) * n_out[:, 0] + sample(vy, grid, P) * n_out[:, 1]
        s = d / sc
        ref = np.median(dv[s > 0.15]) if (s > 0.15).sum() > 50 else np.nan
        per_div.append((s, dv, ref, sc))
        per_vn.append((s, vn, ref, sc))
    return per_div, per_vn


def binned(per, kind, thresh):
    rows = []
    refs = np.array([p[2] for p in per])
    ok = np.isfinite(refs) & (np.abs(refs) > thresh * np.nanmedian(np.abs(refs)))
    out = np.full((ok.sum(), len(EDGES) - 1), np.nan)
    for k, i in enumerate(np.where(ok)[0]):
        s, q, ref, sc = per[i]
        val = q / ref if kind == "div" else q / (ref * sc)
        for b in range(len(EDGES) - 1):
            m = (s >= EDGES[b]) & (s < EDGES[b + 1])
            if m.sum() > 5:
                out[k, b] = np.mean(val[m])
    return out


def run(grid_size, label):
    c = flow.create_flow_cartogram(
        bb.g, "Population", options=flow.MorphOptions(area_scale=1e-6, grid=grid_size, snapshot_every=1, save_internals=True, n_iter=400, show_progress=False),
    )
    snaps = {s.iteration: s for s in c.snapshots}
    res = {}
    internals = list(c.internals)
    for tag, idx in (("first", 0), ("last", len(internals) - 1)):
        it = internals[idx]
        geom_it = snaps.get(it.iteration - 1) or snaps[min(snaps)]
        grid = c.options.grid if hasattr(c.options.grid, "dx") else c.grid
        pd, pv = profiles(list(geom_it.geometry), grid, it.vx, it.vy)
        res[tag] = {"div": np.nanmedian(binned(pd, "div", 0.3), axis=0).round(3).tolist(), "vn": np.nanmedian(binned(pv, "vn", 0.3), axis=0).round(3).tolist()}
        print(label, tag, res[tag], flush=True)
    return res


if __name__ == "__main__":
    out = {"edges": EDGES.tolist()}
    for g in (128, 256, 512):
        out[f"grid {g}"] = run(g, f"grid {g}")
    (HERE / "data" / "velocity_profile.json").write_text(json.dumps(out))
