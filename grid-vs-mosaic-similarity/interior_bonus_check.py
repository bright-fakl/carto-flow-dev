"""Gating check for changing mosaic's `interior_bonus` default from 0.5 to 2.0.

The concern this exists to test: in the earlier sweep `interior_bonus=2.0`
improved adjacency, displacement and direction across the multi-tile and
districts cases at morph=True, but at one tile per region with morph=False it
was the worst value probed (adjacency 0.523).  `morph` is a user-facing
option, so a default that is good with it and bad without it is not safe.

This runs one uniform grid -- 4 input/tiling combinations x {morph=True,
morph=False} x 7 values -- so the two morph settings are compared over
identical values.  Earlier partial probes are left in `results.jsonl`
untouched; these runs use the `ibcheck__` prefix.

    PYTHONPATH=<checkout of origin/main>/src uv run python \
        visual_checks/grid-vs-mosaic-similarity/interior_bonus_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run as R  # noqa: E402

VALUES = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]


def main():
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

    states, districts = R.load_inputs()
    ctx_u = R.input_context(states)
    ctx_s = R.input_context(states, tile_count="tiles")
    ctx_d = R.input_context(districts, group_by="State Name")

    ref_u = R.morph_reference("states_uniform", states, np.ones(len(states)))
    ref_s = R.morph_reference("states", states, states["tiles"].to_numpy())
    ref_d = R.morph_reference("districts", districts, np.ones(len(districts)))

    combos = [
        ("states_uniform_hex", states, ctx_u, None, None, "hexagon", ref_u),
        ("states_uniform_sq", states, ctx_u, None, None, "square", ref_u),
        ("states154", states, ctx_s, "tiles", None, "hexagon", ref_s),
        ("districts", districts, ctx_d, None, "State Name", "hexagon", ref_d),
    ]

    for case, gdf, ctx, tc, gb, tiling, ref in combos:
        for morph in (True, False):
            for v in VALUES:
                opts = dict(R.MOSAIC_DEFAULTS)
                opts["interior_bonus"] = v
                tag = "T" if morph else "F"
                R.run_one(
                    f"ibcheck__{case}__morph{tag}__{v}",
                    gdf,
                    ctx,
                    layout=MosaicLayout(
                        tiling=tiling, morph=morph, hungarian_options=HungarianOptions(**opts)
                    ),
                    tile_count=tc,
                    group_by=gb,
                    keep_placement=False,
                    morph_ref=ref if morph else None,
                    extra={
                        "input": case,
                        "layout": "mosaic",
                        "tiling": tiling,
                        "morph": morph,
                        "ibcheck_case": case,
                        "ibcheck_morph": morph,
                        "ibcheck_value": v,
                        **opts,
                    },
                )
    print("[all done]", flush=True)


if __name__ == "__main__":
    main()
