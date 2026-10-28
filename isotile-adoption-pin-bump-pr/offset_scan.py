"""Scan: 15 presets x 6 offsets x states (grid, and mosaic with morph=False).

    python offset_scan.py <label> <out.json> [straight]

``straight`` forces fill_region to outline="straight" (new isotile only). Per case: lattice tiles, mean distance of a
region from its tiles in tile sizes, and for the mosaic layout the non-contiguous regions and the unassigned core tiles.
"""

import functools
import json
import sys
import warnings

import numpy as np

warnings.simplefilter("ignore")
import isotile

if len(sys.argv) > 3 and sys.argv[3] == "straight":
    orig = isotile.IsohedralTiling.fill_region

    @functools.wraps(orig)
    def straight(self, *a, **kw):
        kw.setdefault("outline", "straight")
        return orig(self, *a, **kw)

    isotile.IsohedralTiling.fill_region = straight

from carto_flow.data import load_us_census
from carto_flow.symbol_cartogram import create_layout
from carto_flow.symbol_cartogram.layouts.grid import GridBasedLayout
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout
from carto_flow.symbol_cartogram.tiling import IsohedralTiling

PHASES = [(0.0, 0.0), (0.25, 0.5), (0.5, 0.25), (0.75, 0.75), (0.4, 0.9), (0.9, 0.1)]
gdf = load_us_census(population=True).reset_index(drop=True)
pop = gdf["Population"].to_numpy(dtype=float)
gdf["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 150)).astype(int)
cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
out = {}
for name in IsohedralTiling.list_presets():
    for off in PHASES:
        for kind in ("grid", "mosaic"):
            tiling = IsohedralTiling.from_preset(name).with_offset(off)
            if kind == "grid":
                res = create_layout(gdf, layout=GridBasedLayout(tiling=tiling), show_progress=False)
            else:
                res = create_layout(gdf, tile_count="tiles", layout=MosaicLayout(tiling=tiling, morph=False), show_progress=False)
            tr = res.tiling_result
            a = np.asarray(res.assignments)
            if kind == "grid":
                d = np.hypot(*(tr.centers[a] - cent).T) / tr.tile_size
                extra = {}
            else:
                import shapely

                per = {}
                for t, g in zip(a.tolist(), np.asarray(res.source_indices).tolist(), strict=True):
                    per.setdefault(g, []).append(t)
                d = np.array(
                    [
                        np.hypot(*(np.array(shapely.union_all([tr.polygons[t] for t in ts]).centroid.coords[0]) - cent[g]))
                        / tr.tile_size
                        for g, ts in per.items()
                    ]
                )
                alg = res.metrics.algorithm
                extra = {"noncontiguous": int(alg.n_noncontiguous_regions), "unassigned_core": int(alg.n_unassigned_core_tiles)}
            out[f"{name}|{kind}|{off[0]}|{off[1]}"] = {"lattice": int(tr.n_tiles), "mean": float(d.mean()), **extra}
        print(sys.argv[1], name, off, flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
