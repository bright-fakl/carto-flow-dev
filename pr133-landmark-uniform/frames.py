"""Smoothness and cost of get_landmarks(iteration=t, uniform=True) over the frames of a morph (PR 133).

    NUMBA_NUM_THREADS=8 uv run python frames.py
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
d = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=0)
owner = np.array([list(g.index).index(o) for o in d["original_index"]])
c = flow.create_flow_cartogram(g, "Population", landmarks=gpd.GeoSeries(list(d.geometry), crs=g.crs), options=flow.MorphOptions(area_scale=1e-6, show_progress=False, snapshot_every=4))
snaps = c.snapshots.snapshots
times, deltas, carried = [], [], []
for s in snaps:
    P = shapely.get_coordinates(np.asarray(s.landmarks, dtype=object))
    t = time.perf_counter()
    Q = shapely.get_coordinates(np.asarray(c.get_landmarks(iteration=s.iteration, uniform=True), dtype=object))
    times.append(time.perf_counter() - t)
    deltas.append(Q - P)
    carried.append(P)
D, C = np.array(deltas), np.array(carried)
width = np.array([np.sqrt(shapely.area(snaps[-1].geometry[o])) for o in owner])
sec = np.linalg.norm(D[2:] - 2 * D[1:-1] + D[:-2], axis=2) / width[None, :]
inc = np.linalg.norm(D[1:] - D[:-1], axis=2)
mot = np.maximum(np.linalg.norm(C[1:] - C[:-1], axis=2), 1e-12)
active = np.linalg.norm(D, axis=2).max(axis=0) > 1e-6 * width
res = {"frames": len(snaps), "first_call_seconds": round(times[0], 3), "later_calls_seconds_median": round(float(np.median(times[1:])), 3),
       "second_difference_median_pct": round(float(100 * np.median(sec[:, active])), 3), "second_difference_p95_pct": round(float(100 * np.percentile(sec[:, active], 95)), 3),
       "increment_over_motion_median": round(float(np.median((inc / mot)[:, active])), 3), "increment_over_motion_p95": round(float(np.percentile((inc / mot)[:, active], 95)), 3),
       "final_correction_median_pct": round(float(100 * np.median(np.linalg.norm(D[-1], axis=1) / width)), 3)}
print(res)
(HERE / "data" / "frames.json").write_text(json.dumps(res))
