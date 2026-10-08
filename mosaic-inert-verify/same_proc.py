"""Compare baseline vs modified hungarian_morphed_assignment on identical inputs.

Sidesteps the known morph=True run-to-run noise: the morph runs once, its
output is captured, and both implementations are called on that same input
inside one process.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import fields

import numpy as np

sys.path.insert(0, "/home/fakl/carto-flow/visual_checks/mosaic-options-sweep")
import inputs as IN  # noqa: E402

BASE = "/home/fakl/carto-flow/.claude/worktrees/mosaic-baseline/src/carto_flow/symbol_cartogram/layouts/mosaic/_assignment.py"

from carto_flow.symbol_cartogram import create_layout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import _assignment as M  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import (  # noqa: E402
    HungarianOptions, MosaicLayout,
)

# Give the baseline module a real package context so its relative imports work.
spec = importlib.util.spec_from_file_location(
    "carto_flow.symbol_cartogram.layouts.mosaic._baseline_assignment", BASE
)
base_mod = importlib.util.module_from_spec(spec)
sys.modules["carto_flow.symbol_cartogram.layouts.mosaic._baseline_assignment"] = base_mod
spec.loader.exec_module(base_mod)

NEW = M.hungarian_morphed_assignment


class BaselineOptions:
    """HungarianOptions plus the two removed fields at their old defaults."""

    def __init__(self, opts):
        for f in fields(opts):
            setattr(self, f.name, getattr(opts, f.name))
        self.gap_bridge_mult = 5.0
        self.disconnected_score_weight = 100


MISMATCH = []
N = [0]


def probe(*args, **kw):
    new_out = NEW(*args, **kw)
    kw_base = dict(kw)
    kw_base["options"] = BaselineOptions(kw["options"])
    kw_base["stats"] = {} if kw.get("stats") is not None else None
    base_out = base_mod.hungarian_morphed_assignment(*args, **kw_base)
    N[0] += 1
    if not np.array_equal(new_out, base_out):
        MISMATCH.append(N[0])
    return new_out


M.hungarian_morphed_assignment = probe

for case in IN.CASES:
    for morph in (False, True):
        loader, tile_count, group_by, tiling = IN.CASES[case]
        gdf = loader()
        MISMATCH.clear()
        N[0] = 0
        create_layout(gdf, tile_count=tile_count, group_by=group_by,
                      layout=MosaicLayout(tiling=tiling, morph=morph,
                                          hungarian_options=HungarianOptions()),
                      show_progress=False)
        print(f"{case} morph={int(morph)}: {N[0]} solve(s), "
              f"{'IDENTICAL' if not MISMATCH else f'MISMATCH at {MISMATCH}'}", flush=True)
