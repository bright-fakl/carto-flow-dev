"""Before/after placement figures for the distance-normalisation variant.

Each tile is coloured by how far it sits from the centroid of the region that
owns it, in tile widths, on a shared scale within a figure -- the statistic the
change targets.  Dark tiles are symbols placed a long way from the land they
represent.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run import CASES, _linear_build_cost_matrix  # noqa: E402

from carto_flow.symbol_cartogram import create_layout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import _assignment as M  # noqa: E402

CMAP = "YlGnBu"
SPECS = [("world", True), ("world", False), ("districts", False), ("states", False)]


def place(case, morph, variant):
    loader, tile_count, group_by, tiling = CASES[case]
    gdf = loader()
    orig = M._build_cost_matrix
    if variant == "linear":
        M._build_cost_matrix = _linear_build_cost_matrix
    try:
        res = create_layout(gdf, tile_count=tile_count, group_by=group_by, show_progress=False,
                            layout=MosaicLayout(tiling=tiling, morph=morph,
                                                hungarian_options=HungarianOptions()))
    finally:
        M._build_cost_matrix = orig
    gc = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
    tg = res.tiles_gdf
    cent = np.array([[p.centroid.x, p.centroid.y] for p in tg.geometry])
    gid = tg["geometry_id"].to_numpy().astype(int)
    ts = float(res.metrics.algorithm.tile_size)
    d = np.hypot(cent[:, 0] - gc[gid, 0], cent[:, 1] - gc[gid, 1]) / ts
    return gdf, tg, d, np.median(d), np.percentile(d, 90)


for case, morph in SPECS:
    out = HERE / f"norm_{case}_morph{int(morph)}.png"
    panels = [(v, *place(case, morph, v)) for v in ("squared", "linear")]
    vmax = max(np.percentile(p[3], 97) for p in panels)
    norm = Normalize(0, vmax)
    fig, axes = plt.subplots(2, 1, figsize=(15, 13))
    for ax, (variant, gdf, tg, d, med, p90) in zip(axes, panels):
        gdf.plot(ax=ax, color="#f1f3f5", edgecolor="white", linewidth=0.2)
        tg.plot(ax=ax, color=plt.get_cmap(CMAP)(norm(d)), edgecolor="white", linewidth=0.2)
        label = "squared distance / max squared (current)" if variant == "squared" \
            else "linear distance / max linear (variant)"
        ax.set_title(f"{case}, morph={morph} — {label}\n"
                     f"tile-to-owning-region displacement: median {med:.2f} tiles, "
                     f"90th percentile {p90:.2f} tiles", fontsize=10)
        ax.set_axis_off()
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=CMAP), ax=axes, fraction=0.025, pad=0.01)
    cb.set_label("distance from tile to its region's centroid (tile widths)", fontsize=9)
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out, flush=True)
