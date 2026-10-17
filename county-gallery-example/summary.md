---
pr: 172
url: https://github.com/bright-fakl/carto-flow/pull/172
issue: 129
title: Gallery example of a county population flow cartogram
description: A flow cartogram of the 3,108 contiguous counties by population, made with a resolution ladder (grid auto, 1000 iterations), in 14 s. Median county error 0.17 %, 95th percentile 15 %, mean 3.9 %.
kind: pr
topic: flow
base: main
branch: docs/county-cartogram-example
date: 2026-10-19 13:00
before: main @ 0491b5b
after: docs/county-cartogram-example @ 7a19269
related: census-county-level, square-grid-spacing, exploration-county-hierarchical-prototype
inputs: bundled ACS 2020 county snapshot (population, share below the poverty level), MorphOptions(grid="auto", n_iter=1000, area_scale=1e-6). The stall-rule PR (171) is not included.
---

## Figures

figure: fig_example.png — The gallery example: counties sized by population, colored by the share below the poverty level, with state boundaries.

## Result

- The ladder starts at 512 (the coarsest grid on which the smallest county covers the most cells; no grid up to 2048 covers 2.5), doubles to 2048 and ends stalled after the last level. Run time 14 s.
- Errors against the population share of the total area: median 0.17 %, 95th percentile 15.1 %, mean 3.9 %. The large errors belong to counties whose target is below one cell of the finest grid.
- Output polygons that cross themselves are repaired for plotting with `to_geodataframe(repair=True)`; this adds vertices, so the geometries are not suitable for animation.
- Three expected warnings (smallest counties below one cell, invalid output polygons, long straight segments after the coarse levels) are filtered in the example, with a comment explaining why.
