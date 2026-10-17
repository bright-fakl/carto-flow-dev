---
pr: 162
url: https://github.com/bright-fakl/carto-flow/pull/162
issue: 77
title: Square packing layout and the Demers preset
description: CirclePackingLayout(shape="square") packs axis-aligned squares of the circles' area with the circle layout's forces; squares touch along flat edges and keep their neighbors as well as circles do. The demers_cartogram preset now uses it. A greedy stacking prototype was rejected.
kind: pr
topic: symbol
base: main
branch: feat/square-packing-layout
date: 2026-10-18 18:00
before: main @ f4952ed
after: feat/square-packing-layout @ aa809ac
related: square-centroid-layout
inputs: bundled US census snapshot (49 regions, EPSG:5070) and bundled world (177 countries, EPSG:8857), spacing 0.
---

## Figures

figure: fig_square_packing.png — Census snapshot, squares drawn: centroid layout with squares (top left), square packing (top right), square packing with compactness 0.8 (bottom left), and the circle layout with squares fit inside (before, bottom right).

figure: fig_demers.png — `demers_cartogram` on the census snapshot: before (squares in grid cells) and after (square packing).

## Demers preset

`demers_cartogram` used the grid layout with a square tiling: each square sits in a lattice cell, and with the default `size_normalization="max"` the squares cover 15 % of the geometry area. It now uses `CirclePackingLayout(shape="square")` with the default forces and `size_normalization="total"` (a new parameter, as in the other presets). The grid version stays available through `layout="grid"`.

| census snapshot | squares in grid cells (before) | square packing (after) |
|---|---|---|
| total square area / geometry area | 0.15 | 1.00 |
| overlapping pairs | 0 | 0 |
| symbol area / convex hull | 0.14 | 0.55 |
| mean displacement | 395 km | 449 km |
| neighboring pairs within half a mean half-side | 0.00 | 0.76 |
| rank order x,y | 0.96 | 0.96 |

Other settings tried for the preset (same measure, neighboring pairs within half a mean half-side): the geographic-style forces (origin 0.5, topology 0.5, neighbor 0.5, no compaction) displace the squares less (277 km) but keep fewer neighbors in contact (0.62); origin weight 0.5 alone gives 337 km and 0.72. The default forces keep the neighbors best (0.76), which is what a Demers cartogram shows; the layout is available for other settings.

## Decision: generalize the simulator, not stack

A greedy stacking prototype (not in the PR) placed the squares one by one, flush against the placed squares, at the feasible spot nearest the original centroid. On the census snapshot it kept fewer neighbors than the centroid layout. The packing layout keeps neighbors through its forces (neighbor tangency, angular topology, compaction, contact sliding), and only the pair geometry of the simulator depends on the shape.

| layout | overlap | hull density | mean displacement | adjacent pairs kept | rank order x,y |
|---|---|---|---|---|---|
| centroid, circles | 0 | 0.58 | 161 km | 0.44 | 0.98 |
| packing, circles | 0 | 0.65 | 365 km | 0.63 | 0.97 |
| packing, circles, compactness 0.8 | 0 | 0.76 | 492 km | 0.73 | 0.95 |
| centroid, squares | 0 | 0.54 | 230 km | 0.45 | 0.98 |
| stacking, largest first | 0 | 0.65 | 313 km | 0.36 | 0.93 |
| stacking, smallest first | 0 | 0.52 | 176 km | 0.25 | 0.94 |
| stacking, center outward | 0 | 0.52 | 220 km | 0.36 | 0.97 |
| **packing, squares** | 0 | 0.57 | 447 km | **0.62** | 0.96 |
| **packing, squares, compactness 0.8** | 0 | 0.66 | 402 km | **0.70** | 0.95 |

Hull density is symbol area divided by the convex hull of the symbols; "adjacent pairs kept" is the fraction of the 109 neighboring pairs whose symbols are within a quarter of the mean symbol size; rank order is the Spearman correlation of x and y with the original centroids. Overlap is the largest overlap as a fraction of the mean symbol size (0 means at most the tolerance, 1e-4).

## World (177 countries)

| layout | overlap | hull density | mean displacement | adjacent pairs kept | rank order | iterations | time |
|---|---|---|---|---|---|---|---|
| packing, circles | 0.0001 | 0.50 | 1146 km | 0.63 | 0.97 | 343 | 2.5 s |
| packing, circles, compactness 0.8 | 0.0001 | 0.78 | 3723 km | 0.52 | 0.84 | 463 | 3.6 s |
| packing, squares | 0.0001 | 0.47 | 1236 km | 0.58 | 0.97 | 442 | 6.7 s |
| packing, squares, compactness 0.8 | 0.0001 | 0.75 | 2777 km | 0.55 | 0.94 | 339 | 5.4 s |
| centroid, squares | 0.0006 | 0.41 | 581 km | 0.49 | 0.99 | 9 | 4.7 s |

The squares converge and keep about as many neighbors as the circles, and keep the rank order better at high compaction.

## Spacing

Smallest edge-to-edge gap as a fraction of the requested gap (spacing times the mean half-side, or radius):

| data | shape | spacing 0.05 | spacing 0.2 |
|---|---|---|---|
| census | circles | 1.006 | 1.000 |
| census | squares | 0.998 | 1.000 |
| world | circles | 0.999 | 1.000 |
| world | squares | 0.998 | 1.000 |

The first version of the PR left the squares of the world data at 0.82 of the requested gap at spacing 0.05: the final Gauss-Seidel passes (500) did not settle the dense clusters, because a square separates along one axis per pair. Giving squares four times the passes in the final cleanup fixes it (the loop stops at the tolerance, so the cost is paid only when needed). A full overlap step in the cleanup also reached the spacing but moved the median symbol by 1.4 mean sizes on the world data (compactness 0.8, neighbors kept 0.55 down to 0.15), so it was rejected.

## What changes

| | |
|---|---|
| option | `CirclePackingLayoutOptions.shape`, `"circle"` (default) or `"square"`; the simulator takes `shape` |
| pair geometry | three helpers in the simulator: the pair distance (Euclidean, or the larger axis offset), the separation and contact direction (line between centers, or the dominant axis) and random directions for coincident pairs; used by the overlap count, the global expansion, the three overlap projections, the topology and tangency gaps and the contact reaction |
| cleanup | squares get four times the Gauss-Seidel passes in the final cleanup (they stop at the tolerance) |
| unchanged | the attraction forces (compaction, origin, group), step control, convergence; the tangency and topology force directions stay center to center |
| size | the half-side is sqrt(pi)/2 times the circle radius; `LayoutResult.sizes` holds the half-sides; the canonical symbol is a square |
| circles | positions of six configurations on the census snapshot (default, Dorling, stage 1 only, spacing 0, Gauss-Seidel only, grouped) are bit-identical before and after |
| preset | `demers_cartogram` uses the square packing layout, with a `size_normalization` parameter; docs that listed it as a grid preset are updated |
| docs | gallery example `plot_symbol_square_packing.py`, a phrase in the layout table of the pipeline explanation |

## Not in this PR

The flow-density layout, rectangles with an aspect ratio (separate issues), and the other named presets (`dorling`, `geographic` and others) do not take `shape`; use `CirclePackingLayout(shape="square", ...)`. The rename of `CirclePackingLayout` to `PackingLayout` is a separate PR. #77 stays closed by this PR for the force-based layouts it named.

## Checks

Suite 1428 passed, mypy and ruff clean. The new tests cover the canonical symbol, the spacing, no overlap as polygons, area proportional to the value, groups with attraction, the default being the circle, an invalid shape, the pair geometry helpers, and the spacing on the world data.
