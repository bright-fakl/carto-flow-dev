# Renders the same images with the ported GUI (isotile). Run in an environment with the ported GUI installed:
#   MPLBACKEND=Agg python render_new.py <output directory>
# Writes <case>_<mode>_strip.png, <case>_<mode>_export.png and <case>_export.svg for the 15 presets, the color modes
# uniform, aspect and coloring (the old mode index is gone).
import sys
from pathlib import Path

from isotile import IsohedralTiling, list_presets

from isohedral_tiling_ui import exports
from isohedral_tiling_ui.exports import Appearance

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for name in list_presets():
    tiling = IsohedralTiling.from_preset(name)
    for mode in ("uniform", "aspect", "coloring"):
        appearance = Appearance(mode)
        (out / f"{name}_{mode}_strip.png").write_bytes(exports.strip_png(tiling, appearance))
        (out / f"{name}_{mode}_export.png").write_bytes(exports.png_export(tiling, appearance, 100))
    (out / f"{name}_export.svg").write_text(exports.svg_export(tiling, Appearance("aspect"), 100))

# Tile polygons of the preview window, to draw the gap of the old tree preview at a larger scale.
import json

for name in ("tree", "puzzle_piece"):
    tiles = exports.strip_tiles(IsohedralTiling.from_preset(name))
    (out / f"{name}_window_tiles.json").write_text(json.dumps(tiles.outlines().tolist()))
