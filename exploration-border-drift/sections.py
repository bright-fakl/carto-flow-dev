"""Do the border sections of a region differ, and does a per-section correction help? (#86)

    NUMBA_NUM_THREADS=8 uv run python sections.py

One morph with 8 seeds of dots and, per region, probe points along the inward normals at K points spread along the border
(the "middle way": a one-dimensional model along the normals, here with real carried points). All landmarks accumulate
log J in place. Reported: the crowding c = (A_final / A_original) / J of the probes by section for Florida; the border
band z-score of the dots after (a) the pooled per-region remap from the dots (PR 133), (b) a per-section remap from
the normal probes, in units of the grid cell.
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
from velocity_profile import sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
K = 24
GRID = 256


def make_probes(orig, h):
    pts, meta = [], []
    for r, poly in enumerate(orig):
        part = max(poly.geoms, key=lambda x: x.area) if hasattr(poly, "geoms") else poly
        ring = shapely.LinearRing(part.exterior.coords)
        L, sc = ring.length, np.sqrt(poly.area)
        dlist = np.unique(np.concatenate([h * np.array([0.0, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12]), sc * np.array([0.1, 0.15, 0.2, 0.3])]))
        for k in range(K):
            s = (k + 0.5) / K * L
            q = np.array(ring.interpolate(s).coords[0])
            a, b = np.array(ring.interpolate((s - 0.002 * L) % L).coords[0]), np.array(ring.interpolate((s + 0.002 * L) % L).coords[0])
            t = (b - a) / max(np.linalg.norm(b - a), 1e-300)
            n1 = np.array([-t[1], t[0]])
            inward = n1 if part.contains(shapely.Point(q + n1 * 1e-3 * sc)) else -n1
            for d0 in dlist:
                p = q + inward * d0
                if d0 == 0 or part.contains(shapely.Point(p)):
                    pts.append(p)
                    meta.append((r, k, d0))
    return np.array(pts), np.array(meta)


def main():
    g = bb.g
    orig = list(g.geometry)
    col = "Below Poverty Level"
    sets = []
    for seed in range(8):
        d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
        sets.append((np.array([list(g.index).index(o) for o in d["original_index"]]), np.array([[p.x, p.y] for p in d.geometry])))
    opts = flow.MorphOptions(area_scale=1e-6, grid=GRID, n_iter=400, show_progress=False)
    h = opts.get_grid(opts._calculate_bounds_from_geometries(g.geometry)).dx
    probes, meta = make_probes(orig, h)
    allP = np.vstack([P for _, P in sets] + [probes])
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
        c = flow.create_flow_cartogram(g, "Population", landmarks=gpd.GeoSeries(shapely.points(allP), crs=g.crs), options=opts)
    finally:
        alg.displace_coords_numba = orig_fn
    fin = c.snapshots[-1]
    Pf = np.array([[p.x, p.y] for p in fin.landmarks])
    geoms = [x.buffer(0) for x in fin.geometry]
    ratio = np.array([geoms[r].area / orig[r].area for r in range(len(orig))])
    cuts = np.cumsum([0] + [len(P) for _, P in sets])
    n_dots = cuts[-1]
    cprobe = ratio[meta[:, 0].astype(int)] / np.exp(st["logJ"][n_dots:])
    Pp = Pf[n_dots:]
    dprobe = np.zeros(len(Pp))
    for r in range(len(orig)):
        m = meta[:, 0] == r
        pts = shapely.points(Pp[m])
        dd = shapely.distance(pts, geoms[r].boundary)
        dprobe[m] = np.where(shapely.contains(geoms[r], pts), dd, -dd)
    # profile per (region, section): sorted by the final distance
    prof = {}
    for r in range(len(orig)):
        for k in range(K):
            m = (meta[:, 0] == r) & (meta[:, 1] == k)
            o = np.argsort(dprobe[m])
            d_, c_ = dprobe[m][o], cprobe[m][o]
            ok = d_ >= 0
            if ok.sum() >= 4:
                prof[(r, k)] = (d_[ok], c_[ok], Pp[m][meta[m][:, 2] == 0][:1])
    names = list(g["State Name"])
    fl = names.index("Florida")
    tree = shapely.STRtree(np.array(geoms, dtype=object))
    rows = []
    for k in range(K):
        if (fl, k) not in prof:
            continue
        d_, c_, bp = prof[(fl, k)]
        sc = np.sqrt(geoms[fl].area)
        q = bp[0]
        # neighbour across the border: the polygon containing a point just outside, found by stepping away from the first interior probe
        inside = Pp[(meta[:, 0] == fl) & (meta[:, 1] == k) & (meta[:, 2] > 0)]
        inside = inside[np.argmin(np.linalg.norm(inside - q, axis=1))]
        out = q + (q - inside) / max(np.linalg.norm(q - inside), 1e-300) * 1.5 * h
        hit = [i for i in tree.query(shapely.Point(out), predicate="intersects") if i != fl]
        nb = names[hit[0]] if hit else "outside"
        rows.append({"section": k, "neighbor": nb, "c_at_1_cell": round(float(np.interp(1 * h, d_, c_)), 2), "c_at_3_cells": round(float(np.interp(3 * h, d_, c_)), 2), "c_at_0.2": round(float(np.interp(0.2 * sc, d_, c_)), 2)})
    print("Florida by section:")
    for r_ in rows:
        print(r_)
    # region-level profile from the normal probes: mean crowding of the probes in each bin of the final distance
    override = {}
    for r in range(len(orig)):
        m = (meta[:, 0] == r) & (dprobe > 0)
        sc = np.sqrt(geoms[r].area)
        s_ = dprobe[m] / sc
        cc = cprobe[m]
        chat = np.full(len(BIN_EDGES) - 1, np.nan)
        for b in range(len(chat)):
            mm = (s_ >= BIN_EDGES[b]) & (s_ < BIN_EDGES[b + 1])
            if mm.sum() >= 3:
                chat[b] = cc[mm].mean()
        override[r] = chat
    # border sections by the kind of neighbour across them: another state (1) or the outside (0)
    typ = {}
    for r in range(len(orig)):
        for k in range(K):
            if (r, k) not in prof:
                continue
            q = prof[(r, k)][2][0]
            ins = Pp[(meta[:, 0] == r) & (meta[:, 1] == k) & (meta[:, 2] > 0)]
            if len(ins) == 0:
                continue
            ins = ins[np.argmin(np.linalg.norm(ins - q, axis=1))]
            outp = q + (q - ins) / max(np.linalg.norm(q - ins), 1e-300) * 1.5 * h
            hit = [i for i in tree.query(shapely.Point(outp), predicate="intersects") if i != r]
            typ[(r, k)] = 1 if hit else 0
    chat_t = {}
    for r in range(len(orig)):
        sc = np.sqrt(geoms[r].area)
        for tt in (0, 1):
            m = (meta[:, 0] == r) & (dprobe > 0) & np.array([typ.get((int(a), int(b)), -1) == tt for a, b in meta[:, :2]])
            s_ = dprobe[m] / sc
            cc = cprobe[m]
            row_ = np.full(len(BIN_EDGES) - 1, np.nan)
            for b in range(len(row_)):
                mm = (s_ >= BIN_EDGES[b]) & (s_ < BIN_EDGES[b + 1])
                if mm.sum() >= 3:
                    row_[b] = cc[mm].mean()
            chat_t[(r, tt)] = row_
    rng = np.random.default_rng(1)
    nb = len(BIN_EDGES) - 1
    obs = np.zeros((2, nb)); exp_ = np.zeros((2, nb)); pt = np.zeros((2, nb)); pp = np.zeros((2, nb)); wsum = np.zeros((2, nb))
    for r in range(len(orig)):
        keys = [k for (rr, k) in typ if rr == r]
        if not keys:
            continue
        bpts = np.array([prof[(r, k)][2][0] for k in keys])
        ktyp = np.array([typ[(r, k)] for k in keys])
        sc = np.sqrt(geoms[r].area)

        def classify(P_):
            pts_ = shapely.points(P_)
            line = shapely.shortest_line(pts_, geoms[r].boundary)
            xy = shapely.get_coordinates(line).reshape(-1, 2, 2)
            dd = np.linalg.norm(xy[:, 0, :] - xy[:, 1, :], axis=1) / sc
            kk = np.argmin(np.linalg.norm(xy[:, 1, :][:, None, :] - bpts[None], axis=2), axis=1)
            return dd, ktyp[kk], shapely.contains(geoms[r], pts_)

        ref = dr.uniform_in(geoms[r], 1500)
        dref, tref, _ = classify(ref)
        n_r = sum((owner == r).sum() for owner, _ in sets)
        dots = np.vstack([Pf[cuts[i]:cuts[i + 1]][sets[i][0] == r] for i in range(len(sets))])
        if len(dots) == 0:
            continue
        dd, td, ins = classify(dots)
        for tt in (0, 1):
            ho = np.histogram(dd[ins & (td == tt)], BIN_EDGES)[0]
            he = np.histogram(dref[tref == tt], BIN_EDGES)[0] / len(ref) * len(dots)
            obs[tt] += ho
            exp_[tt] += he
            for b in range(nb):
                ct = chat_t[(r, tt)][b]
                ca = override[r][b]
                if np.isfinite(ct) and np.isfinite(ca):
                    pt[tt, b] += he[b] * ct
                    pp[tt, b] += he[b] * ca
                    wsum[tt, b] += he[b]
    print("dot density by kind of border section: observed / expected, predicted by section kind, predicted pooled")
    het = {}
    for tt, name in ((1, "border with another state"), (0, "border with the outside")):
        o = obs[tt] / np.maximum(exp_[tt], 1e-9)
        a = pt[tt] / np.maximum(wsum[tt], 1e-9)
        c_ = pp[tt] / np.maximum(wsum[tt], 1e-9)
        het[name] = {"observed": o.round(2).tolist(), "predicted_by_kind": a.round(2).tolist(), "predicted_pooled": c_.round(2).tolist(), "expected_dots": exp_[tt].round(1).tolist()}
        print(name, het[name])
    # remaps
    out_rows = []
    sect_remap = lambda P, owner, cdot: section_remap(geoms, P, owner, prof, h, K, Pf[n_dots:], meta)
    for k_, (owner, P0) in enumerate(sets):
        sl = slice(cuts[k_], cuts[k_ + 1])
        P = Pf[sl]
        bb.owner = owner
        cdot = ratio[owner] / np.exp(st["logJ"][sl])
        z0 = bb.band_z(geoms, P)[2]
        Qa = proxy_remap_sampled(geoms, P, owner, cdot, n_ref=400)
        Qb = section_remap(geoms, P, owner, prof, h)
        Qd = proxy_remap_sampled(geoms, P, owner, cdot, n_ref=400, chat_override=override)
        fl_sel = owner == fl
        zf = lambda Q: round(float(bb_band_z_region(geoms, Q, owner, fl)), 2)
        out_rows.append({"seed": k_, "before": round(z0, 2), "pooled_from_dots": round(bb.band_z(geoms, Qa)[2], 2), "sections_from_probes": round(bb.band_z(geoms, Qb)[2], 2), "pooled_from_probes": round(bb.band_z(geoms, Qd)[2], 2)})
        print(out_rows[-1], flush=True)
    for key in ("before", "pooled_from_dots", "sections_from_probes", "pooled_from_probes"):
        print(key, round(float(np.mean([r[key] for r in out_rows])), 2))
    (HERE / "data" / "sections.json").write_text(json.dumps({"florida": rows, "seeds": out_rows, "cell": float(h), "kinds": het}))


def section_remap(geoms, P, owner, prof, h):
    """Per-section remap in the strip along the border: d' = w C(d) / C(w), C the integral of the crowding over the distance."""
    Q = P.copy()
    for r in np.unique(owner):
        sel = np.where(owner == r)[0]
        poly = geoms[r]
        pts = shapely.points(P[sel])
        inside = shapely.contains(poly, pts)
        if not inside.any():
            continue
        line = shapely.shortest_line(pts[inside], poly.boundary)
        xy = shapely.get_coordinates(line).reshape(-1, 2, 2)
        v = xy[:, 0, :] - xy[:, 1, :]
        d = np.linalg.norm(v, axis=1)
        u = v / np.maximum(d, 1e-300)[:, None]
        # nearest tracked border point of the region decides the section
        keys = [k for (rr, k) in prof if rr == r]
        if not keys:
            continue
        bpts = np.array([prof[(r, k)][2][0] for k in keys])
        sec = np.array(keys)[np.argmin(np.linalg.norm(xy[:, 1, :][:, None, :] - bpts[None], axis=2), axis=1)]
        idx = sel[inside]
        for k in np.unique(sec):
            m = sec == k
            d_, c_, _ = prof[(r, k)]
            w = min(d_[-1], 0.3 * np.sqrt(poly.area))
            sg = np.linspace(0, w, 40)
            cf = np.interp(sg, d_, c_)
            C = np.concatenate([[0], np.cumsum(0.5 * (cf[1:] + cf[:-1]) * np.diff(sg))])
            band = m & (d < w)
            if not band.any():
                continue
            dn = np.interp(d[band], sg, C) / C[-1] * w
            Q[idx[band]] = P[idx[band]] + (dn - d[band])[:, None] * u[band]
    return Q


def bb_band_z_region(geoms, Q, owner, r, frac=0.06):
    sel = owner == r
    poly = geoms[r].buffer(0)
    inner = poly.buffer(-frac * np.sqrt(poly.area))
    p = 1 - inner.area / poly.area
    n = sel.sum()
    obs = (~shapely.contains(inner, shapely.points(Q[sel]))).sum()
    return (obs - n * p) / np.sqrt(max(n * p * (1 - p), 1e-12))


if __name__ == "__main__":
    main()
