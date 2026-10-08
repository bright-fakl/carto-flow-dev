"""`spacing` does not reach the metric set: check what it does reach.

The assignment fingerprint and every fidelity metric are identical across
spacing values (see results.jsonl).  ``spacing`` only divides each tile's
Transform scale by ``1 + spacing`` (mosaic ``_build_transforms``), i.e. it
shrinks the drawn symbol inside an unchanged tile.  This script measures that
scale and draws the result.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from shapely import affinity

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import inputs as IN
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

VALUES = [0.0, 0.05, 0.2, 0.5]
gdf = IN.load_states()
rows = []
fig, axes = plt.subplots(1, len(VALUES), figsize=(4 * len(VALUES), 4))
for ax, sp in zip(axes, VALUES):
    r = create_layout(gdf, layout=MosaicLayout(tiling="hexagon", morph=False, spacing=sp), show_progress=False)
    canon = r.tiling_result.canonical_tile
    scales = [t.scale for t in r.transforms]
    area = float(np.mean([canon.area * s * s for s in scales]))
    rows.append(
        {
            "spacing": sp,
            "mean_transform_scale": float(np.mean(scales)),
            "mean_symbol_area": area,
            "tile_size": float(r.tiling_result.tile_size),
            "tiles_gdf_area": float(sum(g.area for g in r.tiles_gdf.geometry)),
        }
    )
    for t in r.transforms:
        g = affinity.scale(canon, xfact=t.scale, yfact=t.scale, origin=(0, 0))
        g = affinity.translate(g, xoff=t.position[0], yoff=t.position[1])
        ax.fill(*g.exterior.xy, fc="#4477aa", ec="w", lw=0.4)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(f"spacing={sp}\ntransform scale = {np.mean(scales):.3f}")
a0 = rows[0]["mean_symbol_area"]
for row in rows:
    row["area_ratio_vs_0"] = row["mean_symbol_area"] / a0
    row["predicted_1_over_1plus_s_sq"] = 1.0 / (1 + row["spacing"]) ** 2
fig.suptitle(
    "spacing: symbol scale only (states_uniform, morph=False) -- tile size, centres and assignment unchanged"
)
fig.tight_layout()
fig.savefig(HERE / "spacing_symbols.png", dpi=120)
(HERE / "spacing_check.json").write_text(json.dumps(rows, indent=2))
for row in rows:
    print(row)
