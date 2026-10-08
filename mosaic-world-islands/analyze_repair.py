"""Analyse a captured repair_contiguity call: where the heap operations go,
how cost scales with max_passes, and whether the BFS pre-check is exact."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import repair_probe as RP  # noqa: E402
from carto_flow.geo_utils.contiguity import repair_contiguity  # noqa: E402

OUT = HERE / "repair_analysis.jsonl"


def append(rec):
    with OUT.open("a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
        f.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkl", required=True)
    ap.add_argument("--passes", default="1,2,3,5,10")
    a = ap.parse_args()
    calls = pickle.load(open(a.pkl, "rb"))
    label = Path(a.pkl).stem

    for ci, c in enumerate(calls):
        groups = c["groups"]
        adjacency = [set(s) for s in c["adjacency"]]
        mcp = c["max_candidate_paths"]
        n = len(groups)
        deg = np.mean([len(s) for s in adjacency])
        print(f"== {label} call {ci}: n={n} groups={len(set(groups))} mean_deg={deg:.2f} "
              f"max_passes={c['max_passes']} max_cand={mcp} lib_time={c['elapsed']:.1f}s")

        for mp in [int(x) for x in a.passes.split(",")]:
            RP._reset()
            t0 = time.perf_counter()
            slot_probe, disc = RP.repair_probe(None, groups, max_passes=mp,
                                               adjacency=[set(s) for s in adjacency],
                                               max_candidate_paths=mcp)
            t_probe = time.perf_counter() - t0
            st = dict(RP.STATS)

            t0 = time.perf_counter()
            slot_ref, disc_ref = repair_contiguity(None, groups, max_passes=mp,
                                                   adjacency=[set(s) for s in adjacency],
                                                   max_candidate_paths=mcp)
            t_ref = time.perf_counter() - t0

            RP._reset()
            t0 = time.perf_counter()
            slot_fast, disc_fast = RP.repair_fast(None, groups, max_passes=mp,
                                                  adjacency=[set(s) for s in adjacency],
                                                  max_candidate_paths=mcp)
            t_fast = time.perf_counter() - t0
            st_fast = dict(RP.STATS)

            identical = bool(np.array_equal(slot_fast, slot_ref))
            rec = dict(label=label, call=ci, n=n, n_groups=len(set(groups)),
                       mean_degree=float(deg), max_passes=mp, max_candidate_paths=mcp,
                       t_lib=t_ref, t_probe=t_probe, t_fast=t_fast,
                       speedup=t_ref / t_fast if t_fast else None,
                       fast_identical=identical,
                       n_discontiguous=len(disc_ref),
                       **{f"probe_{k}": v for k, v in st.items()},
                       precheck_skips=st_fast["precheck_skips"],
                       precheck_time=st_fast["precheck_time"])
            append(rec)
            print(f"  passes={mp:2d}  lib={t_ref:6.1f}s fast={t_fast:6.2f}s "
                  f"speedup={rec['speedup'] or 0:6.1f}x identical={identical}  "
                  f"pops={st['pops']:,} ({st['pops_no_yield']:,} in calls that yielded nothing) "
                  f"enum_calls={st['calls']} no_yield={st['calls_no_yield']} "
                  f"unreachable={st['calls_unreachable']} skips={st_fast['precheck_skips']} "
                  f"disc={len(disc_ref)}")


if __name__ == "__main__":
    main()
