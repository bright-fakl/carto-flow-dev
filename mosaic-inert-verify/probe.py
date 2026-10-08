"""Trace the connectivity-repair loop: per-iteration split/disconnected/gaps."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, "/home/fakl/carto-flow/visual_checks/mosaic-options-sweep")
import inputs as IN  # noqa: E402

case, morph = sys.argv[1], sys.argv[2] == "1"
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

loader, tile_count, group_by, tiling = IN.CASES[case]
gdf = loader()
hung = {}
for kv in sys.argv[3:]:
    k, v = kv.split("=")
    hung[k] = float(v) if "." in v else int(v)
layout = MosaicLayout(tiling=tiling, morph=morph, hungarian_options=HungarianOptions(**hung))
res = create_layout(gdf, tile_count=tile_count, group_by=group_by, layout=layout, show_progress=True)
