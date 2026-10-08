import json
from pathlib import Path

import numpy as np
import shapely

base = Path("/home/fakl/carto-flow/visual_checks/pr-mosaic-performance/bitcheck")
for cfg in ["states_morph", "districts_morph", "districts_grouped_morph"]:
    b = json.loads((base / "before" / f"{cfg}.json").read_text())
    a = json.loads((base / "after" / f"{cfg}.json").read_text())
    ts_b = b["metrics"]["algorithm"]["tile_size"]
    ts_a = a["metrics"]["algorithm"]["tile_size"]
    rel = abs(ts_a - ts_b) / ts_b
    wkb_b = json.loads((base / "before" / f"{cfg}.wkb.json").read_text())
    wkb_a = json.loads((base / "after" / f"{cfg}.wkb.json").read_text())
    geoms_b = [shapely.from_wkb(bytes.fromhex(w)) for w in wkb_b]
    geoms_a = [shapely.from_wkb(bytes.fromhex(w)) for w in wkb_a]
    maxdiff = 0.0
    for gb, ga in zip(geoms_b, geoms_a):
        cb = shapely.get_coordinates(gb)
        ca = shapely.get_coordinates(ga)
        if cb.shape == ca.shape:
            d = float(np.max(np.abs(cb - ca))) if cb.size else 0.0
            maxdiff = max(maxdiff, d)
        else:
            maxdiff = float("inf")
    others_b = {k: v for k, v in b["metrics"]["algorithm"].items() if k != "tile_size"}
    others_a = {k: v for k, v in a["metrics"]["algorithm"].items() if k != "tile_size"}
    print(cfg, "tile_size_rel_diff", rel, "max_coord_diff", maxdiff, "other_metrics_match", others_b == others_a)
