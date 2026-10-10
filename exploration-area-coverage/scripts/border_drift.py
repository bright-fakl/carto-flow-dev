"""Issue #86: border-band z-score of dots carried along with the morph, for center sampling vs coverage.

Usage: NUMBA_NUM_THREADS=4 uv run python border_drift.py   -> data/border_drift.pkl
The statistic is the one in the issue (band of 6 % of sqrt(area) inside each state, binomial z summed over states).
"""

import pickle
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely

import carto_flow.data as examples
import carto_flow.flow_cartogram as flow
import carto_flow.proportional_cartogram as prop

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent.parent

g = examples.load_us_census(population=True, poverty=True)
col = "Below Poverty Level"
dots = prop.generate_dot_density(
    g, columns=[col], n_dots=round(g[col].max() / 25000), normalization="maximum", seed=7
)
owner = np.array([list(g.index).index(o) for o in dots["original_index"]])
P0 = np.array([[p.x, p.y] for p in dots.geometry])


def border_band_z(P, geoms, frac=0.06):
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


out = HERE / "data" / "border_drift.pkl"
res = {"start": border_band_z(P0, list(g.geometry))}
print("start", res["start"])
for grid in (256, 512):
    for re in (10, 1):
        for ro in (0.01, None):
            for cov in (None, 4, "exact"):
                name = f"g{grid}|re{re}|ro{ro}|{cov or 'center'}"
                opts = flow.MorphOptions.preset_balanced().copy_with(
                    area_scale=1e-6,
                    n_iter=400,
                    show_progress=False,
                    grid_size=grid,
                    recompute_every=re,
                    refresh_on_rise=ro,
                    density_coverage=cov,
                )
                cart = flow.morph_gdf(g, "Population", landmarks=gpd.GeoSeries(list(dots.geometry), crs=g.crs), options=opts)
                fin = cart.latest
                P = np.array([[p.x, p.y] for p in fin.landmarks])
                obs, exp, z = border_band_z(P, list(fin.geometry))
                res[name] = dict(obs=obs, exp=exp, z=z, status=str(cart.status.value), it=cart.niterations)
                print(name, res[name], flush=True)
                pickle.dump(res, open(out, "wb"))
