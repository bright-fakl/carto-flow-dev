---
pr: 49
title: Pin the repair_contiguity reachability pre-check with tests
description: No figures - a test-only PR changes no output. The written evidence is the invariant now pinned, how the pre-check and the enumeration are compared directly, and which mutations the tests catch.
url: https://github.com/bright-fakl/carto-flow/pull/49
branch: test/contiguity-precheck-invariant
base: main
date: 2026-09-23
before: origin/main @ 2bae205
after: test/contiguity-precheck-invariant
inputs: hand-built adjacency graphs (chains, cycles, stars, a 4x4 grid) and 300 seeded random small graphs - no geodata
---

## No figures, and why

Every PR gets a page, including one with nothing to draw. This PR adds one
test file and changes no source, so there is no before/after image to make: the
rendered cartogram is identical by construction. The evidence that belongs
here is written, and it is below.

## What landed

`tests/test_geo_utils_contiguity_precheck.py`, 17 tests, 295 lines. No change
to `src/`.

## The invariant, and why it needed pinning

PR #44 put a 25-line node-level BFS in front of the path enumeration inside
`repair_contiguity`. It returns early when no node of `dst_slots` is reachable
from `src_slots` within `max_len` nodes while avoiding `forbidden_nodes`. The
correctness argument is that a shortest walk is a simple path, so
"unreachable within `max_len` nodes" is exactly the condition under which the
enumeration would have yielded nothing.

The argument is sound, but the pre-check **duplicates** four things the
enumeration also does:

1. the source filter (`s not in forbidden_nodes`),
2. the `forbidden_nodes` handling during expansion,
3. the depth bound (`>= max_len` stops expanding),
4. the convention that `max_len` counts **nodes**, starting at 1, not edges.

Change any one of them on one side only and the pre-check starts returning
early on calls that do have a path. `repair_contiguity` then quietly stops
repairing satellites, still returns a valid permutation, and no test fails.
That is the failure mode these tests exist to make loud.

PR #44's own page, `visual_checks/pr44-contiguity-reachability-precheck/`,
states plainly that the merged diff adds no test of its own and that the
identity evidence was the argument plus end-to-end fingerprint runs. This PR
closes that gap.

## How the two are compared directly

Both the pre-check and the enumeration are closures inside
`repair_contiguity`, so neither can be imported. Rather than test only through
`repair_contiguity` - which can show a repair happening but cannot show
*which* of the two decided nothing was reachable - the tests lift
`_enumerate_paths` out of the live function source with `inspect.getsource`
and compile three callables over a caller-supplied adjacency list:

| form | what it is |
|---|---|
| guarded | the generator exactly as written |
| bare | the same generator with the pre-check block deleted |
| verdict | the pre-check alone, returning its `reachable` flag |

So the comparison is direct: `verdict(...) is bool(list(bare(...)))`, plus
`list(guarded(...)) == list(bare(...))` element-wise. All three are derived
from the real source at test time - no copy of the algorithm lives in the test
file, so the tests cannot drift into agreeing with a stale duplicate.

The lift is marker-guarded. If the pre-check block stops matching the markers
the tests strip it by, they fail with a message saying exactly that, rather
than silently testing nothing.

## What is asserted

- **The boundary, in both directions.** On a chain, a route of exactly
  `max_len` nodes is yielded and the verdict is reachable; one node further,
  the verdict is unreachable and the bare enumeration also yields nothing. The
  node-not-edge convention is asserted explicitly at the default bound of 10.
- **Agreement.** Verdict against bare enumeration on 11 hand-built graphs with
  hand-computed expectations - including `forbidden_nodes` cutting the only
  route, `forbidden_nodes` forcing a longer route that is still within the
  bound, a forbidden source, a source that is also a destination, an isolated
  node, a cycle with two routes of different length - and on 300 seeded random
  small graphs (2-9 nodes, random `max_len` from 1 to 6).
- **The skip is real, not just harmless.** On a 4x4 grid with a destination
  beyond the bound, the guarded call costs at most one neighbour lookup per
  node (16) while the bare one costs 471. This pins the performance claim of
  PR #44 as well as the correctness one.
- **The repair still repairs.** Three cases through `repair_contiguity`
  itself: a reachable satellite is walked back next to the main body; a
  10-node route repairs while an 11-node one leaves the satellite in
  `discontiguous` with the permutation untouched; a group in three components
  - so one satellite sits in `forbidden_nodes` while the other searches -
  still converges to contiguous. A pre-check that wrongly skipped everything
  would fail all three.

Expected values are hand-derived from the graph, never read off a run.

## Mutation check

Four one-line mutations of the pre-check were applied by hand to
`contiguity.py` and the suite re-run. Each is caught:

| mutation | tests failing |
|---|---|
| depth bound off by one (`depth >= max_len - 1`) | 7 |
| `forbidden_nodes` dropped from expansion | 4 |
| source filter dropped (`seen = set(src_slots)`) | 2 |
| destination test shifted (`and depth > 1`) | 2 |

The first three are exactly the three duplications listed above; the fourth is
the depth convention. The source was restored after each. Note that the
earlier draft of these tests, which compared only guarded-against-bare output,
caught the depth mutation but **not** the two `forbidden_nodes` /source-filter
ones - those make the pre-check too permissive, which is invisible in the
output and only costs performance. Lifting the verdict out separately is what
made them visible; that is the reason the third form exists.

## Disagreements found

None. The merged pre-check agreed with the enumeration on every input tried,
including the 300 random graphs. No bug to report against PR #44.

## Checks

`make check` clean. Full suite 649 passed (632 before PR #44's page was
written, +17 here). No new warnings.
