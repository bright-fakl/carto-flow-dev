---
pr: 161
url: https://github.com/bright-fakl/carto-flow/pull/161
issue: 77
title: Square collision for the centroid layout
description: CentroidLayout(shape="square") separates axis-aligned squares of the circles' area, so squares sit flush with no gaps and no overlaps; the default stays circles.
kind: pr
topic: symbol
base: main
branch: feat/square-centroid-layout
date: 2026-10-18 12:00
before: main @ b7df147
after: feat/square-centroid-layout @ 0a91dc2
inputs: bundled US census snapshot (49 regions, EPSG:5070), size Population, spacing 0.
---

## Figures

figure: fig_before_after.png — Left and middle: squares drawn on the circle layout (the fit modes `inside` and `area`); right: the square layout.

## Measured (US census snapshot, spacing 0)

| layout and symbols | overlapping pairs | total symbol area / circle area | mean displacement |
|---|---|---|---|
| circle layout, circles | 7 | 1.00 | 156 km |
| circle layout, squares, fit `inside` | 0 | 0.64 | 156 km |
| circle layout, squares, fit `area` | 28 | 1.00 | 156 km |
| square layout, squares | 0 | 1.01 | 230 km |
| square layout, squares, spacing 0.05 | 0 | 1.01 | 246 km |

Overlapping pairs have an overlap area above 0.1 % of the mean symbol area. The area ratio of 1.01 is the polygon approximation of the circle (a 64-gon has 0.5 % less area than the circle). The 7 overlapping pairs of the circle layout at `spacing=0` are the existing behavior of its cleanup pass and are not changed here.

## What changes

| | |
|---|---|
| option | `CentroidLayoutOptions.shape`, `"circle"` (default, unchanged) or `"square"` |
| collision | the pair distance is the larger axis offset (Chebyshev) and pairs separate along that axis, the direction of the smaller penetration; the global expansion factor uses the same distance |
| size | the square half-side is sqrt(pi)/2 times the circle radius, so the area stays proportional to the value; `LayoutResult.sizes` holds the half-sides |
| final pass | after the attraction cycles, up to 500 local passes with a full step (stops at the tolerance): 0.28 of the mean size overlap remained after 20 passes, none after this pass; 0.6 s for 49 regions |
| docs | gallery example `plot_symbol_square_layout.py`, a line in the layout table of the pipeline explanation |

## Not in this PR

The packing and flow-density layouts (their force simulators assume circles), rectangles with an aspect ratio, and a preset function. The symbols sit farther from the geometry centroids than circles (230 km against 156 km): equal-area squares need more room in the dense east, and the final pass allows no overlap.

## Checks

Symbol and layout tests pass locally (395), mypy and ruff clean; the new tests cover flush squares, coincident squares, the canonical symbol, no overlap with and without groups, area proportional to the value, and the unchanged circle path. The full suite and the docs build run in CI.
