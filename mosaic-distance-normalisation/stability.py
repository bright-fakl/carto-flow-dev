"""Repeat the key world cells to separate a real integrity change from
flow-morph run-to-run noise (morph=True only; morph=False is deterministic)."""
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

gdf = CASES["world"][0]()
out = []
for morph, reps in ((True, 4), (False, 2)):
    for dw in (1.0, 2.0, 4.0):
        for variant in ("squared", "linear"):
            ncs, ods = [], []
            for _ in range(reps):
                orig = M._build_cost_matrix
                if variant == "linear":
                    M._build_cost_matrix = _linear_build_cost_matrix
                try:
                    res = create_layout(gdf, tile_count="tiles", show_progress=False,
                                        layout=MosaicLayout(morph=morph,
                                                            hungarian_options=HungarianOptions(distance_weight=dw)))
                finally:
                    M._build_cost_matrix = orig
                am = res.metrics.algorithm
                ncs.append(int(am.n_noncontiguous_regions))
                gc = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
                tg = res.tiles_gdf
                cent = np.array([[p.centroid.x, p.centroid.y] for p in tg.geometry])
                gid = tg["geometry_id"].to_numpy().astype(int)
                ods.append(float(np.median(np.hypot(cent[:, 0] - gc[gid, 0], cent[:, 1] - gc[gid, 1])) / 1000))
            rec = dict(morph=morph, dw=dw, variant=variant, noncontig=ncs,
                       owner_km=[round(x) for x in ods])
            out.append(rec)
            print(f"world morph={int(morph)} dw={dw} {variant:8s}: noncontig={ncs}  owner_km={rec['owner_km']}", flush=True)
(HERE / "stability.json").write_text(json.dumps(out, indent=1))
