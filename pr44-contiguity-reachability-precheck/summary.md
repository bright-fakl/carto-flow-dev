---
pr: 44
title: Skip hopeless path enumeration in repair_contiguity
description: No figures - the output is bit-identical, so a before/after pair would be two identical images. A BFS pre-check removes 99.5% of the heap work in repair_contiguity; the step becomes essentially free.
url: https://github.com/bright-fakl/carto-flow/pull/44
branch: perf/contiguity-path-reachability-precheck
base: main
date: 2026-09-23
after: 2bae205 (merged)
inputs: world (bundled, 800 and 1500 nominal tiles), congressional districts, US states; morph True and False
---

## No figures, and why

Pure performance change. The returned permutation is unchanged, so the
rendered cartogram is unchanged, so a before/after figure pair would be two
identical PNGs. The evidence that belongs on this page is the argument for why
the output *cannot* change, and an honest reading of the timings.

## What landed

25 added lines in one file, `src/carto_flow/geo_utils/contiguity.py`, at the
top of the inner `_enumerate_paths` generator. Nothing else in the merged diff.

## The cost being removed

`_enumerate_paths` is a heap over **paths**, not nodes. It keeps no visited
set, so a node is re-expanded once per distinct prefix that reaches it, and the
loop terminates only when `max_k` candidates have been yielded **or the heap
empties**. When nothing reaches `dst_slots`, "the heap empties" means every
simple path of up to `max_len` (10) nodes has been enumerated - on a hex tile
lattice roughly 1.3e5 heap operations to establish that one satellite cannot
be repaired at all. That happens once per unrepairable satellite, once per
pass.

Instrumented on a captured `repair_contiguity` call from the mosaic layout on
world countries at 800 nominal / 848 actual tiles (842 slots, 173 units, mean
degree 5.13):

| `max_passes` | heap pops | pops in calls that yielded nothing | calls | calls yielding nothing | provably unreachable |
|---|---|---|---|---|---|
| 1 | 1,482,211 | 1,468,147 | 22 | 11 | 11 |
| 2 | 2,959,350 | 2,936,294 | 36 | 21 | 21 |
| 5 | 7,384,414 | 7,340,735 | 72 | 51 | 51 |
| 10 (default) | 11,807,758 | **11,745,176 (99.5%)** | 107 | 80 | 80 |

Cost is exactly linear in `max_passes` (~1.48M pops per pass) because each pass
redoes the identical hopeless enumeration. The existing `if not any_swap:
break` does not help while some *other* satellite is still repairable.

## Why the result cannot change

This is the important part, and it is structural rather than merely tested.

A shortest walk is a simple path. So "no node of `dst_slots` is reachable from
`src_slots` within `max_len` nodes while avoiding `forbidden_nodes`" is
*precisely* the condition under which the path enumeration can yield nothing.
If any candidate path existed, a shortest one exists, is simple, is no longer,
and the BFS would find its endpoint.

The merged pre-check uses the same three parameters as the enumeration it
guards - same source filter (`s not in forbidden_nodes`), same forbidden set,
same depth bound and same depth convention (both count nodes, starting at 1,
and both stop expanding at `depth >= max_len`) - and returns early only when
`reachable` is False. It can therefore never skip a call that would have
yielded a path. In the instrumented comparison it fired on exactly the 80
no-yield calls and on no others, at every `max_passes` from 1 to 10.

Bit-identity was also confirmed end to end on six configurations - world (800
nominal / 848 actual), congressional districts and US states, each at
`morph=True` and `morph=False` - by a fingerprint of the complete per-region
set of assigned tile centroids plus the calibrated tile size. All six hashes
match before and after, re-run after rebasing onto current `main` rather than
carried over from the pre-rebase branch.

Note that the merged diff adds no test of its own; the identity evidence is the
argument above plus those fingerprint runs, and the existing suite (632 passed,
`make check` clean).

## Measurements, and what they actually support

**Isolated - the clean measurement.** The captured `repair_contiguity` call
above, run directly, `slot_of` compared with `np.array_equal`:

| `max_passes` | before | after | speedup | `slot_of` identical |
|---|---|---|---|---|
| 1 | 5.0 s | 0.06 s | 81x | yes |
| 2 | 10.6 s | 0.10 s | 110x | yes |
| 3 | 11.0 s | 0.08 s | 143x | yes |
| 5 | 19.8 s | 0.11 s | 176x | yes |
| 10 | **30.5 s** | **0.23 s** | **132x** | yes |

**End to end: 1.0x to 2.7x**, best of two reps per configuration:

| configuration | before | after |
|---|---|---|
| world, 800 nominal / 848 tiles, morph=True | 52.4 s | 26.5 s |
| world, 800 nominal / 848 tiles, morph=False | 45.6 s | 43.6 s |
| world, 1500 nominal / 1527 tiles, morph=True | 129.6 s | 90.4 s |
| world, 1500 nominal / 1527 tiles, morph=False | 204.7 s | 77.3 s |
| congressional districts, morph=True | 11.0 s | 4.2 s |
| congressional districts, morph=False | 9.4 s | 3.7 s |

### The noise, stated explicitly

Wall clock on this machine varies a great deal. The **same** world / 800 /
`morph=True` configuration measured **37.3 s, 52.4 s and 81.0 s on unpatched
`main` across three separate runs** - a 2.2x spread from run-to-run noise
alone, which is larger than most of the "speedups" in the table above. No
single end-to-end pair in that table supports a 2x claim, and the 52.4 -> 26.5
row in particular must not be read as "2x end to end": its `before` sits in the
middle of a range whose low end is below the `after` figure's plausible
neighbourhood.

### The honest summary

The repair step itself becomes essentially free (30.5 s -> 0.23 s in
isolation, with `slot_of` array-identical). How much total runtime that removes
depends entirely on how much of the run the repair was consuming - from almost
none (world / `morph=False` at 800 tiles, where the extra-ring swap-back
dominates instead) to most of it (districts). Quote the isolated number; treat
the end-to-end column as a range, not a measurement.
