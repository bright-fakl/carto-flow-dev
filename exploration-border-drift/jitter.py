"""Frame-to-frame smoothness of the corrected dots in an animation (#86).

    NUMBA_NUM_THREADS=8 uv run python jitter.py

One morph with one seed of dots, 400 random probes per region (uniform in the original region) and the structured probes
of sections.py (along the inward normals at 24 points of the border), all with the area scaling summed in place; the
sum is kept at every iteration. Frames are the snapshots every 4 iterations. For every frame the dots are corrected with
  A : the crowding profile from the dots (PR 133), the distribution of the distance from 400 sample points,
  B : the profile from the structured probes, F from 400 sample points,
  C : the profile from the random probes, F from 400 sample points,
  E : the profile from the structured probes, F from polygon buffers (13 distance points).
Jitter: the correction vector of every dot over the frames; reported are the second difference |d(f+1) - 2 d(f) + d(f-1)|
in units of the width of the region, and the increment of the correction relative to the carried motion
|d(f+1) - d(f)| / |P(f+1) - P(f)|, over the dots that are corrected.
"""
import json
import warnings
from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import numpy as np
import shapely

import border_band as bb
import carto_flow.flow_cartogram as flow
import carto_flow.flow_cartogram.algorithm as alg
import carto_flow.proportional_cartogram as prop
import distance_remap as dr
from jacobian_path import EDGES as BIN_EDGES
from jacobian_path import proxy_remap, proxy_remap_sampled
from sections import make_probes
from velocity_profile import sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
GRID = 256
import os

SKIP = bool(os.environ.get("SKIP"))
EVERY = 4


def profile_from_probes(geoms, Pp, cp, region, arithmetic):
    out = {}
    for r in range(len(geoms)):
        m = region == r
        pts = shapely.points(Pp[m])
        sc = np.sqrt(geoms[r].area)
        d = shapely.distance(pts, geoms[r].boundary) / sc
        ins = shapely.contains(geoms[r], pts)
        chat = np.full(len(BIN_EDGES) - 1, np.nan)
        for b in range(len(chat)):
            mm = ins & (d >= BIN_EDGES[b]) & (d < BIN_EDGES[b + 1])
            if mm.sum() >= 3:
                chat[b] = cp[m][mm].mean() if arithmetic else 1.0 / np.mean(1.0 / cp[m][mm])
        out[r] = chat
    return out


def main():
    g = bb.g
    orig = list(g.geometry)
    col = "Below Poverty Level"
    d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=0)
    owner = np.array([list(g.index).index(o) for o in d["original_index"]])
    P0 = np.array([[p.x, p.y] for p in d.geometry])
    opts = flow.MorphOptions(area_scale=1e-6, grid=GRID, n_iter=400, show_progress=False, snapshot_every=EVERY)
    h = opts.get_grid(opts._calculate_bounds_from_geometries(g.geometry)).dx
    sprobes, smeta = make_probes(orig, h)
    rng = np.random.default_rng(2)
    rprobes, rregion = [], []
    for r, poly in enumerate(orig):
        pts = dr.uniform_in(poly.buffer(0), 400)
        rprobes.append(pts)
        rregion += [r] * len(pts)
    rprobes, rregion = np.vstack(rprobes), np.array(rregion)
    allP = np.vstack([P0, sprobes, rprobes])
    n = len(allP)
    n_d, n_s = len(P0), len(sprobes)
    st = {"key": None, "div": None, "grid": None, "logJ": np.zeros(n), "hist": {}, "step": 0}
    orig_fn = alg.displace_coords_numba

    def wrapped(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel=True):
        if coords.ndim == 2 and coords.shape[0] == n:
            key = float(vx.sum())
            if st["key"] != key:
                st["key"] = key
                st["div"] = np.gradient(vx, dx, axis=1) + np.gradient(vy, dy, axis=0)
                st["grid"] = SimpleNamespace(x_coords=xs, y_coords=ys, dx=dx, dy=dy)
            st["logJ"] += dt * sample(st["div"], st["grid"], coords)
            st["step"] += 1
            st["hist"][st["step"]] = st["logJ"].copy()
        return orig_fn(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel)

    alg.displace_coords_numba = wrapped
    try:
        c = flow.create_flow_cartogram(g, "Population", landmarks=gpd.GeoSeries(shapely.points(allP), crs=g.crs), options=opts)
    finally:
        alg.displace_coords_numba = orig_fn
    frames = [s for s in c.snapshots if s.iteration in st["hist"]]
    print("frames", [s.iteration for s in frames], flush=True)
    variants = {"A dots, F sampled": [], "B structured probes, F sampled": [], "C random probes, F sampled": [], "E structured probes, F from buffers": []}
    carried = []
    for s in frames:
        it = s.iteration
        geoms = [x.buffer(0) for x in s.geometry]
        ratio = np.array([geoms[r].area / orig[r].area for r in range(len(orig))])
        Pf = np.array([[p.x, p.y] for p in s.landmarks])
        lj = st["hist"][it]
        cdots = ratio[owner] / np.exp(lj[:n_d])
        sreg = smeta[:, 0].astype(int)
        cs = ratio[sreg] / np.exp(lj[n_d:n_d + n_s])
        cr = ratio[rregion] / np.exp(lj[n_d + n_s:])
        P = Pf[:n_d]
        ov_s = profile_from_probes(geoms, Pf[n_d:n_d + n_s], cs, sreg, True)
        ov_r = profile_from_probes(geoms, Pf[n_d + n_s:], cr, rregion, False)
        carried.append(P)
        if SKIP:
            print("frame", it, flush=True)
            continue
        variants["A dots, F sampled"].append(proxy_remap_sampled(geoms, P, owner, cdots) - P)
        variants["B structured probes, F sampled"].append(proxy_remap_sampled(geoms, P, owner, cdots, chat_override=ov_s) - P)
        variants["C random probes, F sampled"].append(proxy_remap_sampled(geoms, P, owner, cdots, chat_override=ov_r) - P)
        variants["E structured probes, F from buffers"].append(proxy_remap(geoms, P, owner, cdots, n_grid=13, chat_override=ov_s) - P)
        print("frame", it, flush=True)
    import pickle

    pickle.dump({"frames": [s.iteration for s in frames], "geoms": [[shapely.to_wkb(x) for x in s.geometry] for s in frames],
                 "dots": [np.array([[p.x, p.y] for p in s.landmarks])[:n_d] for s in frames], "logJ": [st["hist"][s.iteration][:n_d] for s in frames],
                 "owner": owner, "orig": [shapely.to_wkb(x) for x in orig]}, open(HERE / "data" / "frames.pkl", "wb"))
    res = {"frames": [s.iteration for s in frames], "variants": {}}
    if SKIP:
        return
    sc_final = np.array([np.sqrt(shapely.buffer(frames[-1].geometry[o], 0).area) for o in owner])
    carried = np.array(carried)
    for name, deltas in variants.items():
        D = np.array(deltas)  # (frames, dots, 2)
        sec = np.linalg.norm(D[2:] - 2 * D[1:-1] + D[:-2], axis=2) / sc_final[None, :]
        inc = np.linalg.norm(D[1:] - D[:-1], axis=2)
        mot = np.maximum(np.linalg.norm(carried[1:] - carried[:-1], axis=2), 1e-12)
        active = np.linalg.norm(D, axis=2).max(axis=0) > 1e-6 * sc_final
        res["variants"][name] = {
            "second_difference_median_pct": round(float(100 * np.median(sec[:, active])), 3), "second_difference_p95_pct": round(float(100 * np.percentile(sec[:, active], 95)), 3),
            "increment_over_motion_median": round(float(np.median((inc / mot)[:, active])), 3), "increment_over_motion_p95": round(float(np.percentile((inc / mot)[:, active], 95)), 3),
            "final_median_pct": round(float(100 * np.median(np.linalg.norm(D[-1], axis=1)[active] / sc_final[active])), 3), "active_dots": int(active.sum()),
        }
        print(name, res["variants"][name], flush=True)
    (HERE / "data" / "jitter.json").write_text(json.dumps(res))


if __name__ == "__main__":
    main()
