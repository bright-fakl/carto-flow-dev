"""usage: run_extra.py <pipeline|presets|landmarks>  writes ../data/<what>.jsonl (output geometries to the scratch directory)

pipeline:  CartogramWorkflow.morph_multiresolution(min_resolution=128, levels=3) with default options at several dt
presets:   preset_fast / preset_balanced / preset_high_quality at their own dt and at other dt
landmarks: issue 86 border-band z-score with landmarks and snapshot_every=1 (also frames and displacement per iteration)
"""
import json
import pickle
import sys

from common import *

from carto_flow.flow_cartogram.refresh import score_rose, should_refresh
from carto_flow.flow_cartogram.workflow import CartogramWorkflow

DTS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.8]
R = 0.01


def replay_recomputes(score, rre, rr):
    """Number of velocity-field refreshes implied by the score history (same rule as the loop)."""
    n, since, rose, prev = 0, 0, False, np.inf
    for step, s in enumerate(score):
        if should_refresh(step, since, rose, rre, rr):
            since = 0
            n += 1
        since += 1
        rose = score_rose(s, prev, rr)
        prev = s
    return n


def pipeline(case, dt, rr):
    g, col, sc, _, _ = load_case(case)
    o = MorphOptions(show_progress=False, n_iter=300, dt=dt, refresh_on_rise=rr, area_scale=sc)
    wf = CartogramWorkflow(g, col, None, None, o)
    t = time.perf_counter()
    wf.morph_multiresolution(min_resolution=128, levels=3, options=o)
    wall = time.perf_counter() - t
    levels, cost, tit, trec = [], 0.0, 0, 0
    for res in wf.results[1:]:
        s = score_of(res, res.options)
        ratio = RATIO[(case, res.grid.sx)]
        rec = replay_recomputes(s, res.options.recompute_every, rr)
        cost += len(s) + rec * ratio
        tit += len(s)
        trec += rec
        levels.append(dict(grid=int(res.grid.sx), status=str(res.status.value), it=int(len(s)), rec=rec, best=float(s.min())))
    geoms = list(wf.latest.latest.geometry)
    rec = dict(case=case, dt=dt, rr=rr, it=tit, rec=trec, cost=cost, wall=round(wall, 2), levels=levels,
               **metrics(geoms, g[col].to_numpy(float)))
    return rec, geoms


def presets(case, preset, dt, extra):
    g, col, sc, _, _ = load_case(case)
    base = getattr(MorphOptions, f"preset_{preset}")()
    o = base.copy_with(show_progress=False, dt=dt, **extra)
    grid_size = o.grid_size
    rec, r, geoms = run_one(case, grid_size, dt, o.refresh_on_rise, base_opts=o, preset=preset, preset_dt=base.dt, n_iter_set=o.n_iter,
                            mean_tol_set=o.mean_tol, max_tol_set=o.max_tol)
    return rec, geoms


def landmarks_case(dt, seed, recompute_every=None):
    import geopandas as gpd

    import carto_flow.proportional_cartogram as prop

    g = data.load_us_census(population=True, poverty=True)
    col = "Below Poverty Level"
    dots = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
    owner = np.array([list(g.index).index(o) for o in dots["original_index"]])
    kw = dict(area_scale=1e-6, snapshot_every=1, n_iter=400, show_progress=False, dt=dt)
    if recompute_every:
        kw["recompute_every"] = recompute_every
    opts = MorphOptions.preset_balanced().copy_with(**kw)
    t = time.perf_counter()
    cart = morph_gdf(g, "Population", landmarks=gpd.GeoSeries(list(dots.geometry), crs=g.crs), options=opts)
    wall = time.perf_counter() - t

    def z_of(snap, frac=0.06):
        P = np.array([[p.x, p.y] for p in snap.landmarks])
        geoms = list(snap.geometry)
        obs = exp = var = 0.0
        inside = 0
        for r in range(len(g)):
            sel = owner == r
            if sel.sum() < 8:
                continue
            poly = geoms[r].buffer(0)
            inner = poly.buffer(-frac * np.sqrt(poly.area))
            p = 1 - inner.area / poly.area
            obs += (~shapely.contains(inner, shapely.points(P[sel]))).sum()
            exp += sel.sum() * p
            var += sel.sum() * p * (1 - p)
        ins = float(np.mean([shapely.contains(geoms[owner[i]].buffer(0), shapely.Point(*P[i])) for i in range(len(P))]))
        return float(obs), float(exp), float((obs - exp) / np.sqrt(var)), ins

    snaps = list(cart.snapshots)
    fin = snaps[-1]
    obs, exp, z, ins = z_of(fin)
    obs0, exp0, z0, _ = z_of(snaps[0])
    # displacement per iteration (consecutive snapshots), in cells and as a fraction of the map extent
    cell = cart.grid.dx
    b = g.total_bounds
    extent = max(b[2] - b[0], b[3] - b[1])
    mx, mean_pt = [], []
    for a, c in zip(snaps[:-1], snaps[1:]):
        ca = shapely.get_coordinates(np.array(list(a.geometry), dtype=object))
        cb = shapely.get_coordinates(np.array(list(c.geometry), dtype=object))
        d = np.hypot(*(cb - ca).T)
        mx.append(float(d.max()))
        mean_pt.append(float(d.mean()))
    s = score_of(cart, opts)
    return dict(dt=dt, seed=seed, rre=opts.recompute_every, status=str(cart.status.value), it=int(len(s)), frames=len(snaps),
                obs=obs, exp=exp, z=z, z_start=z0, inside=ins,
                max_disp_cells=max(mx) / cell, mean_max_disp_cells=float(np.mean(mx)) / cell,
                max_disp_frac=max(mx) / extent, mean_disp_cells=float(np.mean(mean_pt)) / cell, cell=cell, extent=extent,
                wall=round(wall, 2)), None


def main(what):
    what0 = what
    what = "landmarks" if what == "landmarks2" else what
    out = os.path.join(DATA, f"{what}.jsonl")
    shp = os.path.join(SCRATCH, "shapes", f"{what}.pkl")
    os.makedirs(os.path.dirname(shp), exist_ok=True)
    shapes = pickle.load(open(shp, "rb")) if os.path.exists(shp) else {}
    done = {json.loads(l)["_key"] for l in open(out)} if os.path.exists(out) else set()
    g, col, sc, extra, n0 = load_case("states")
    run_one("states", 64, 0.2, R, g=g.iloc[:30])  # numba warm-up
    J = []
    if what == "pipeline":
        for case in ("states", "districts"):
            for rr in (R, None):
                for dt in (DTS if rr else (0.2, 0.4, 0.6)):
                    J.append((f"pipeline|{case}|{dt}|{rr}", lambda c=case, d=dt, r=rr: pipeline(c, d, r)))
    elif what == "presets":
        for case in ("states", "districts"):
            for preset, dts in (("fast", (0.2, 0.3, 0.4, 0.6)), ("balanced", (0.2, 0.3, 0.4, 0.6)), ("high_quality", (0.1, 0.2, 0.3, 0.4))):
                for dt in dts:
                    J.append((f"presets|{case}|{preset}|{dt}", lambda c=case, p=preset, d=dt: presets(c, p, d, {})))
    elif what0 == "landmarks":
        for seed in (7, 8, 9, 10, 11):
            for dt in DTS:
                J.append((f"landmarks|{seed}|{dt}", lambda d=dt, s=seed: landmarks_case(d, s)))
        for dt in (0.2, 0.4, 0.6):
            J.append((f"landmarks|7|{dt}|rre1", lambda d=dt: landmarks_case(d, 7, 1)))
    elif what0 == "landmarks2":
        for seed in (7, 8, 9, 10, 11):
            for dt, rre in [(0.2, 5), (0.2, 20), (0.4, 5), (0.6, 3), (0.8, 2), (0.4, 2), (0.6, 2), (0.3, 7)]:
                J.append((f"landmarks|{seed}|{dt}|rre{rre}", lambda d=dt, s=seed, r=rre: landmarks_case(d, s, r)))
    for key, fn in J:
        if key in done:
            continue
        try:
            rec, geoms = fn()
        except Exception as e:  # noqa
            print("ERROR", key, repr(e)[:300], flush=True)
            continue
        rec["_key"] = key
        if geoms is not None:
            shapes[key] = [x.wkb for x in geoms]
            pickle.dump(shapes, open(shp, "wb"))
        rec.pop("score", None)
        open(out, "a").write(json.dumps(rec) + "\n")
        print(key, rec, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
