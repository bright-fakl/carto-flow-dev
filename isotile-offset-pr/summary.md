---
pr: 8
title: "isotile: fill_region offset"
description: fill_region takes offset=(u, v), the lattice phase in multiples of the two translation vectors of the placed tiling, and selects the tiles in one cover pass. Needed by Tiling.with_offset of adoption step 3. Nothing to compare visually; the page gives the written evidence.
kind: pr
topic: symbol
project: isotile
url: https://github.com/bright-fakl/isotile/pull/8
branch: fill-region-offset
base: main
related: proposal-isotile-adoption, isotile-step-0-pr
date: 2026-10-28 12:00
before: bright-fakl/isotile main at 392484c
after: fill-region-offset (4,562 passed, 186 skipped locally on Python 3.10)
inputs: Python 3.10, numpy, shapely (tests); best of 15 runs for the timing
---

Issue 7 of isotile. `IsohedralTiling.fill_region(..., offset=(u, v))` anchors the lattice at the region center plus `u * translation_u + v * translation_v` of the placed tiling. The default `(0.0, 0.0)` gives the previous output. Non-finite values and a wrong shape raise `ValueError`.

## Tests

| Test | Types |
|---|---|
| `(u+1, v)`, `(u, v+1)`, `(u+1, v+1)`, `(u-2, v+3)` give the same tiles (compared by vertices, since the cell indices shift) | square, hexagon, triangle, IH7, IH28, IH84 |
| equal to the two-step result: shift the frame of the placed tiling by `u * translation_u + v * translation_v`, call `cover` | same six |
| default and explicit `(0.0, 0.0)` give identical cells, vertices and frame | same six |
| non-finite, wrong length, scalar, string, `None` raise `ValueError` | square |

## Timing

Regular hexagon, 100 x 100 region, `n_tiles=10000` (10,152 tiles), best of 15, two sessions:

| Call | ms |
|---|---|
| `fill_region` (default) | 141, 163 |
| `fill_region(offset=(0.37, 0.21))`, one pass | 204, 206 |
| `fill_region`, shift the frame, `cover` | 315, 378 |

The one-pass call costs about one `cover`; the two-step call costs about two. The machine is noisy (WSL2), so the ratio is the result, not the absolute numbers.

## Documentation

Docstring, the lattice-anchor note in `docs/concepts.md` and the CHANGELOG. The strict docs build and `scripts/make_doc_figures.py --check` pass.
