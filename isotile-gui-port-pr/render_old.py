# Renders the preview strips and exports of the GUI on carto-flow 2.0.0 and tactile 0.1.0 (isohedral-tiling-ui a1a706f).
# Run in an environment with carto-flow 2.0.0, tactile 0.1.0 and the old GUI installed:
#   MPLBACKEND=Agg python render_old.py <output directory>
# Writes <case>_<mode>_strip.png (the strip of the preview), <case>_<mode>_export.png (the Medium PNG export) and
# <case>_export.svg for the 15 presets, the color modes uniform, aspect and index.
import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
from carto_flow.symbol_cartogram.tiling import IsohedralTiling

from isohedral_tiling_ui.components.preview_strip import PreviewStrip
from isohedral_tiling_ui.state import TilingState

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
state = TilingState()
strip = PreviewStrip(state=state)
state.grid_size = "Medium"
for name in IsohedralTiling.list_presets():
    state.load_preset(name)
    for mode in ("uniform", "aspect", "index"):
        state.face_color_mode = mode
        (out / f"{name}_{mode}_strip.png").write_bytes(strip._render_strip_png())
        (out / f"{name}_{mode}_export.png").write_bytes(strip._generate_png_export().getvalue())
    state.face_color_mode = "aspect"
    (out / f"{name}_export.svg").write_text(strip._generate_svg_export().getvalue())

# Tile polygons of the preview window, to draw the gap of the tree preset at a larger scale.
import json

for name in ("tree", "puzzle_piece"):
    t = IsohedralTiling.from_preset(name)
    result = t.generate(bounds=(-1, -0.3, 1, 0.3), n_tiles=100, margin=0.25, compute_adjacency=False)
    polygons = [[list(p) for p in zip(*poly.exterior.xy, strict=False)] for poly in result.polygons]
    (out / f"{name}_window_tiles.json").write_text(json.dumps(polygons))
