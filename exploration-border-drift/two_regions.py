"""Two adjacent squares with a density contrast and uniform dots: dot density against distance to the shared border (#86).

    NUMBA_NUM_THREADS=8 uv run python two_regions.py
"""
import json
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry import box

import carto_flow.flow_cartogram as flow

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
N = 20000
rng = np.random.default_rng(0)
A, B = box(0, 0, 1, 1), box(1, 0, 2, 1)
gdf = gpd.GeoDataFrame({"v": [1.0, 4.0]}, geometry=[A, B])
pts = np.vstack([np.column_stack([rng.uniform(0, 1, N), rng.uniform(0, 1, N)]), np.column_stack([rng.uniform(1, 2, N), rng.uniform(0, 1, N)])])
owner = np.repeat([0, 1], N)
landmarks = gpd.GeoSeries(shapely.points(pts))
EDGES = np.array([0, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.0])  # distance to the shared border in sqrt(area) of the region


def profile(geoms, P):
    border = geoms[0].boundary.intersection(geoms[1].boundary)
    out = {}
    for r in (0, 1):
        sel = owner == r
        d = shapely.distance(shapely.points(P[sel]), border) / np.sqrt(geoms[r].area)
        # expected: uniform in the final region; the area within distance d of the border, by sampling the region
        b = geoms[r].bounds
        samp = shapely.points(np.column_stack([rng.uniform(b[0], b[2], 400000), rng.uniform(b[1], b[3], 400000)]))
        samp = samp[shapely.contains(geoms[r], samp)]
        ds = shapely.distance(samp, border) / np.sqrt(geoms[r].area)
        obs = np.histogram(d, EDGES)[0]
        exp = np.histogram(ds, EDGES)[0] / len(ds) * sel.sum()
        out[r] = [round(float(o / e), 2) if e > 0 else None for o, e in zip(obs, exp)]
    return out


def run(label, **kw):
    base = dict(snapshot_every=1, n_iter=400, show_progress=False, mean_tol=0.005, max_tol=0.01)
    base.update(kw)
    c = flow.create_flow_cartogram(gdf, "v", landmarks=landmarks, options=flow.MorphOptions(**base))
    fin = c.snapshots[-1]
    P = np.array([[p.x, p.y] for p in fin.landmarks])
    row = {"variant": label, "status": c.status.value, "iterations": int(c.niterations), "ratio_by_distance": profile(list(fin.geometry), P)}
    print(row, flush=True)
    return row


if __name__ == "__main__":
    rows = [run("grid 128", grid=128), run("grid 256", grid=256), run("grid 512", grid=512), run("grid 512, recompute_every 1", grid=512, recompute_every=1)]
    (HERE / "data" / "two_regions.json").write_text(json.dumps({"edges": EDGES.tolist(), "rows": rows}))
