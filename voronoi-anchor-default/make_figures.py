"""Regenerates followup_anchor.png (premorph with generator_anchor 0, 0.25 and 0.5) from the runs of
exploration-voronoi-followup, which holds the data and the full script.

Run from a carto-flow checkout (bundled data only):
    uv run python make_figures.py
"""

import runpy
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "exploration-voronoi-followup"
module = runpy.run_path(str(SOURCE / "make_figures.py"), run_name="followup")
module["anchor"]()
shutil.copy(SOURCE / "followup_anchor.png", HERE / "followup_anchor.png")
