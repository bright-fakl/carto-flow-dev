"""Writes data/tables.md: a ladder with n_iter per level (list of options) against n_iter as the total (single options).

    COUNTIES_PARQUET=counties_prepared.parquet NUMBA_NUM_THREADS=8 uv run python make_tables.py
"""
import copy
import math
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "exploration-multires-stall"))
from stall_levels import CASES, COUNTIES, DISTRICTS, STATES, values  # noqa: E402

from carto_flow.flow_cartogram import CartogramWorkflow, LadderSpec, MorphOptions  # noqa: E402

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
rows = ["| case | n_iter | per level (list of options) | total (single options) |", "|---|---|---|---|"]
for case, (kind, dist, start, fin) in CASES.items():
    if kind == "counties" and COUNTIES is None:
        continue
    gdf = {"states": STATES, "districts": DISTRICTS, "counties": COUNTIES}[kind][["geometry"]].copy()
    if kind == "counties":
        gdf["v"] = COUNTIES["total_votes"].to_numpy(float)
        extra = {"area_scale": 1e-6}
    else:
        gdf["v"] = values({"states": STATES, "districts": DISTRICTS}[kind], dist)
        extra = {}
    levels = int(math.log2(fin // start)) + 1
    for n_iter in (500,):
        out = []
        for mode in ("list", "total"):
            base = MorphOptions(show_progress=False, mean_tol=0.01, max_tol=0.03, n_iter=n_iter, grid=LadderSpec(start, levels), **extra)
            wf = CartogramWorkflow(gdf, "v", options=base)
            t = time.perf_counter()
            if mode == "list":
                opts = [copy.deepcopy(base) for _ in range(levels)]
                wf.morph_multiresolution(min_resolution=start, levels=levels, options=opts)
            else:
                wf.morph()
            wall = time.perf_counter() - t
            res = list(wf)[1:]
            geoms = list(wf.last.get_geometry())
            a = np.array([g.area for g in geoms])
            err = np.abs(a / (gdf["v"].to_numpy(float) / gdf["v"].sum() * a.sum()) - 1) * 100
            lv = ", ".join(f"{r.options.grid.sx} {r.status.value[:4]} {r.niterations}" for r in res)
            out.append(f"{wf.last.status.value}, {sum(r.niterations for r in res)} it, {wall:.1f} s, mean {err.mean():.2f} / max {err.max():.1f} %: {lv}")
        rows.append(f"| {case} | {n_iter} | {out[0]} | {out[1]} |")
(HERE / "data" / "tables.md").write_text("\n".join(rows) + "\n")
print("\n".join(rows))
