"""Do the specific scrambled placements survive the linear normalisation?

Checks the three cases named in the world diagnosis: the tile nearest Jamaica
carried Senegal, the tile nearest Cyprus carried India, and Denmark's tile sat
in northern Canada.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run import CASES, _linear_build_cost_matrix  # noqa: E402

from carto_flow.symbol_cartogram import create_layout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import _assignment as M  # noqa: E402

WATCH = ["Jamaica", "Cyprus", "Puerto Rico", "Denmark", "Bahamas", "Trinidad and Tobago", "Iceland"]
out = []
loader = CASES["world"][0]
gdf = loader()
names = [str(x) for x in gdf["name"]]
gc = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])

for morph in (False, True):
    for variant in ("squared", "linear"):
        orig = M._build_cost_matrix
        if variant == "linear":
            M._build_cost_matrix = _linear_build_cost_matrix
        try:
            res = create_layout(gdf, tile_count="tiles", show_progress=False,
                                layout=MosaicLayout(morph=morph, hungarian_options=HungarianOptions()))
        finally:
            M._build_cost_matrix = orig
        tg = res.tiles_gdf
        cent = np.array([[p.centroid.x, p.centroid.y] for p in tg.geometry])
        gid = tg["geometry_id"].to_numpy().astype(int)
        print(f"\n=== world morph={morph} {variant} ===")
        for nm in WATCH:
            i = names.index(nm)
            d = np.hypot(cent[:, 0] - gc[i, 0], cent[:, 1] - gc[i, 1])
            j = int(np.argmin(d))
            # where does this region's OWN tile sit?
            own = np.where(gid == i)[0]
            own_km = (np.hypot(cent[own, 0] - gc[i, 0], cent[own, 1] - gc[i, 1]).min() / 1000
                      if len(own) else None)
            rec = dict(morph=morph, variant=variant, region=nm,
                       nearest_tile_owner=names[gid[j]], nearest_tile_km=float(d[j] / 1000),
                       own_tile_km=own_km, own_tiles=int(len(own)))
            out.append(rec)
            print(f"  {nm:22s} nearest tile -> {names[gid[j]]:22s} ({d[j]/1000:5.0f} km); "
                  f"its own {len(own)} tile(s) nearest at "
                  + (f"{own_km:.0f} km" if own_km is not None else "none placed"))
(HERE / "scramble_check.json").write_text(json.dumps(out, indent=1))
