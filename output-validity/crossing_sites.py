import warnings, numpy as np, shapely, geopandas as gpd, pandas as pd
from shapely import STRtree
warnings.filterwarnings("ignore")
from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
MIN = data.load_us_census(population=True, race=True, simplify=1000); MIN["Minorities"] = MIN[["Black or African American","Asian","Hispanic or Latino"]].sum(axis=1)
COUNTIES = gpd.read_parquet("/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/counties_prepared.parquet")
def parts(g): return list(g.geoms) if hasattr(g, "geoms") else [g]
def classify(label, gdf, col, kw):
    o = MorphOptions(show_progress=False, snapshot_every=1, **kw)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore"); r = morph_gdf(gdf, col, options=o)
    cell = o.get_grid(o._calculate_bounds_from_geometries(gdf.geometry.values)).dx
    snaps = [np.asarray(s.geometry.geometry if hasattr(s.geometry, "geometry") else s.geometry, dtype=object) for s in r.snapshots]
    final_bad = np.flatnonzero(~shapely.is_valid(snaps[-1]))
    out = {"inside the region itself (thin land neck)": 0, "inside another region": 0, "outside all regions (water or a gap)": 0, "not classified": 0}
    gaps = []
    for i in final_bad:
        first = next(k for k in range(1, len(snaps)) if not shapely.is_valid(snaps[k][i]))
        bad, prev = snaps[first][i], snaps[first - 1]
        txt = shapely.is_valid_reason(bad)
        if "[" not in txt: out["not classified"] += 1; continue
        pt = shapely.Point(*[float(v) for v in txt.split("[")[1].rstrip("]").split()])
        pa = min(parts(prev[i]), key=lambda p: p.distance(pt)); c = np.asarray(pa.exterior.coords)[:-1]
        near = np.flatnonzero(np.hypot(c[:, 0] - pt.x, c[:, 1] - pt.y) < 3 * cell)
        best = None
        for a in near:
            for b in near:
                if b > a + 2 and not (a == 0 and b == len(c) - 1):
                    d = np.hypot(*(c[a] - c[b]))
                    if best is None or d < best[0]: best = (d, (c[a] + c[b]) / 2)
        if best is None: out["not classified"] += 1; continue
        m = shapely.Point(*best[1]); gaps.append(best[0] / cell)
        if prev[i].contains(m): out["inside the region itself (thin land neck)"] += 1
        else:
            tree = STRtree(prev); hits = [j for j in tree.query(m, predicate="intersects") if j != i and prev[j].contains(m)]
            out["inside another region" if hits else "outside all regions (water or a gap)"] += 1
    print(f"{label}: invalid {len(final_bad)}; " + "; ".join(f"{k}: {v}" for k, v in out.items()) + f"; gap before the crossing median {np.median(gaps) if gaps else float('nan'):.4f} cells", flush=True)
classify("issue 85 map, grid 512", MIN, "Minorities", dict(grid_size=512))
classify("districts 256", DISTRICTS, "Population", dict(grid_size=256))
classify("districts 512 0.5/1 %", DISTRICTS, "Population", dict(grid_size=512, mean_tol=.005, max_tol=.01, n_iter=400))
classify("counties 256", COUNTIES, "total_votes", dict(grid_size=256, area_scale=1e-6, n_iter=300))
classify("counties 512", COUNTIES, "total_votes", dict(grid_size=512, area_scale=1e-6, n_iter=300))
