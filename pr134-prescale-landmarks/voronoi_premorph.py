"""The Voronoi cartogram of the 52 US regions (with Alaska, Hawaii and Puerto Rico) with and without a pre-scaled premorph (PR 134).

    NUMBA_NUM_THREADS=8 uv run python voronoi_premorph.py
"""
import json
import time
import warnings
from pathlib import Path

import numpy as np

import carto_flow.flow_cartogram as flow
import carto_flow.voronoi_cartogram as vor
from carto_flow import data

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
g = data.load_us_census(population=True, contiguous_only=False).reset_index(drop=True)
w = g["Population"].to_numpy(float)
base = flow.MorphOptions.preset_balanced().copy_with(n_iter=400, show_progress=False)
cases = {
    "premorph=True, VoronoiOptions.prescale_components=True (cascades)": (True, True),
    "premorph=MorphOptions(prescale_components=False), Voronoi flag on (the behavior before)": (base.copy_with(prescale_components=False), True),
    "premorph=True, no pre-scaling": (True, False),
}
rows = []
for name, (premorph, flag) in cases.items():
    t = time.perf_counter()
    res = vor.create_voronoi_cartogram(g, weights="Population", premorph=premorph, options=vor.VoronoiOptions(prescale_components=flag))
    sec = time.perf_counter() - t
    pm = res.premorph
    e = pm.get_errors()
    a = np.array([x.area for x in res.to_geodataframe().geometry])
    err = np.abs(a / (w / w.sum() * a.sum()) - 1) * 100
    rows.append({"case": name, "premorph_iterations": int(pm.niterations), "premorph_mean_max_pct": [round(e.mean_error_pct, 1), round(e.max_error_pct, 1)], "cells_mean_max_pct": [round(float(err.mean()), 2), round(float(err.max()), 1)], "seconds": round(sec, 1)})
    print(rows[-1], flush=True)
lines = ["| case | premorph iterations | premorph mean / max error % | Voronoi cell area error mean / max % | seconds |", "|---|---|---|---|---|"]
lines += [f"| {r['case']} | {r['premorph_iterations']} | {r['premorph_mean_max_pct'][0]} / {r['premorph_mean_max_pct'][1]} | {r['cells_mean_max_pct'][0]} / {r['cells_mean_max_pct'][1]} | {r['seconds']} |" for r in rows]
(HERE / "data" / "voronoi.md").write_text("\n".join(lines) + "\n")
