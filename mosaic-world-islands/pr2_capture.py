"""Capture mosaic placements for the M2 before/after figures."""
from __future__ import annotations
import pickle, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))
from run_all import load_case, run  # noqa: E402

SPECS = [("world", 384, True), ("world", 384, False), ("world", 800, True)]
label = sys.argv[1]
out = {}
for case, budget, morph in SPECS:
    gdf, tc, gb = load_case(case, budget)
    res, elapsed = run(gdf, tc, gb, morph=morph)
    want = gdf["tiles"].to_numpy()
    got = res.regions_gdf["tile_count"].to_numpy()
    out[(case, budget, morph)] = dict(
        tiles=[(p, int(g)) for p, g in zip(res.tiles_gdf.geometry, res.tiles_gdf["geometry_id"])],
        want=want, got=got, elapsed=elapsed,
        names=[str(x) for x in gdf["name"]],
        geom=list(gdf.geometry),
    )
    print(f"[{label}] {case} b{budget} morph={morph} {elapsed:.1f}s short={int((got!=want).sum())}", flush=True)
with (HERE / f"placements_{label}.pkl").open("wb") as f:
    pickle.dump(out, f)
