"""Dump mosaic layout output (serialized layout + styled geometry) for bit-identity comparison.

Writes .json (result.serialize() + metrics) and .wkb (styled tile geometry) per
config under visual_checks/pr-mosaic-performance/bitcheck/{before,after}/.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

sys.path.insert(0, "src")

SUBDIR = os.environ.get("PROFILE_SUBDIR", "after")
OUT = Path(f"/home/fakl/carto-flow/visual_checks/pr-mosaic-performance/bitcheck/{SUBDIR}")
OUT.mkdir(parents=True, exist_ok=True)


def dump(name, gdf, **kwargs):
    import shapely

    import carto_flow.symbol_cartogram.layouts.mosaic as mosaic_mod
    from carto_flow.symbol_cartogram.api import create_layout

    layout = mosaic_mod.MosaicLayout(morph=kwargs.pop("morph", True))
    result = create_layout(gdf, "Population", layout=layout, show_progress=False, **kwargs)

    serialized = result.serialize()

    metrics = result.metrics
    metrics_d = asdict(metrics) if is_dataclass(metrics) else (dict(metrics.__dict__) if metrics is not None else {})
    serialized["metrics"] = metrics_d

    (OUT / f"{name}.json").write_text(json.dumps(serialized, sort_keys=True, default=str))

    cart = result.style()
    geoms = list(cart.symbols.geometry)
    wkb_hex = [shapely.to_wkb(g).hex() for g in geoms]
    (OUT / f"{name}.wkb.json").write_text(json.dumps(wkb_hex))
    print(f"{name}: {len(geoms)} geoms, metrics={metrics_d}")


if __name__ == "__main__":
    from carto_flow.data import load_us_census, load_us_states

    states = load_us_states()
    if "Population" not in states.columns:
        states = load_us_census(level="state", population=True)
    districts = load_us_census(level="congressional_district", population=True)

    dump("states_morph", states, morph=True)
    dump("states_nomorph", states, morph=False)
    dump("districts_morph", districts, morph=True)
    dump("districts_nomorph", districts, morph=False)
    dump("districts_grouped_morph", districts, morph=True, group_by="State Name")
    dump("districts_grouped_nomorph", districts, morph=False, group_by="State Name")
    print("done")
