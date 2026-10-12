"""Writes data/tables.md: the new entry point against the deprecated ones on states and districts.

    NUMBA_NUM_THREADS=8 uv run python make_tables.py
"""
import warnings
from pathlib import Path

import numpy as np

from carto_flow import data
from carto_flow.flow_cartogram import LadderSpec, MorphOptions, create_flow_cartogram, morph_gdf, multiresolution_morph

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
INPUTS = {
    "states": data.load_us_census(population=True),
    "districts": data.load_us_census(population=True, level="congressional_district"),
}


def summary(c):
    e = c.get_errors()
    return f"{c.status.value}, {c.niterations} it, grid {c.options.grid.sx if c.options.grid is not None else c.options.grid_size}, mean {e.mean_error_pct:.3f} / max {e.max_error_pct:.2f} %"


def same(a, b):
    ga, gb = list(a.get_geometry()), list(b.get_geometry())
    return max(float(np.abs(np.array(x.bounds) - np.array(y.bounds)).max()) for x, y in zip(ga, gb, strict=True))


out = ["| input | call | result | largest bounds difference to the deprecated call |", "|---|---|---|---|"]
opts = MorphOptions(show_progress=False)
for name, gdf in INPUTS.items():
    old = morph_gdf(gdf, "Population", options=opts)
    new = create_flow_cartogram(gdf, "Population", options=opts)
    out.append(f"| {name} | `morph_gdf` (deprecated) | {summary(old)} | |")
    out.append(f"| {name} | `create_flow_cartogram` | {summary(new)} | {same(old, new):.3g} |")
    lad = MorphOptions(show_progress=False, grid_size=LadderSpec(min_resolution=128, levels=4))
    old = multiresolution_morph(gdf, "Population", min_resolution=128, levels=4, options=MorphOptions(show_progress=False))
    new = create_flow_cartogram(gdf, "Population", options=lad)
    out.append(f"| {name} | `multiresolution_morph(min_resolution=128, levels=4)` (deprecated) | {summary(old)} | |")
    out.append(f"| {name} | `create_flow_cartogram` with `LadderSpec(128, 4)` | {summary(new)} | {same(old, new):.3g} |")
    auto = create_flow_cartogram(gdf, "Population", options=MorphOptions(show_progress=False, grid_size="auto"))
    out.append(f"| {name} | `create_flow_cartogram` with `grid_size=\"auto\"` | {summary(auto)} | |")
(HERE / "data" / "tables.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
