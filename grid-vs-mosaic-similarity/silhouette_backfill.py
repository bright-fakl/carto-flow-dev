"""Backfill silhouette + morphed-reference numbers for runs that predate them.

`run.py` saved `placements/<name>.pkl` (assigned tile polygons, per-region tile
lists, lattice adjacency, tile size) for every comparison run, which is enough
to compute both silhouette references and the secondary displacement without
re-running any layout.

Two silhouette references are emitted per run:

* ``silhouette``          -- vs the ORIGINAL input union.  The only
  cross-layout-comparable reference, and the one matching the visual criterion
  "does the tilegram still resemble the US".  This is the headline.
* ``silhouette_working``  -- vs the footprint the layout actually tiled
  against: the MORPHED union for mosaic morph=True runs, the original union
  otherwise.  Internal fidelity only; NOT comparable across layouts, because
  the runs aim at different shapes.

For morph=True runs, displacement is also recomputed from the morphed
centroids (``*_vs_working``).  The headline displacement from the original
centroids stays in ``results.jsonl`` untouched.

Results are appended a line at a time to `silhouette.jsonl`; join on `name`.
Sweep runs saved no pickle and are not covered here.

    PYTHONPATH=<checkout of origin/main>/src uv run python \
        visual_checks/grid-vs-mosaic-similarity/silhouette_backfill.py
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from metrics import _pct, build_study_union, silhouette_metrics  # noqa: E402
from run import morph_reference  # noqa: E402

OUT = HERE / "silhouette.jsonl"


def main():
    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 150)).astype(int)
    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)

    gdfs = {"states": states, "districts": districts}
    unions = {k: build_study_union(v) for k, v in gdfs.items()}
    centroids = {
        k: np.array([[g.centroid.x, g.centroid.y] for g in v.geometry]) for k, v in gdfs.items()
    }
    # morph references, keyed the same way run.py keys them
    refs = {
        "states_uniform": lambda: morph_reference("states_uniform", states, np.ones(len(states))),
        "states": lambda: morph_reference("states", states, states["tiles"].to_numpy()),
        "districts": lambda: morph_reference("districts", districts, np.ones(len(districts))),
    }

    def case_of(name):
        if name.startswith("districts"):
            return "districts", "districts"
        if name.startswith("states_uniform"):
            return "states_uniform", "states"
        return "states", "states"

    OUT.write_text("")
    for pkl in sorted((HERE / "placements").glob("*.pkl")):
        name = pkl.stem
        case, gkey = case_of(name)
        with pkl.open("rb") as f:
            pay = pickle.load(f)
        polys = pay["polygons"]
        keys = sorted(polys)
        centres = np.array([[polys[t].centroid.x, polys[t].centroid.y] for t in keys])
        occ_polys = [polys[t] for t in keys]

        rec = {"name": name, "silhouette": silhouette_metrics(occ_polys, centres, unions[gkey])}

        is_morph = "mosaic_morph" in name
        if is_morph:
            ref = refs[case]()
            rec["silhouette_working"] = silhouette_metrics(occ_polys, centres, ref["working_union"])
            rec["silhouette_working_is_original"] = False
            # displacement from the morphed centroids
            block = np.array(
                [
                    np.mean([[polys[t].centroid.x, polys[t].centroid.y] for t in tiles], axis=0)
                    if tiles
                    else [np.nan, np.nan]
                    for tiles in pay["tile_of_region"]
                ]
            )
            ok = ~np.isnan(block[:, 0])
            dm = np.linalg.norm(block[ok] - ref["working_centroids"][ok], axis=1) / pay["tile_size"]
            do = np.linalg.norm(block[ok] - centroids[gkey][ok], axis=1) / pay["tile_size"]
            rec["displacement_vs_working"] = {
                "median_tiles_vs_working": _pct(dm, 50),
                "p90_tiles_vs_working": _pct(dm, 90),
                "median_tiles_check_original": _pct(do, 50),
            }
        else:
            rec["silhouette_working"] = rec["silhouette"]
            rec["silhouette_working_is_original"] = True

        with OUT.open("a") as f:
            f.write(json.dumps(rec) + "\n")
            f.flush()
        sw = rec["silhouette_working"]
        print(
            f"[sil] {name:38s} iou_vs_original={rec['silhouette']['iou_aligned']:.3f} "
            f"iou_vs_working={sw['iou_aligned']:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
