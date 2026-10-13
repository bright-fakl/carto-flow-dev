"""Distance remap on the two-region toy case of #86 (A: value 1, B: value 4), grid 256 and 512."""
import json
import warnings

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.flow_cartogram as flow
import distance_remap as dr
import sector_remap as sr
import two_regions as tr

warnings.filterwarnings("ignore")
rng = np.random.default_rng(11)
NT = 2000
tracers = np.vstack([np.column_stack([rng.uniform(0, 1, NT), rng.uniform(0, 1, NT)]), np.column_stack([rng.uniform(1, 2, NT), rng.uniform(0, 1, NT)])])
owner_t = np.repeat([0, 1], NT)
rows = []
for grid in (256,):
    allP = np.vstack([tr.pts, tracers])
    c = flow.create_flow_cartogram(
        tr.gdf, "v", landmarks=gpd.GeoSeries(shapely.points(allP)),
        options=flow.MorphOptions(n_iter=400, show_progress=False, mean_tol=0.005, max_tol=0.01, grid=grid),
    )
    fin = c.snapshots[-1]
    L = np.array([[p.x, p.y] for p in fin.landmarks])
    geoms = [x.buffer(0) for x in fin.geometry]
    P, T = L[: len(tr.pts)], L[len(tr.pts):]
    for K, signed in ((1, False), (8, False), (1, True), (8, True)):
        m = sr.SectorRemap(geoms, T, owner_t, K, signed=signed)
        Q = m.apply(P, tr.owner)
        sc = np.array([np.sqrt(geoms[o].area) for o in tr.owner])
        s = np.linalg.norm(Q - P, axis=1) / sc
        inside = {r: float(shapely.contains(geoms[r], shapely.points(Q[tr.owner == r])).mean()) for r in (0, 1)}
        row = {"grid": grid, "sectors": K, "signed": signed, "inside_own": inside, "before": tr.profile(geoms, P), "after": tr.profile(geoms, Q), "shift_median": round(float(np.median(s)), 4), "shift_p95": round(float(np.percentile(s, 95)), 4)}
        print(row, flush=True)
        rows.append(row)
(tr.HERE / "data" / "toy_remap.json").write_text(json.dumps({"edges": tr.EDGES.tolist(), "rows": rows}))
