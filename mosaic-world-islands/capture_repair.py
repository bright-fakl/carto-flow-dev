"""Capture the exact (units, adjacency) inputs `_chain_swap_repair` hands to
`repair_contiguity`, by monkeypatching the module attribute (the mosaic code
imports it inside the function, so the patch is picked up).  Nothing in the
library is modified.
"""

from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))

import wi_inputs as W  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="world")
    ap.add_argument("--budget", type=int, default=800)
    ap.add_argument("--morph", type=int, default=1)
    a = ap.parse_args()

    import carto_flow.geo_utils.contiguity as C

    orig = C.repair_contiguity
    calls = []

    def spy(cells, groups, **kw):
        t0 = time.perf_counter()
        out = orig(cells, groups, **kw)
        dt = time.perf_counter() - t0
        calls.append(dict(groups=list(groups), adjacency=[sorted(s) for s in kw["adjacency"]],
                          max_passes=kw.get("max_passes"),
                          max_candidate_paths=kw.get("max_candidate_paths"),
                          elapsed=dt, slot_of=out[0].tolist()))
        print(f"[spy] repair_contiguity n={len(groups)} {dt:.1f}s", flush=True)
        return out

    C.repair_contiguity = spy

    from run_all import load_case, run

    gdf, tc, gb = load_case(a.case, a.budget)
    res, elapsed = run(gdf, tc, gb, morph=bool(a.morph))
    print(f"[total] {elapsed:.1f}s, {len(calls)} repair call(s)")
    out = HERE / f"repair_{a.case}_{a.budget}_morph{a.morph}.pkl"
    with out.open("wb") as f:
        pickle.dump(calls, f)
    print("wrote", out)


if __name__ == "__main__":
    main()
