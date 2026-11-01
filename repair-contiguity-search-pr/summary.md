---
pr: 205
title: "repair_contiguity: distance-pruned chain search"
description: The chain search of repair_contiguity enumerates paths with a heap keyed by length plus the distance to the main body, so prefixes that cannot finish within the maximum length are never expanded. Chains and their order are unchanged.
kind: pr
topic: symbol
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/205
branch: fix-repair-contiguity-191
base: main
related: mosaic-lattice-phase-search-pr
date: 2026-11-01 11:00
before: main; chain repair on districts by state with hexagons takes 3.8 s of a 7.8 s layout
after: fix-repair-contiguity-191
inputs: 432 congressional districts grouped by state, hexagon tiling, mosaic layout, morph=False; states, districts by division and Texas with squares and hexagons.
---
## Change

Part of #191. Results do not change, so there are no before and after figures.

- `_enumerate_paths` in `geo_utils/contiguity.py`: a backward breadth-first search gives every tile its distance to the main body; the heap is keyed by path length plus that distance, and prefixes that cannot finish within `max_len` are not pushed. The chains and their order are identical to before.
- `tests/test_geo_utils_contiguity_search.py` replaces the precheck test: pruned against plain enumeration on 11 hand-built cases and 60 random graphs, and a linear-cost check.

## Timings

| Input (mosaic) | Chain repair before -> after (s) | Wall time before -> after (s) | Split groups, split geometries |
|---|---|---|---|
| Districts by state, hexagon | 3.79 -> 0.02 | 7.8 -> 4.0 | (1,0), unchanged |
| Districts by state, square | 0.36 -> 0.02 | 5.9 -> 5.9 | (2,0), unchanged |
| Districts by division, hexagon | 0.00 | 3.7 -> 1.6 | (0,0), unchanged |

Other inputs (states, states by division, Texas, both tilings) are unchanged. Wall times vary with numba compilation.

## Where the remaining time goes (districts by state, hexagon, about 4 s)

Layout setup, not the repair: intersections of tile polygons with the region unions about 45 %, tile and geometry adjacency about 26 %, the Hungarian assignment about 35 %, tile size calibration about 19 % (shares overlap). Not done: intersecting only tiles whose bounds touch the union boundary, and computing the tile adjacency once.

## Not in this PR

The set of tiles that a satellite repair must avoid is built from `comps[2:]`, but satellites are processed in distance order, so a satellite other than `comps[1]` forbids its own tiles and `comps[1]` is not forbidden. Building the set from `comps[1:]` minus the current satellite lets the three unreachable satellites of districts by state with hexagons connect: split groups 1 -> 0 with hexagons, 2 -> 1 with squares on districts by state, and 1 -> 0 on districts by division with squares. It breaks `TestRingSwapbackReach::test_us_states_needs_more_than_8_hops[False-350]`: one state ends non-contiguous, and more passes or candidate paths do not help. It is left out until that is understood.

The remaining satellite on districts by state with squares lies 11 tiles from its main body, beyond `max_len` 10; raising `max_len` changes the result non-monotonically.
