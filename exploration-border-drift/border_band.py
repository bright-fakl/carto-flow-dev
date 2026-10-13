"""Border band count of dots carried along with a flow cartogram (#86), re-evaluated on the current code.

    NUMBA_NUM_THREADS=8 uv run python border_band.py [seed]

The test counts the dots inside a band (6 % of sqrt(area) wide) along the border of their own state and compares with
the number expected if the dots were uniform, as a binomial z-score summed over states.
"""
import json
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.data as examples
import carto_flow.flow_cartogram as flow
import carto_flow.proportional_cartogram as prop

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7

g = examples.load_us_census(population=True, poverty=True)
col = "Below Poverty Level"
dots = prop.generate_dot_density(g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=SEED)
owner = np.array([list(g.index).index(o) for o in dots["original_index"]])
landmarks = gpd.GeoSeries(list(dots.geometry), crs=g.crs)


def band_z(geoms, P, frac=0.06):
    obs = exp = var = 0.0
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
    return int(obs), float(exp), float((obs - exp) / np.sqrt(var))


def run(label, **kw):
    base = dict(area_scale=1e-6, snapshot_every=1, n_iter=400, show_progress=False)
    base.update(kw)
    cart = flow.create_flow_cartogram(g, "Population", landmarks=landmarks, options=flow.MorphOptions(**base))
    fin = cart.snapshots[-1]
    P = np.array([[p.x, p.y] for p in fin.landmarks])
    obs, exp, z = band_z(list(fin.geometry), P)
    inside = float(np.mean([shapely.contains(fin.geometry[owner[i]].buffer(0), shapely.Point(P[i])) for i in range(len(P))]))
    row = {"variant": label, "status": cart.status.value, "iterations": int(cart.niterations), "observed": obs, "expected": round(exp, 1), "z": round(z, 2), "inside_own_state": round(inside, 3)}
    print(row, flush=True)
    return row


if __name__ == "__main__":
    P0 = np.array([[p.x, p.y] for p in landmarks])
    obs, exp, z = band_z(list(g.geometry), P0)
    rows = [{"variant": "start", "status": "-", "iterations": 0, "observed": obs, "expected": round(exp, 1), "z": round(z, 2), "inside_own_state": 1.0}]
    print(rows[0])
    rows.append(run("defaults (grid 256, recompute_every 10)"))
    rows.append(run("grid 512", grid=512))
    rows.append(run("recompute_every 1", recompute_every=1))
    rows.append(run("grid 512, recompute_every 1", grid=512, recompute_every=1))
    rows.append(run("defaults, density_rasterization center", density_rasterization="center"))
    rows.append(run("defaults, adaptive_dt off", adaptive_dt=False))
    rows.append(run("defaults, dt 0.05", dt=0.05))
    (HERE / "data" / f"border_band_seed{SEED}.json").write_text(json.dumps(rows))
