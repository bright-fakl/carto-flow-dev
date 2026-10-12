"""Writes data/tables.md: the automatic ladder and the warnings on states, districts and (if COUNTIES_PARQUET is set) counties.

    NUMBA_NUM_THREADS=8 uv run python make_tables.py
"""
import os
import warnings
from pathlib import Path

import geopandas as gpd

from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf, multiresolution_morph
from carto_flow.flow_cartogram.grid import build_multilevel_grids
from carto_flow.flow_cartogram.resolution import auto_levels, auto_start, check_resolution

HERE = Path(__file__).resolve().parent
INPUTS = {
    "states": (data.load_us_census(population=True), "Population", {}),
    "districts": (data.load_us_census(population=True, level="congressional_district"), "Population", {}),
}
if os.environ.get("COUNTIES_PARQUET"):
    INPUTS["counties"] = (gpd.read_parquet(os.environ["COUNTIES_PARQUET"]), "total_votes", {"area_scale": 1e-6})

out = ["## Smallest target region in cells and the automatic ladder\n", "| input | regions | 64 | 128 | 256 | 512 | auto min_resolution | auto levels |", "|---|---|---|---|---|---|---|---|"]
for name, (gdf, col, _) in INPUTS.items():
    t = gdf[col].to_numpy(float)
    t = gdf.area.sum() * t / t.sum()
    cells = []
    for n in (64, 128, 256, 512):
        g = build_multilevel_grids(gdf.total_bounds, n, 1, margin=0.5, square=True)[0]
        cells.append(f"{t.min() / (g.dx * g.dy):.3g}")
    start = auto_start(gdf.total_bounds, t)
    out.append(f"| {name} | {len(gdf)} | " + " | ".join(cells) + f" | {start} | {auto_levels(start)} |")

out += ["\n## Warnings\n", "| input | min_resolution, levels | warning |", "|---|---|---|"]
for name, (gdf, col, _) in INPUTS.items():
    t = gdf[col].to_numpy(float)
    t = gdf.area.sum() * t / t.sum()
    for n, lv in ((64, 1), (96, 4), (128, 5), (512, 3)):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            check_resolution(gdf.total_bounds, t, n, lv)
        out.append(f"| {name} | {n}, {lv} | {w[0].message if w else 'none'} |")

out += ["\n## Single-resolution morph (morph_gdf), warning for the grid in use\n", "| input | grid_size | warning |", "|---|---|---|"]
for name, (gdf, col, extra) in INPUTS.items():
    for n in (256, 512):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            morph_gdf(gdf, col, options=MorphOptions(show_progress=False, grid_size=n, n_iter=10, recompute_every=5, **extra))
        msg = next((str(x.message) for x in w if str(x.message).startswith("Grid resolution")), "none")
        out.append(f"| {name} | {n} | {msg} |")

out += ["\n## Automatic ladder, default options\n", "| input | levels run (grid, status, iterations) | mean / max error % (reported) | warning |", "|---|---|---|---|"]
for name, (gdf, col, extra) in INPUTS.items():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = multiresolution_morph(gdf, col, min_resolution="auto", levels="auto", options=MorphOptions(show_progress=False, **extra))
    a = r.get_errors()
    msg = next((str(x.message) for x in w if str(x.message).startswith("Grid resolution")), "none")
    out.append(f"| {name} | {r.options.grid.sx}, {r.status.value}, {r.niterations} | {a.mean_error_pct:.2f} / {a.max_error_pct:.1f} | {msg} |")
(HERE / "data" / "tables.md").write_text("\n".join(out) + "\n")
