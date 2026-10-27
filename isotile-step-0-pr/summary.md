---
pr: 5
title: "isotile step 0: preset amplitude, neighbor_lists, cover precision"
description: Three small changes in isotile that the carto-flow adoption needs, plus a documentation note. The wavy_triangle preset has the amplitude 0.15 of carto-flow again, TileSet.neighbor_lists returns the neighbors of all tiles from one adjacency matrix (10,300 tiles in 14 ms), cover measures overlap areas relative to the region center (no holes in the triangle tilings at distance 1e6, 144 instead of 146 square tiles at 1e3), and fill_region states that the lattice is anchored at the region center. Nothing to compare visually; the page gives the written evidence.
kind: pr
topic: symbol
project: isotile
url: https://github.com/bright-fakl/isotile/pull/5
branch: step0-carto-flow-adoption
base: main
related: proposal-isotile-adoption, isotile-phase-2-pr
date: 2026-10-27 17:30
before: bright-fakl/isotile main at a66ed7a
after: step0-carto-flow-adoption @ 819d151 (4,522 passed, 186 skipped locally on Python 3.10)
inputs: Python 3.10, numpy, scipy, shapely (tests); single runs; carto-flow 2.0.0 for the preset fixture
---

Items I-1 to I-3 and the documentation note of section 2.4 of [the adoption proposal](../proposal-isotile-adoption/index.html). There is nothing to show in figures; each change has a test that fails before it.

## What changed

| Item | Change | Test (fails before) |
|---|---|---|
| I-1 | `wavy_triangle` has the curves `[(0,0), (0.25,0.15), (0.5,0), (0.75,-0.15), (1,0)]` on all three shape ids (0.12 before). `wavy_square` keeps 0.12, as in carto-flow. | `test_preset_matches_carto_flow` for each of the 15 presets against `tests/data/carto_flow_presets.json` (type, parameters, curves, modes). Only `wavy_triangle` failed before; the other 14 are equal to carto-flow's data. |
| I-2 | `TileSet.neighbor_lists(kind="edge") -> list[IntArray]`: sorted neighbors of every tile from one adjacency matrix; `[]` for an empty set. `neighbors(i)` is unchanged: a cache on the mutable `TileSet` dataclass is not a clean change. Its docstring and the Adjacency page point to the new method. | equal to `neighbors(i)` for 3 types and 3 kinds, default kind, empty and single-tile sets, 10,300 tiles in under 0.1 s |
| I-3 | `cover` subtracts the region center from the tile vertices and the bounds before the overlap areas are computed. | the two experiments of `cover_precision.py`: 100 random triangle tilings at distance 1e6 have no sampled hole; the square tiling with the boundary on tile edges returns 144 tiles at distances 0, 1e3, 1e5 and 1e6 |
| note | The `fill_region` docstring and the Concepts page state that the lattice is anchored at the region center, so a region expanded by the same amount on all sides keeps the lattice. | every tile of a region is a tile of its symmetric expansion, for the square, the hexagon and IH1, IH7, IH10, IH28, IH41, IH84 (passes before the change as well: it records the property) |

The CHANGELOG has entries under Fixed, Added and Documentation.

## Evidence

Timings of I-2 (`IH7` over [-1, 1]^2, `n_tiles=10000`, 10,300 tiles, one machine, single run):

| | before | after |
|---|---|---|
| one `neighbors(i)` call | 25 ms first call, 3.0 ms mean of the next 200 | unchanged |
| neighbors of all tiles | 31 s (200 calls extrapolated to 10,300; the proposal page estimated 5 minutes from 30 ms per call) | `neighbor_lists()`: 14 ms |
| `adjacency("edge")` | 2.8 ms | unchanged |

Precision of I-3, before the change (`cover_precision.txt` of the proposal page): 16 of 100 triangle tilings with a sampled hole of at most 5e-5 of the area at distance 1e6; 146 square tiles instead of 144 at distance 1e3. After: the tests above pass.

Checks run locally: `ruff check`, `ruff format`, `mypy` (strict, on `src`), the full test suite (4,522 passed, 186 skipped), `scripts/make_doc_figures.py --check` (figure files are up to date) and the strict docs build. The fixture generator is `scripts/make_carto_flow_presets_fixture.py`; it needs carto-flow 2.0.0 (`uv run --with "carto-flow==2.0.0" python scripts/make_carto_flow_presets_fixture.py`) and its output is the committed file byte for byte (9 KB with the repository's JSON formatting; the hook `pretty-format-json` fixes the indentation).

## Deviations

- The fixture is 9 KB, not 4 KB: the repository's pre-commit hook writes JSON with an indent of 2.
- The sampled-hole test uses 20,000 sample points per tiling (the experiment used 40,000) to keep the test under a few seconds.
- `neighbors(i)` does not reuse a cached matrix.
