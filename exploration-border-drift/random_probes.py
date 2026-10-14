"""How many random probe points per region does the crowding profile need? (#86)

    NUMBA_NUM_THREADS=8 uv run python random_probes.py

One morph with 8 seeds of dots and 400 random probes per region (uniform in the original region), the area scaling summed
in place. The dots are corrected with the profile from the first n probes of every region (harmonic mean of the crowding
per bin of the distance), n = 12 ... 400, and from the dots themselves; z-score of the border band.
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
from jacobian_path import proxy_remap_sampled
from sections import make_probes
from velocity_profile import sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
NS = (25, 100, 400)


def main():
    g = bb.g
    orig = list(g.geometry)
    col = "Below Poverty Level"
    sets = []
    for seed in range(8):
        d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
        sets.append((np.array([list(g.index).index(o) for o in d["original_index"]]), np.array([[p.x, p.y] for p in d.geometry])))
    rprobes, rreg = [], []
    for r, poly in enumerate(orig):
        pts = dr.uniform_in(poly.buffer(0), max(NS))
        rprobes.append(pts)
        rreg += [r] * len(pts)
    rprobes, rreg = np.vstack(rprobes), np.array(rreg)
    opts0 = flow.MorphOptions(area_scale=1e-6, grid=256)
    h = opts0.get_grid(opts0._calculate_bounds_from_geometries(g.geometry)).dx
    sprobes, smeta = make_probes(orig, h)
    sreg = smeta[:, 0].astype(int)
    allP = np.vstack([P for _, P in sets] + [rprobes, sprobes])
    n = len(allP)
    st = {"key": None, "div": None, "grid": None, "logJ": np.zeros(n)}
    orig_fn = alg.displace_coords_numba

    def wrapped(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel=True):
        if coords.ndim == 2 and coords.shape[0] == n:
            key = float(vx.sum())
            if st["key"] != key:
                st["key"] = key
                st["div"] = np.gradient(vx, dx, axis=1) + np.gradient(vy, dy, axis=0)
                st["grid"] = SimpleNamespace(x_coords=xs, y_coords=ys, dx=dx, dy=dy)
            st["logJ"] += dt * sample(st["div"], st["grid"], coords)
        return orig_fn(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel)

    alg.displace_coords_numba = wrapped
    try:
        c = flow.create_flow_cartogram(g, "Population", landmarks=gpd.GeoSeries(shapely.points(allP), crs=g.crs), options=flow.MorphOptions(area_scale=1e-6, n_iter=400, show_progress=False))
    finally:
        alg.displace_coords_numba = orig_fn
    fin = c.snapshots[-1]
    Pf = np.array([[p.x, p.y] for p in fin.landmarks])
    geoms = [x.buffer(0) for x in fin.geometry]
    ratio = np.array([geoms[r].area / orig[r].area for r in range(len(orig))])
    cuts = np.cumsum([0] + [len(P) for _, P in sets])
    n_dots = cuts[-1]
    n_r = len(rprobes)
    cp = ratio[rreg] / np.exp(st["logJ"][n_dots:n_dots + n_r])
    cs = ratio[sreg] / np.exp(st["logJ"][n_dots + n_r:])
    Pp = Pf[n_dots:n_dots + n_r]
    Ps = Pf[n_dots + n_r:]
    dprobe = np.zeros(len(Pp))
    inside = np.zeros(len(Pp), bool)
    for r in range(len(orig)):
        m = rreg == r
        pts = shapely.points(Pp[m])
        dprobe[m] = shapely.distance(pts, geoms[r].boundary) / np.sqrt(geoms[r].area)
        inside[m] = shapely.contains(geoms[r], pts)
    dsp = np.zeros(len(Ps))
    insp = np.zeros(len(Ps), bool)
    for r in range(len(orig)):
        m = sreg == r
        pts = shapely.points(Ps[m])
        dsp[m] = shapely.distance(pts, geoms[r].boundary) / np.sqrt(geoms[r].area)
        insp[m] = shapely.contains(geoms[r], pts)

    def pooled_profile(Qs):
        obs = np.zeros(len(BIN_EDGES) - 1)
        exp_ = np.zeros(len(BIN_EDGES) - 1)
        for k, (owner, _) in enumerate(sets):
            Q = Qs[k]
            for r in np.unique(owner):
                poly = geoms[r]
                sc = np.sqrt(poly.area)
                sel = owner == r
                pts = shapely.points(Q[sel])
                dd = shapely.distance(pts, poly.boundary) / sc
                obs += np.histogram(dd[shapely.contains(poly, pts)], BIN_EDGES)[0]
                A = np.array([poly.buffer(-e * sc).area if e > 0 else poly.area for e in BIN_EDGES]) if k == 0 and r not in cacheA else cacheA[r]
                cacheA[r] = A
                exp_ += sel.sum() * (A[:-1] - A[1:]) / poly.area
        return obs / exp_

    cacheA = {}
    res = {"n": list(NS), "z": {}, "profile": {}}
    rank = np.concatenate([np.arange((rreg == r).sum()) for r in range(len(orig))])  # position of the probe within its region
    for nn in ("none", "dots") + NS + ("structured",):
        over = None
        if nn == "structured":
            over = {}
            for r in range(len(orig)):
                m = (sreg == r) & insp
                chat = np.full(len(BIN_EDGES) - 1, np.nan)
                for b in range(len(chat)):
                    mm = m & (dsp >= BIN_EDGES[b]) & (dsp < BIN_EDGES[b + 1])
                    if mm.sum() >= 3:
                        chat[b] = cs[mm].mean()
                over[r] = chat
        elif nn not in ("dots", "none"):
            over = {}
            for r in range(len(orig)):
                m = (rreg == r) & (rank < nn) & inside
                chat = np.full(len(BIN_EDGES) - 1, np.nan)
                for b in range(len(chat)):
                    mm = m & (dprobe >= BIN_EDGES[b]) & (dprobe < BIN_EDGES[b + 1])
                    if mm.sum() >= 1:
                        chat[b] = 1.0 / np.mean(1.0 / cp[mm])
                over[r] = chat
        zs, Qs = [], []
        for k, (owner, _) in enumerate(sets):
            sl = slice(cuts[k], cuts[k + 1])
            P = Pf[sl]
            bb.owner = owner
            cdot = ratio[owner] / np.exp(st["logJ"][sl])
            Q = P if nn == "none" else proxy_remap_sampled(geoms, P, owner, cdot, n_ref=1000, chat_override=over)
            Qs.append(Q)
            zs.append(bb.band_z(geoms, Q)[2])
        res["z"][str(nn)] = {"mean": round(float(np.mean(zs)), 2), "sd": round(float(np.std(zs)), 2)}
        res["profile"][str(nn)] = pooled_profile(Qs).round(3).tolist()
        print(nn, res["z"][str(nn)], res["profile"][str(nn)], flush=True)
    print("done")
    (HERE / "data" / "random_probes.json").write_text(json.dumps(res))


if __name__ == "__main__":
    main()
