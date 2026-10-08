"""Independent inertness check for HungarianOptions knobs.

Fingerprint is the FULL layout: per-tile region id, per-tile centre (full
float64 bytes), base_size, sizes, bounds.  Not a summary metric.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path("/home/fakl/carto-flow/visual_checks/mosaic-options-sweep")))
import inputs as IN  # noqa: E402


def full_fingerprint(res) -> str:
    h = hashlib.sha256()
    pos = np.array([t.position for t in res.transforms], dtype=np.float64)
    h.update(pos.tobytes())
    h.update(np.array([t.scale for t in res.transforms], dtype=np.float64).tobytes())
    h.update(np.asarray(res.sizes, dtype=np.float64).tobytes())
    h.update(np.float64(res.base_size).tobytes())
    h.update(np.asarray(res.bounds, dtype=np.float64).tobytes())
    for name in ("source_indices", "group_ids", "valid_mask"):
        v = getattr(res, name, None)
        h.update(b"|" + name.encode() + b"|")
        if v is not None:
            h.update(np.asarray(v).tobytes())
    m = res.metrics
    h.update(json.dumps({"iter": getattr(m, "iterations", None),
                         "alg": str(getattr(m, "algorithm", None))}).encode())
    return h.hexdigest()[:20]


def run(case, morph, hung):
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

    loader, tile_count, group_by, tiling = IN.CASES[case]
    gdf = loader()
    layout = MosaicLayout(tiling=tiling, morph=morph, hungarian_options=HungarianOptions(**hung))
    res = create_layout(gdf, tile_count=tile_count, group_by=group_by, layout=layout,
                        show_progress=False)
    return full_fingerprint(res)


if __name__ == "__main__":
    case, morph, param, values = sys.argv[1], sys.argv[2] == "1", sys.argv[3], sys.argv[4]
    out = {}
    for raw in values.split(","):
        v = float(raw) if "." in raw else int(raw)
        fp = run(case, morph, {param: v} if param != "-" else {})
        out[raw] = fp
        print(f"{case} morph={int(morph)} {param}={raw} -> {fp}", flush=True)
    print("IDENTICAL" if len(set(out.values())) == 1 else "DIFFERS", flush=True)
