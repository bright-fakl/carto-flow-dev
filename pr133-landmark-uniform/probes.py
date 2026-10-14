"""Dots corrected with probe points (MorphOptions.landmark_probes): z-score over 8 seeds, cost and smoothness (PR 133).

    NUMBA_NUM_THREADS=8 uv run python probes.py
"""
import json
import time
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.flow_cartogram as flow
import carto_flow.proportional_cartogram as prop
from carto_flow import data

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
g = data.load_us_census(population=True, poverty=True)
col = "Below Poverty Level"
EDGES = np.array([0, 0.01, 0.02, 0.04, 0.06, 0.1, 0.2, 0.4, 0.6])


def band_z(geoms, P, owner, frac=0.06):
    obs = exp = var = 0.0
    for r in range(len(geoms)):
        sel = owner == r
        if sel.sum() < 8:
            continue
        poly = geoms[r].buffer(0)
        inner = poly.buffer(-frac * np.sqrt(poly.area))
        p = 1 - inner.area / poly.area
        obs += (~shapely.contains(inner, shapely.points(P[sel]))).sum()
        exp += sel.sum() * p
        var += sel.sum() * p * (1 - p)
    return (obs - exp) / np.sqrt(var)


rows = []
for probes in (0, 25, 50, 100):
    zs, times, mt = [], [], []
    for seed in range(8):
        d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=seed)
        owner = np.array([list(g.index).index(o) for o in d["original_index"]])
        t0 = time.perf_counter()
        c = flow.create_flow_cartogram(g, "Population", landmarks=gpd.GeoSeries(list(d.geometry), crs=g.crs), options=flow.MorphOptions(area_scale=1e-6, show_progress=False, landmark_probes=probes))
        mt.append(time.perf_counter() - t0)
        geoms = list(c.get_geometry())
        t0 = time.perf_counter()
        Q = shapely.get_coordinates(np.asarray(c.get_landmarks(uniform=True), dtype=object))
        times.append(time.perf_counter() - t0)
        zs.append(band_z(geoms, Q, owner))
    rows.append({"probes_per_region": probes, "z_mean": round(float(np.mean(zs)), 2), "z_sd": round(float(np.std(zs)), 2), "get_landmarks_seconds": round(float(np.median(times)), 3), "morph_seconds": round(float(np.median(mt)), 3)})
    print(rows[-1], flush=True)
(HERE / "data" / "probes.json").write_text(json.dumps(rows))
