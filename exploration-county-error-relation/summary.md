---
issue: 167, 177
title: Area error of the county flow cartogram against original and target area
description: 72 of 3,108 counties end above 10 % area error. The error depends on the shrink factor (target over original area) and on the target size in grid cells together. No county that shrinks by less than 10 times, and almost none with a target of 16 cells or more, is above 10 %. The failing counties are thin strips along the Great Plains and a cluster in Virginia.
kind: exploration
topic: flow
status: open
related: exploration-counties-subcell, exploration-quadtree-windows
date: 2026-10-19 12:00
before: main @ 06d4ff0
after: the same checkout; script only, no library change
inputs: 3,108 bundled counties (population) with max_segment_length 1000, ladder with min_resolution and levels auto, n_iter 1000, area_scale 1e-6, default options. Error is the output area against the population share of the total output area; the cell is that of the finest level (4.26 km, 18.1 km2). Single run.
---

`relation.py <output dir>` runs the morph and draws the four figures. The run ends stalled with a mean error of 1.52 %, a median of 0.25 % and a maximum of 523 %.

## Error against shrink and target size

figure: fig1_error_vs_shrink.png — Absolute area error against the shrink factor (target area over original area), colored by the target area in grid cells. The errors above 10 % are at shrink factors below 0.1, and the darkest points (targets below four cells) dominate them.
figure: fig2_error_vs_target.png — Absolute area error against the target area in grid cells, colored by the shrink factor. The errors rise below about 10 cells and are above 10 % for targets under four cells with a shrink below 0.1. Targets of 16 cells or more are at 0.1 to 1 % whatever the shrink.
figure: fig3_share_over_10pct.png — Share of counties above 10 % error by shrink factor and target size. The failures sit in one corner: shrink below 0.1 and target below 16 cells; the corner is darkest at shrink below 0.01 and target below one cell (76 %).

## Where they are

figure: fig4_where.png — The cartogram output with the 72 counties above 10 % error in red. Most are thin strips along the Great Plains (TX 22, NE 18, MT 7, ND 7) and a cluster in Virginia (7), where the independent cities enlarge and their surrounding counties shrink.

## Reading

- Counties that shrink by less than 10 times (shrink above 0.1) are within 10 % whatever their target size; the median error there is 0.1 to 0.5 %.
- Counties with a target of 16 cells or more are within 10 % except for 6 of 2,273.
- A county has to be both strongly shrunk (below 0.1, down to 0.003) and small (below about 16 cells) to fail. A floor at one cell on the convergence test would excuse 15 of the 72; at four cells 45 stay above 10 %.
- The failing counties are on average larger than the others in the original map (median 131 cells against 89), so they are large rural counties squeezed to strips. In the cartogram they form the thin dividing line along the plains.
