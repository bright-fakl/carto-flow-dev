---
pr: 205
title: "repair_contiguity: distance-pruned chain search, satellite repair fixes and retries"
description: The chain search of repair_contiguity enumerates paths only while they can still reach the main body, forbids the tiles of the other satellites correctly, and refuses chains that split another group further, and retries when split groups block each other.
kind: pr
topic: symbol
project: carto-flow
url: https://github.com/bright-fakl/carto-flow/pull/205
branch: fix-repair-contiguity-191
base: main
related: mosaic-lattice-phase-search-pr
date: 2026-11-01 15:00
before: main; chain repair on districts by state with hexagons takes 3.8 s of a 7.8 s layout and leaves one split group
after: fix-repair-contiguity-191
inputs: 432 congressional districts grouped by state and by division, US states, Texas; mosaic layout, hexagon and square tilings, morph=False unless noted.
---
## Change

Fixes #191.

- Speedup (`_enumerate_paths` in `geo_utils/contiguity.py`): a backward breadth-first search gives every tile its distance to the main body; the heap is keyed by path length plus that distance, and prefixes that cannot finish within `max_len` are not pushed. Chains and their order are unchanged.
- Satellite bug: the tiles forbidden to a satellite repair were built from `comps[2:]`, but satellites are processed in distance order, so a satellite other than `comps[1]` forbade its own tiles, `comps[1]` was not forbidden, and the satellite found no path. The set is now built from `comps[1:]` minus the current satellite's tiles.
- Guard: a chain is refused if it increases the number of pieces of any other group, including groups that are already split. Before, only contiguous groups were protected; with the satellite fix a repair could re-split another split group and the next pass undid it (on states with 350 regions and squares, two groups alternated from the second pass on).
- Retries: `repair_contiguity` has an opt-in `retries` parameter (default 0; the mosaic layout passes 8). If split groups remain after the normal repair, it repeats the repair from the best state so far with a fixed portfolio: the first retry lets a satellite join any other piece of its group, the later ones run a lookahead pass in several group and satellite orders. A retry is kept only if the total number of extra pieces drops and no group gets more pieces; retries use at least 20 passes.
- Tests: `tests/test_geo_utils_contiguity_search.py` (pruned against plain enumeration, a satellite that is not the second largest component, states with 350 regions and squares); changelog entries.

## Split groups and non-contiguous regions, main -> branch

| Input (mosaic) | Split groups / non-contiguous regions |
|---|---|
| Districts by state, hexagon | 1 / 0 -> 0 / 0 |
| Districts by state, square | 2 / 0 -> 0 / 0 (without retries: 2 / 0, groups NY and CT) |
| Districts by division, hexagon | 0 / 0 -> 0 / 0 |
| Districts by division, square | 1 / 0 -> 0 / 0 |
| States with 150, 300 (morph) and 350 regions, hexagon | 0 / 0 -> 0 / 0 |
| States with 350 regions, square | 0 / 1 -> 0 / 0 |
| Texas, hexagon and square | 0 / 0 -> 0 / 0 |

With the satellite fix alone, states with 350 regions and squares got worse (2) and districts by division with squares stayed at 1; the guard fixes both. `TestRingSwapbackReach::test_us_states_needs_more_than_8_hops[False-350]` passes at the default 60 candidate paths (the last satellites of one group were blocked on all 60 candidates before; the old code solved it only by path-dependent luck).

## Timings, main -> branch (runs not isolated, noisy)

| Input (mosaic) | Wall time (s) |
|---|---|
| Districts by state, hexagon | 12.7 -> 4.1 |
| Districts by state, square | 10.1 -> 5.6 |
| Districts by division, hexagon | 6.9 -> 3.9 |

Chain repair alone on districts by state with hexagons: 3.79 s -> 0.02 s. Districts by state with squares: mean tile distance +0.24 % (660,409 -> 662,005), time 4.9 s; all other inputs have identical split groups, non-contiguous count and mean distance, and the retries do not run on them. `pytest -k "contiguity or mosaic or voronoi or symbol"`: 577 passed. The 8-hop probe in `TestRingSwapbackReach` now asserts that 16 hops strand fewer core tiles than 8 hops and no longer depends on the repair failing.

Figures (split groups outlined in red):

![before, hexagon](before_hexagon.png)
![after, hexagon](after_hexagon.png)
![before, square](before_square.png)
![after, square](after_square.png)

## Open

- Only one real input (districts by state with squares) exercises the retries, and the portfolio order was tuned on it (the third entry closes it); robustness on other inputs is unknown. An exact repartition (mixed-integer program) was too slow as a default.
- Layout setup time (about 4 s on districts by state with hexagons): tile intersections with the study union about 45 %, tile and geometry adjacency about 26 %. Not tried, because the change is not small.
