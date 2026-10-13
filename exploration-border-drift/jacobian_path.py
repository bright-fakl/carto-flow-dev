"""Area scaling of each dot from the velocity field along its own path (#86).

    NUMBA_NUM_THREADS=8 uv run python jacobian_path.py

The saved velocity fields (save_internals) and the positions of the carried dots at every iteration give, for each
dot, log J = sum over the iterations of a_t * div v(x_t), where a_t is the step of the iteration (fitted from the
displacements of all dots, since the step is not stored) and J the area scaling of the flow along the path. A dot
density relative to the uniform one at the final position is then exp(-log J) * A_final / A_original.
"""
import json
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely

import border_band as bb
import carto_flow.flow_cartogram as flow
import carto_flow.proportional_cartogram as prop
from velocity_profile import sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
EDGES = np.array([0, 0.01, 0.02, 0.04, 0.06, 0.1, 0.2, 0.4, 0.6])


def coords(landmarks):
    return shapely.get_coordinates(np.asarray(landmarks, dtype=object))


def run(grid_size=256, n_seeds=8):
    g = bb.g
    col = "Below Poverty Level"
    sets = []
    for seed in range(n_seeds):
        d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
        sets.append((np.array([list(g.index).index(o) for o in d["original_index"]]), np.array([[p.x, p.y] for p in d.geometry])))
    allP = np.vstack([P for _, P in sets])
    c = flow.create_flow_cartogram(
        g, "Population", landmarks=gpd.GeoSeries(shapely.points(allP), crs=g.crs),
        options=flow.MorphOptions(area_scale=1e-6, grid=grid_size, snapshot_every=1, save_internals=True, n_iter=400, show_progress=False),
    )
    grid = c.options.grid if hasattr(c.options.grid, "dx") else c.grid
    snaps = {s.iteration: s for s in c.snapshots}
    its = [0] + sorted(snaps)
    X = {i: coords(snaps[i].landmarks) for i in sorted(snaps)}
    X[0] = allP
    internals = sorted(list(c.internals), key=lambda s: s.iteration)
    fields = {s.iteration - 1: s for s in internals}  # the field computed at the start of step s.iteration - 1
    starts = sorted(fields)
    logJ = np.zeros(len(allP))
    resid = []
    cur = None
    for t in its[:-1]:
        if t in fields:
            cur = fields[t]
        div = np.gradient(cur.vx, grid.dx, axis=1) + np.gradient(cur.vy, grid.dy, axis=0)
        x0, x1 = X[t], X[t + 1] if (t + 1) in X else None
        if x1 is None:
            continue
        v = np.column_stack([sample(cur.vx, grid, x0), sample(cur.vy, grid, x0)])
        dx = x1 - x0
        a = float((dx * v).sum() / max((v * v).sum(), 1e-300))
        resid.append(float(np.linalg.norm(dx - a * v) / max(np.linalg.norm(dx), 1e-300)))
        logJ += a * sample(div, grid, x0)
    geoms = [x.buffer(0) for x in c.snapshots[-1].geometry]
    orig = list(g.geometry)
    ratio = np.array([geoms[r].area / orig[r].area for r in range(len(orig))])
    cuts = np.cumsum([0] + [len(P) for _, P in sets])
    Pf = X[its[-1]]
    out = {"fit_residual_median": float(np.median(resid)), "fit_residual_p95": float(np.percentile(resid, 95)), "steps": len(resid), "edges": EDGES.tolist()}
    cc_all = np.exp(-logJ) * ratio[np.concatenate([o for o, _ in sets])]
    out["mean_c"] = float(cc_all.mean())
    return out, (sets, Pf, geoms, logJ, ratio, cuts)


def proxy_remap(geoms, P, owner, cdot, edges=EDGES, n_grid=201):
    """Remap the distance to the border so that the dot density follows from the area scaling of the flow along the paths
    (the area-average of the density ratio in a bin is the harmonic mean of c over the dots in it)."""
    import distance_remap as dr

    Q = P.copy()
    centers = 0.5 * (edges[:-1] + edges[1:])
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
            m = ins & (d >= edges[b]) & (d < edges[b + 1])
            if m.sum():
                chat[b] = 1.0 / np.mean(1.0 / cdot[sel][m])
        ok = np.isfinite(chat)
        if ok.sum() < 2:
            continue
        sgrid = np.linspace(0, 0.5, n_grid)
        cfun = np.interp(sgrid, centers[ok], chat[ok])
        A = np.array([poly.buffer(-s_ * sc).area if s_ > 0 else poly.area for s_ in sgrid])
        F = 1 - A / poly.area
        dens = np.diff(F) * 0.5 * (cfun[1:] + cfun[:-1])
        G = np.concatenate([[0], np.cumsum(dens)])
        G = G / G[-1] * F[-1]
        dn = np.interp(np.interp(d[ins], sgrid, G), F, sgrid) * sc
        u = dr.inward_direction(poly, P[sel][ins])
        Q[sel[ins]] = P[sel][ins] + (dn - d[ins] * sc)[:, None] * u
    return Q


def proxy_remap_fast(geoms, P, owner, cdot, w=0.15, edges=(0, 0.01, 0.02, 0.04, 0.06, 0.1, 0.15)):
    """The same remap to first order in the distance: the area at distance d from the border is A - perimeter * d, so only the
    band d < w x sqrt(area) matters and no polygon has to be buffered. d' = w C(d) / C(w) with C the integral of the
    density ratio over the distance."""
    import distance_remap as dr

    edges = np.asarray(edges, dtype=float)
    centers = 0.5 * (edges[:-1] + edges[1:])
    sgrid = np.linspace(0, w, 31)
    Q = P.copy()
    for r in np.unique(owner):
        sel = np.where(owner == r)[0]
        poly = geoms[r]
        sc = np.sqrt(poly.area)
        d = dr.signed_distance(poly, P[sel]) / sc
        ins = d > 0
        chat = np.full(len(centers), np.nan)
        for b in range(len(centers)):
            m = ins & (d >= edges[b]) & (d < edges[b + 1])
            if m.any():
                chat[b] = 1.0 / np.mean(1.0 / cdot[sel][m])
        ok = np.isfinite(chat)
        band = ins & (d < w)
        if ok.sum() < 2 or not band.any():
            continue
        cfun = np.interp(sgrid, centers[ok], chat[ok])
        C = np.concatenate([[0], np.cumsum(0.5 * (cfun[1:] + cfun[:-1]) * np.diff(sgrid))])
        dn = np.interp(d[band], sgrid, C) / C[-1] * w
        u = dr.inward_direction(poly, P[sel][band])
        Q[sel[band]] = P[sel][band] + ((dn - d[band]) * sc)[:, None] * u
    return Q


def proxy_remap_sampled(geoms, P, owner, cdot, n_ref=400, edges=EDGES, seed=0):
    """The same remap, with the distribution F of the distance to the border of a uniform sample of the region taken from
    n_ref sample points instead of from polygon buffers."""
    import distance_remap as dr

    rng = np.random.default_rng(seed)
    centers = 0.5 * (edges[:-1] + edges[1:])
    Q = P.copy()
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
            m = ins & (d >= edges[b]) & (d < edges[b + 1])
            if m.any():
                chat[b] = 1.0 / np.mean(1.0 / cdot[sel][m])
        ok = np.isfinite(chat)
        if ok.sum() < 2:
            continue
        ref = np.sort(shapely.distance(shapely.points(dr.uniform_in(poly, n_ref)), poly.boundary) / sc)
        sgrid = np.linspace(0, ref[int(0.98 * n_ref)], 60)
        F = np.searchsorted(ref, sgrid, side="right") / n_ref
        cfun = np.interp(sgrid, centers[ok], chat[ok])
        dens = np.diff(F) * 0.5 * (cfun[1:] + cfun[:-1])
        G = np.concatenate([[0], np.cumsum(dens)])
        G = G / G[-1] * F[-1]
        keep = np.concatenate([[True], np.diff(F) > 0])  # F must be strictly increasing to be inverted
        dn = np.interp(np.interp(d[ins], sgrid, G), F[keep], sgrid[keep]) * sc
        u = dr.inward_direction(poly, P[sel][ins])
        Q[sel[ins]] = P[sel][ins] + (dn - d[ins] * sc)[:, None] * u
    return Q


if __name__ == "__main__":
    out, (sets, Pf, geoms, logJ, ratio, cuts) = run()
    print("fit residual median %.4f p95 %.4f over %d steps; mean c %.3f" % (out["fit_residual_median"], out["fit_residual_p95"], out["steps"], out["mean_c"]))
    res = {"fit": [out["fit_residual_median"], out["fit_residual_p95"]], "edges": out["edges"], "seeds": []}
    pred = {"expanding": [[], []], "shrinking": [[], []]}
    for k, (owner, P0) in enumerate(sets):
        sl = slice(cuts[k], cuts[k + 1])
        cdot = np.exp(-logJ[sl]) * ratio[owner]
        P = Pf[sl]
        bb.owner = owner
        z0 = bb.band_z(geoms, P)[2]
        Q = proxy_remap(geoms, P, owner, cdot)
        z1 = bb.band_z(geoms, Q)[2]
        sc = np.array([np.sqrt(geoms[o].area) for o in owner])
        s_ = np.linalg.norm(Q - P, axis=1) / sc
        res["seeds"].append({"seed": k, "before": round(z0, 2), "proxy": round(z1, 2), "shift_median": round(float(np.median(s_)), 4), "shift_p95": round(float(np.percentile(s_, 95)), 4)})
        print(res["seeds"][-1], flush=True)
        # predicted (harmonic mean of c) against observed ratio, by class and bin
        for r in np.unique(owner):
            sel = owner == r
            poly = geoms[r]
            scr = np.sqrt(poly.area)
            pts_r = shapely.points(P[sel])
            dd = shapely.distance(pts_r, poly.boundary) / scr
            inside = shapely.contains(poly, pts_r)
            cls = "expanding" if ratio[r] > 1 else "shrinking"
            A = np.array([poly.buffer(-e * scr).area if e > 0 else poly.area for e in EDGES])
            obs = np.histogram(dd[inside], EDGES)[0]
            exp = sel.sum() * (A[:-1] - A[1:]) / poly.area
            hm = np.array([1.0 / np.mean(1.0 / cdot[sel][inside & (dd >= EDGES[b]) & (dd < EDGES[b + 1])]) if (inside & (dd >= EDGES[b]) & (dd < EDGES[b + 1])).any() else np.nan for b in range(len(EDGES) - 1)])
            pred[cls][0].append((obs, exp))
            pred[cls][1].append((hm, exp))
    res["pooled"] = {}
    for cls in pred:
        obs = sum(o for o, _ in pred[cls][0]) / sum(e for _, e in pred[cls][0])
        w = np.array([e for _, e in pred[cls][1]])
        h = np.array([hm for hm, _ in pred[cls][1]])
        hmean = np.nansum(h * w, axis=0) / np.nansum(np.where(np.isfinite(h), w, 0), axis=0)
        res["pooled"][cls] = {"observed": obs.round(3).tolist(), "predicted": hmean.round(3).tolist()}
        print(cls, "observed", obs.round(3).tolist())
        print(cls, "predicted", hmean.round(3).tolist())
    (HERE / "data" / "jacobian_path.json").write_text(json.dumps(res))
    print("mean z before %.2f, proxy %.2f" % (np.mean([r["before"] for r in res["seeds"]]), np.mean([r["proxy"] for r in res["seeds"]])))
