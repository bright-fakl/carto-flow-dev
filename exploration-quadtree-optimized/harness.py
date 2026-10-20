"""Common test protocol: load a dataset, run the multiresolution ladder, print the metrics."""
import os, sys, time, warnings, json
warnings.filterwarnings("ignore")
import numpy as np, shapely
import carto_flow, carto_flow.data as data
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
import carto_flow.flow_cartogram.algorithm as alg

def load(dataset="county"):
    if dataset == "county":
        g = data.load_us_census(level="county", max_segment_length=int(os.environ.get("MSL", "1000")))
    elif dataset == "cd":
        g = data.load_us_census(level="congressional_district", max_segment_length=1000)
    elif dataset == "coarse":
        from carto_flow.geo_utils import simplify_coverage
        g = simplify_coverage(data.load_us_census(level="county"), tolerance=float(os.environ.get("TOL", "4000")))
        if os.environ.get("CSEG"):
            from carto_flow.geo_utils import densify_coverage
            g = densify_coverage(g, float(os.environ["CSEG"]))
    elif dataset == "mid":
        from carto_flow.geo_utils import simplify_coverage, densify_coverage
        g = simplify_coverage(data.load_us_census(level="county"), tolerance=float(os.environ.get("MTOL", "1000")))
        if os.environ.get("MSEG", "2000") != "0":
            g = densify_coverage(g, float(os.environ.get("MSEG", "2000")))
    else:
        raise ValueError(dataset)
    g = g.reset_index(drop=True)
    v = g["Population"].to_numpy(float)
    if float(os.environ.get('VFLOOR', '0')) > 0:
        v = np.maximum(v, float(os.environ['VFLOOR']) * np.median(v))
    return g[["geometry"]].assign(v=v), v

def metrics(o, v, dataset=None, label=None):
    o = np.array(o, dtype=object)
    valid = shapely.is_valid(o)
    a = shapely.area(o)
    T = v / v[valid].sum() * a[valid].sum()
    e = np.abs(a - T) / T * 100
    ev = e[valid]
    extra = {}
    bf = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"out/basevalid_{dataset}.npy")
    if dataset is not None and os.path.exists(bf):
        bv = np.load(bf)
        Tb = v / v[bv].sum() * a[bv].sum()
        eb = (np.abs(a - Tb) / Tb * 100)[bv]
        extra = dict(mean_b=eb.mean(), med_b=np.median(eb), p95_b=np.percentile(eb, 95), gt10_b=int((eb > 10).sum()))
    return dict(**extra, invalid=int((~valid).sum()), nv=len(shapely.get_coordinates(o)),
                mean=ev.mean(), med=np.median(ev), p95=np.percentile(ev, 95), gt10=int((ev > 10).sum()))

def run(dataset="county", n_iter=1000, label="", extra=None):
    gdf, v = load(dataset)
    nv0 = len(shapely.get_coordinates(gdf.geometry.values))
    t = time.time()
    w = CartogramWorkflow(gdf, "v", validate=False)
    mo = json.loads(os.environ.get('MORPH_OPTS', '{}'))
    if os.environ.get('SCHED'):
        opts = [MorphOptions(area_scale=1e-6, n_iter=int(k), show_progress=False, stall_patience=None, **({'snapshot_every': int(os.environ['SNAP'])} if os.environ.get('SNAP') else {}), **mo) for k in os.environ['SCHED'].split(',')]
    else:
        opts = MorphOptions(area_scale=1e-6, n_iter=n_iter, show_progress=False, **mo)
    w.morph_multiresolution(min_resolution="auto", levels="auto", options=opts)
    dt = time.time() - t
    c = w[-1]
    m = metrics(c.get_geometry(), v, dataset, label)
    lv = " | ".join(f"{x.grid.dx/1000:.1f}km {x.niterations}it {x.status.name[:5]} best {x.best_iteration} mean {x.get_errors().mean_error_pct:.2f} max {x.get_errors().max_error_pct:.0f}"
                    for x in w if x.grid is not None)
    print(f"[{label}] {dataset} n_iter={n_iter} time {dt:.1f}s inv {m['invalid']} nv {nv0}->{m['nv']} "
          f"err mean {m['mean']:.2f} med {m['med']:.3f} p95 {m['p95']:.2f} >10% {m['gt10']} | levels {lv}"
          + (f" | on baseline-valid: mean {m['mean_b']:.2f} med {m['med_b']:.3f} p95 {m['p95_b']:.2f} >10% {m['gt10_b']}" if 'mean_b' in m else "")
          + (f" | {extra()}" if extra else ""), flush=True)
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"), exist_ok=True)
    oo = np.array(c.get_geometry(), dtype=object)

    plat = {}
    if os.environ.get('SNAP'):
        snaps = [s for s in c.snapshots.snapshots if s.iteration >= c.niterations - 100 and s.iteration < c.niterations]
        rows = []
        for s in snaps:
            o_ = np.array(s.geometry, dtype=object); va = shapely.is_valid(o_); a_ = shapely.area(o_)
            T_ = v / v[va].sum() * a_[va].sum(); e_ = (np.abs(a_ - T_) / T_ * 100)[va]
            rows.append((e_.mean(), np.median(e_), np.percentile(e_, 95), (e_ > 10).sum(), (~va).sum()))
        if rows:
            r_ = np.array(rows, float)
            plat = dict(plat_n=len(rows), plat_mean=r_[:, 0].mean(), plat_med=float(np.exp(np.log(r_[:, 1] + 1e-6).mean())), plat_p95=r_[:, 2].mean(), plat_gt10=r_[:, 3].mean(), plat_inv=r_[:, 4].mean())
    if os.environ.get('PROTO'):
        import resource
        rec = dict(proto=os.environ['PROTO'], method=os.environ.get('METHOD', label), dataset=dataset, time=round(dt, 1), rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
                   levels=lv, **plat, **{k: (round(float(x), 4) if not isinstance(x, (int, np.integer)) else int(x)) for k, x in m.items()}, nv0=nv0,
                   cfg=dict(MSL=os.environ.get('MSL'), MORPH_OPTS=os.environ.get('MORPH_OPTS'), n_iter=n_iter))
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out/protocol.jsonl'), 'a') as f: f.write(json.dumps(rec) + chr(10))
    if os.environ.get('REASONS'):
        for i in np.flatnonzero(~shapely.is_valid(oo))[:10]: print('  invalid', i, shapely.is_valid_reason(oo[i])[:120])
    np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"out/{label}_{dataset}.npz"), area=shapely.area(oo), valid=shapely.is_valid(oo), v=v)
    np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"out/{label}_{dataset}_wkb.npy"), shapely.to_wkb(oo))
    if label == "baseline":
        np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"out/basevalid_{dataset}.npy"), shapely.is_valid(np.array(c.get_geometry(), dtype=object)))
    return w, m
