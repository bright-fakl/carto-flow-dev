"""Option 3 of #86: remap the distance to the region border of co-advected dots so that the profile is uniform again.

    NUMBA_NUM_THREADS=8 uv run python distance_remap.py

Dense tracer points, uniform in each original region, are carried through the same morph as the dots. For each region
the empirical distribution G of the tracers' distance to the morphed border is compared with the distribution F of a
uniform sample of the morphed region; a dot at distance d moves along the direction to its nearest border point to the
distance F^-1(G(d)). "region": G and F per region (units of the distance); "pooled": one G and F over all regions in
units of sqrt(area).
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

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(3)


def uniform_in(poly, n):
    out = np.empty((0, 2))
    minx, miny, maxx, maxy = poly.bounds
    while len(out) < n:
        c = np.column_stack([rng.uniform(minx, maxx, 4 * n), rng.uniform(miny, maxy, 4 * n)])
        out = np.vstack([out, c[shapely.contains_xy(poly, c[:, 0], c[:, 1])]])
    return out[:n]


def signed_distance(poly, P):
    pts = shapely.points(P)
    d = shapely.distance(pts, poly.boundary)
    return np.where(shapely.contains(poly, pts), d, -d)


def area_inside(poly, dgrid):
    """Area of the part of poly farther than d from the border, for d in dgrid."""
    return np.array([poly.buffer(-d).area if d > 0 else poly.area for d in dgrid])


def inward_direction(poly, P):
    pts = shapely.points(P)
    line = shapely.shortest_line(pts, poly.boundary)
    c = shapely.get_coordinates(line).reshape(-1, 2, 2)
    v = c[:, 0, :] - c[:, 1, :]  # from the nearest border point to the point
    n = np.linalg.norm(v, axis=1)
    return v / np.maximum(n, 1e-300)[:, None]


class Remap:
    """Monotone map of the distance to the border, built from tracers (per region or pooled)."""

    def __init__(self, geoms, tracers, owner_t, pooled):
        self.geoms, self.pooled = geoms, pooled
        self.sorted_d, self.Fgrid, self.dgrid, self.scale = {}, {}, {}, {}
        s_all, F_all = [], []
        if pooled:
            sgrid = np.linspace(0, 0.5, 201)
        for r, poly in enumerate(geoms):
            T = tracers[owner_t == r]
            d = signed_distance(poly, T)
            d = d[d >= 0]
            sc = np.sqrt(poly.area)
            self.scale[r] = sc
            dgrid = (sgrid * sc) if pooled else np.linspace(0, 0.5 * sc, 201)
            F = 1.0 - area_inside(poly, dgrid) / poly.area
            self.dgrid[r], self.Fgrid[r] = dgrid, F
            self.sorted_d[r] = np.sort(d / (sc if pooled else 1.0))
        if pooled:
            self.pooled_sorted = np.sort(np.concatenate([self.sorted_d[r] for r in self.sorted_d]))
            self.pooled_F = np.mean([self.Fgrid[r] for r in self.Fgrid], axis=0)
            self.sgrid = sgrid

    def new_distance(self, r, d):
        sc = self.scale[r]
        if self.pooled:
            s = d / sc
            u = np.searchsorted(self.pooled_sorted, s, side="right") / (len(self.pooled_sorted) + 1)
            return np.interp(u, self.pooled_F, self.sgrid) * sc
        sd = self.sorted_d[r]
        u = np.searchsorted(sd, d, side="right") / (len(sd) + 1)
        return np.interp(u, self.Fgrid[r], self.dgrid[r])

    def apply(self, P, owner):
        Q = P.copy()
        for r in np.unique(owner):
            sel = np.where(owner == r)[0]
            poly = self.geoms[r]
            d = signed_distance(poly, P[sel])
            ins = d > 0
            if not ins.any():
                continue
            dn = self.new_distance(r, d[ins])
            u = inward_direction(poly, P[sel][ins])
            Q[sel[ins]] = P[sel][ins] + (dn - d[ins])[:, None] * u
        return Q


def displacement(geoms, P, Q, owner):
    sc = np.array([np.sqrt(geoms[o].area) for o in owner])
    s = np.linalg.norm(Q - P, axis=1) / sc
    return {"median": round(float(np.median(s)), 4), "p95": round(float(np.percentile(s, 95)), 4), "max": round(float(s.max()), 3),
            "moved_more_than_5pct": round(float((s > 0.05).mean()), 3)}


def states(n_seeds=8, n_tracers=2000):
    g = bb.g
    col = "Below Poverty Level"
    dot_sets = []
    for seed in range(n_seeds):
        d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
        dot_sets.append((np.array([list(g.index).index(o) for o in d["original_index"]]), np.array([[p.x, p.y] for p in d.geometry])))
    tr = np.vstack([uniform_in(poly, n_tracers) for poly in g.geometry])
    owner_t = np.repeat(np.arange(len(g)), n_tracers)
    allP = np.vstack([P for _, P in dot_sets] + [tr])
    cart = flow.create_flow_cartogram(
        g, "Population", landmarks=gpd.GeoSeries(shapely.points(allP), crs=g.crs),
        options=flow.MorphOptions(area_scale=1e-6, n_iter=400, show_progress=False),
    )
    fin = cart.snapshots[-1]
    L = np.array([[p.x, p.y] for p in fin.landmarks])
    geoms = [x.buffer(0) for x in fin.geometry]
    import pickle
    pickle.dump({"L": L, "geoms": [shapely.to_wkb(x) for x in geoms], "owner_t": owner_t, "dot_sets": dot_sets, "status": cart.status.value, "iterations": int(cart.niterations)}, open(HERE / "data" / "states_morph.pkl", "wb"))
    sizes = [len(P) for _, P in dot_sets]
    cuts = np.cumsum([0] + sizes)
    tracers_f = L[cuts[-1]:]
    maps = {"region": Remap(geoms, tracers_f, owner_t, False), "pooled": Remap(geoms, tracers_f, owner_t, True)}
    rows = {"status": cart.status.value, "iterations": int(cart.niterations), "seeds": []}
    for k, (owner, P0) in enumerate(dot_sets):
        P = L[cuts[k]:cuts[k + 1]]
        bb.owner = owner
        row = {"seed": k, "before": round(bb.band_z(geoms, P)[2], 2)}
        for name, m in maps.items():
            Q = m.apply(P, owner)
            row[name] = {"z": round(bb.band_z(geoms, Q)[2], 2), "shift": displacement(geoms, P, Q, owner)}
        rows["seeds"].append(row)
        print(row, flush=True)
    return rows


if __name__ == "__main__":
    out = {"states": states()}
    (HERE / "data" / "distance_remap_states.json").write_text(json.dumps(out))
