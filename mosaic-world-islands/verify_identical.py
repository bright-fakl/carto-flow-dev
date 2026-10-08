"""Bit-identity check for the contiguity pre-check patch.

Runs the same configurations twice (once per checkout state) and writes a
fingerprint per configuration.  The fingerprint is the full per-region set of
assigned tile centroids plus the calibrated tile size, so equal fingerprints
mean an identical placement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))

from run_all import fingerprint, load_case, run  # noqa: E402

CONFIGS = [
    ("world", 800),
    ("districts", 0),
    ("states", 0),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    import carto_flow
    out = {"_carto_flow": carto_flow.__file__}
    for case, budget in CONFIGS:
        for morph in (True, False):
            gdf, tc, gb = load_case(case, budget)
            res, elapsed = run(gdf, tc, gb, morph=morph)
            am = res.metrics.algorithm
            key = f"{case}_b{budget}_morph{int(morph)}"
            out[key] = dict(
                fingerprint=fingerprint(res, len(gdf)),
                wall_clock_s=round(elapsed, 2),
                tile_size=am.tile_size,
                noncontig=am.n_noncontiguous_regions,
                split_groups=am.n_split_groups,
                regions_correct=am.regions_correct,
                unassigned_core=am.n_unassigned_core_tiles,
            )
            print(f"[{a.label}] {key} {elapsed:6.1f}s fp={out[key]['fingerprint']}", flush=True)
    (HERE / f"verify_{a.label}.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
