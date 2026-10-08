"""min_one_tile_per_region: off (must equal the PR2 baseline) vs on."""
from __future__ import annotations
import json, pickle, sys, time, warnings
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))
from run_all import load_case, fingerprint, integrity, append  # noqa: E402
from carto_flow.symbol_cartogram import create_layout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout  # noqa: E402

SPECS = [("world", 384), ("world", 800), ("africa", 150), ("world_mainland", 384),
         ("states", 0), ("districts", 0)]
FIGS = {("world", 384, True), ("world", 384, False)}
placements = {}
for case, budget in SPECS:
    for morph in (True, False):
        gdf, tc, gb = load_case(case, budget)
        for flag in (False, True):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                t0 = time.perf_counter()
                res = create_layout(gdf, tile_count=tc, group_by=gb, show_progress=False,
                                    layout=MosaicLayout(morph=morph, min_one_tile_per_region=flag))
                el = time.perf_counter() - t0
            msgs = [str(x.message) for x in w if "received no tile" in str(x.message)]
            rec = dict(mode="pr3", case=case, budget=budget, morph=morph, seeded=flag,
                       wall_clock_s=el, fingerprint=fingerprint(res, len(gdf)),
                       warning=msgs[0] if msgs else None, **integrity(res, gdf, tc))
            append(rec)
            print(f"[pr3] {case} b{budget} morph={int(morph)} seeded={int(flag)} {el:5.1f}s "
                  f"fp={rec['fingerprint']} short={rec['n_short']} zero={rec['n_zero']} "
                  f"noncontig={rec['n_noncontiguous_regions']} split={rec['n_split_groups']} "
                  f"warn={'yes' if msgs else 'no'}", flush=True)
            if (case, budget, morph) in FIGS:
                want = gdf["tiles"].to_numpy()
                placements[(case, budget, morph, flag)] = dict(
                    tiles=[(p, int(g)) for p, g in zip(res.tiles_gdf.geometry, res.tiles_gdf["geometry_id"])],
                    want=want, got=res.regions_gdf["tile_count"].to_numpy(), elapsed=el,
                    names=[str(x) for x in gdf["name"]], geom=list(gdf.geometry))
with (HERE / "placements_pr3.pkl").open("wb") as f:
    pickle.dump(placements, f)
print("PR3DONE")
