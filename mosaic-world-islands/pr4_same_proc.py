"""Same-process bit-identity check for the two HungarianOptions changes.

Follows the technique from `visual_checks/mosaic-inert-verify/same_proc.py`:
the morph runs once and feeds BOTH implementations inside one process, so the
known run-to-run noise of `morph_geometries` cannot masquerade as a
regression.  For every Hungarian solve the layout performs, the new
`hungarian_morphed_assignment` (max_connectivity_iters=5, penalize_disconnected
switch) and the `origin/main` one (max_connectivity_iters=15,
disconnected_penalty_mult=10.0) are called on identical arguments and their
assignments compared elementwise.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import fields

import numpy as np

sys.path.insert(0, "/home/fakl/carto-flow/visual_checks/mosaic-options-sweep")
import inputs as IN  # noqa: E402

BASE = "/tmp/pr4base/_assignment.py"

from carto_flow.symbol_cartogram import create_layout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout  # noqa: E402
from carto_flow.symbol_cartogram.layouts.mosaic import _assignment as M  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "carto_flow.symbol_cartogram.layouts.mosaic._baseline_assignment", BASE
)
base_mod = importlib.util.module_from_spec(spec)
sys.modules["carto_flow.symbol_cartogram.layouts.mosaic._baseline_assignment"] = base_mod
spec.loader.exec_module(base_mod)

NEW = M.hungarian_morphed_assignment


class BaselineOptions:
    """HungarianOptions as origin/main declared it."""

    def __init__(self, opts):
        for f in fields(opts):
            if f.name != "penalize_disconnected":
                setattr(self, f.name, getattr(opts, f.name))
        self.max_connectivity_iters = 15
        self.disconnected_penalty_mult = 10.0 if opts.penalize_disconnected else 0.0


MISMATCH: list[int] = []
N = [0]
PASSES: list[int] = []


def probe(*args, **kw):
    new_stats: dict = {}
    kw_new = dict(kw, stats=new_stats)
    new_out = NEW(*args, **kw_new)
    kw_base = dict(kw)
    kw_base["options"] = BaselineOptions(kw["options"])
    kw_base["stats"] = {}
    base_out = base_mod.hungarian_morphed_assignment(*args, **kw_base)
    N[0] += 1
    PASSES.append(int(new_stats.get("passes", 0)))
    if not np.array_equal(new_out, base_out):
        MISMATCH.append(N[0])
    if kw.get("stats") is not None:
        kw["stats"].update(new_stats)
    return new_out


M.hungarian_morphed_assignment = probe

worst = 0
for case in IN.CASES:
    for morph in (False, True):
        loader, tile_count, group_by, tiling = IN.CASES[case]
        gdf = loader()
        MISMATCH.clear()
        N[0] = 0
        PASSES.clear()
        create_layout(
            gdf, tile_count=tile_count, group_by=group_by,
            layout=MosaicLayout(tiling=tiling, morph=morph, hungarian_options=HungarianOptions()),
            show_progress=False,
        )
        mp = max(PASSES) if PASSES else 0
        worst = max(worst, mp)
        print(f"{case:18s} morph={int(morph)}: {N[0]:3d} solve(s)  max passes run={mp}  "
              f"{'IDENTICAL' if not MISMATCH else f'MISMATCH at {MISMATCH}'}", flush=True)
print(f"\nworst passes run over all inputs = {worst} (cap allows {5 + 1})")
