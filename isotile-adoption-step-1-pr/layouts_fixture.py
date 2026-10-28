"""Writes tests/data/layouts.json from the outputs of layout_cases.py.

    python layouts_fixture.py <layouts_old.pkl> <phase_old.json> <phase_new.json> <output.json>

Per case: the placement metrics of the tactile-based code (tiles used, regions split over more than one block, mean and
largest distance of a region from its tiles in tile sizes). Per grid tiling: the range of the mean distance over six
shifts of the lattice relative to the 49 states, for the old and the new code together.
"""

from __future__ import annotations

import json
import pickle
import sys

old = pickle.load(open(sys.argv[1], "rb"))
phase_old = json.load(open(sys.argv[2]))
phase_new = json.load(open(sys.argv[3]))
keys = ("lattice_tiles", "assigned", "regions", "split", "disp_mean", "disp_max")
out = {
    "cases": {name: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items() if k in keys} for name, r in old.items()},
    "phase_range": {
        t: [round(min(phase_old[t] + phase_new[t]), 6), round(max(phase_old[t] + phase_new[t]), 6)] for t in phase_old
    },
}
json.dump(out, open(sys.argv[4], "w"), indent=2)
