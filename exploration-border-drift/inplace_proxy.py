"""Border pile-up of the dots (#86) without snapshots: the area scaling summed in place, and the first velocity field only.

    NUMBA_NUM_THREADS=8 uv run python inplace_proxy.py

One morph, no save_internals and no snapshot_every. A wrapper around the displacement of the landmarks (the dots)
  - adds dt * div v(x) at the position of every dot to a running sum log J (summed in place), and
  - keeps a copy of the first velocity field.
Two remaps of the distance to the border follow, as in jacobian_path.py:
  inplace : the density ratio exp(-log J) * A_final / A_original of every dot from the running sum;
  first   : the density ratio exp(-(r(d) - 1) * ln(A_final / A_original)) per region, with r(d) the divergence of the first
            velocity field relative to its value deep inside the region, as a function of the distance to the border
            in cells (original geometry); it assumes the divergence profile stays the same during the morph.
"""
import json
import os
import time
import tracemalloc
import warnings
from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import numpy as np
import shapely

import border_band as bb
import carto_flow.flow_cartogram.algorithm as alg
import carto_flow.flow_cartogram as flow
import carto_flow.proportional_cartogram as prop
import distance_remap as dr
from jacobian_path import EDGES, proxy_remap_sampled
from velocity_profile import sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
SKIP_FIRST = bool(os.environ.get("SKIP_FIRST"))
CELL_EDGES = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 20, 1e9])


def run(grid_size=256, n_seeds=8, wrap=True):
    g = bb.g
    col = "Below Poverty Level"
    sets = []
    for seed in range(n_seeds):
        d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
        sets.append((np.array([list(g.index).index(o) for o in d["original_index"]]), np.array([[p.x, p.y] for p in d.geometry])))
    allP = np.vstack([P for _, P in sets])
    st = {"n": len(allP), "key": None, "div": None, "logJ": np.zeros(len(allP)), "first": None, "grid": None, "calls": 0}
    orig_fn = alg.displace_coords_numba

    def wrapped(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel=True):
        if coords.ndim == 2 and coords.shape[0] == st["n"]:
            key = float(vx.sum())  # the solver overwrites one buffer, so the object does not change with the field
            if st["key"] != key:
                st["key"] = key
                st["div"] = np.gradient(vx, dx, axis=1) + np.gradient(vy, dy, axis=0)
                st["grid"] = SimpleNamespace(x_coords=xs, y_coords=ys, dx=dx, dy=dy)
                if st["first"] is None:
                    st["first"] = (vx.copy(), vy.copy(), st["div"].copy(), st["grid"])
            st["logJ"] += dt * sample(st["div"], st["grid"], coords)
            st["calls"] += 1
        return orig_fn(coords, xs, ys, vx, vy, dt, dx, dy, use_parallel)

    if wrap:
        alg.displace_coords_numba = wrapped
    try:
        t0 = time.perf_counter()
        c = flow.create_flow_cartogram(
            g, "Population", landmarks=gpd.GeoSeries(shapely.points(allP), crs=g.crs),
            options=flow.MorphOptions(area_scale=1e-6, grid=grid_size, n_iter=400, show_progress=False),
        )
        st["seconds"] = time.perf_counter() - t0
    finally:
        alg.displace_coords_numba = orig_fn
    fin = c.snapshots[-1]
    Pf = np.array([[p.x, p.y] for p in fin.landmarks])
    geoms = [x.buffer(0) for x in fin.geometry]
    return sets, Pf, geoms, st, c


def first_field_profiles(orig, st, n_pts=3000):
    """Per region: divergence of the first field relative to its interior value, in bins of the distance in cells."""
    vx, vy, div, grid = st["first"]
    cell = grid.dx
    prof = {}
    rng = np.random.default_rng(0)
    pooled = []
    for r, poly in enumerate(orig):
        poly = poly.buffer(0)
        sc = np.sqrt(poly.area)
        P = dr.uniform_in(poly, n_pts)
        pts = shapely.points(P)
        d = shapely.distance(pts, poly.boundary)
        dv = sample(div, grid, P)
        s = d / sc
        ok = (s > 0.15).sum() > 50
        ref = np.median(dv[s > 0.15]) if ok else np.nan
        row = np.full(len(CELL_EDGES) - 1, np.nan)
        for b in range(len(row)):
            m = (d / cell >= CELL_EDGES[b]) & (d / cell < CELL_EDGES[b + 1])
            if m.sum() > 5:
                row[b] = dv[m].mean() / ref if np.isfinite(ref) and abs(ref) > 0 else np.nan
        prof[r] = (row, ref)
        pooled.append(row)
    refs = np.array([p[1] for p in prof.values()])
    good = np.isfinite(refs) & (np.abs(refs) > 0.3 * np.nanmedian(np.abs(refs)))
    pool = np.nanmedian(np.array(pooled)[good], axis=0)
    return prof, pool, cell


def first_field_remap(geoms, orig, P, owner, prof, pool, cell, ratio):
    Q = P.copy()
    centers = 0.5 * (CELL_EDGES[:-1] + np.minimum(CELL_EDGES[1:], 40))
    for r in np.unique(owner):
        sel = np.where(owner == r)[0]
        poly = geoms[r]
        sc = np.sqrt(poly.area)
        d = dr.signed_distance(poly, P[sel])
        ins = d > 0
        if ins.sum() < 3:
            continue
        row = prof[r][0]
        row = np.where(np.isfinite(row), row, pool)  # fall back to the pooled profile where the region has none
        ok = np.isfinite(row)
        L = np.log(ratio[r])
        sgrid = np.linspace(0, 0.5, 201)
        rfun = np.interp(sgrid * sc / cell, centers[ok], row[ok])
        cfun = np.exp(-(rfun - 1.0) * L)
        A = np.array([poly.buffer(-s_ * sc).area if s_ > 0 else poly.area for s_ in sgrid])
        F = 1 - A / poly.area
        dens = np.diff(F) * 0.5 * (cfun[1:] + cfun[:-1])
        G = np.concatenate([[0], np.cumsum(dens)])
        G = G / G[-1] * F[-1]
        dn = np.interp(np.interp(d[ins] / sc, sgrid, G), F, sgrid) * sc
        u = dr.inward_direction(poly, P[sel][ins])
        Q[sel[ins]] = P[sel][ins] + (dn - d[ins])[:, None] * u
    return Q


if __name__ == "__main__":
    sets, Pf, geoms, st, c = run()
    orig = list(bb.g.geometry)
    ratio = np.array([geoms[r].area / orig[r].area for r in range(len(orig))])
    prof, pool, cell = first_field_profiles(orig, st)
    cuts = np.cumsum([0] + [len(P) for _, P in sets])
    res = {"calls": st["calls"], "pooled_first_profile": pool.round(3).tolist(), "cell_edges": CELL_EDGES[:-1].tolist(), "seeds": []}
    for k, (owner, P0) in enumerate(sets):
        sl = slice(cuts[k], cuts[k + 1])
        P = Pf[sl]
        bb.owner = owner
        z0 = bb.band_z(geoms, P)[2]
        cdot = np.exp(-st["logJ"][sl]) * ratio[owner]
        Qi = proxy_remap_sampled(geoms, P, owner, cdot, n_ref=400)
        Qf = P if SKIP_FIRST else first_field_remap(geoms, orig, P, owner, prof, pool, cell, ratio)
        sc = np.array([np.sqrt(geoms[o].area) for o in owner])
        row = {"seed": k, "before": round(z0, 2), "inplace": round(bb.band_z(geoms, Qi)[2], 2), "first_field": round(bb.band_z(geoms, Qf)[2], 2),
               "shift_inplace": round(float(np.median(np.linalg.norm(Qi - P, axis=1) / sc)), 4), "shift_first": round(float(np.median(np.linalg.norm(Qf - P, axis=1) / sc)), 4)}
        res["seeds"].append(row)
        print(row, flush=True)
    for key in ("before", "inplace", "first_field"):
        print(key, round(float(np.mean([r[key] for r in res["seeds"]])), 2))
    (HERE / "data" / ("inplace_sampled.json" if SKIP_FIRST else "inplace_proxy.json")).write_text(json.dumps(res))
