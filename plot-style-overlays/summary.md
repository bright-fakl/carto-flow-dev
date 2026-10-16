---
pr: 146
url: https://github.com/bright-fakl/carto-flow/pull/146
issue: 99
title: Overlay colors of the diagnostic plots in PlotStyle
description: PlotStyle gets series_color, accent_color, positive_color and highlight_color for the fixed colors of the diagnostic overlays of the Voronoi and symbol plots. Default and dark set them; classic keeps the former colors.
kind: pr
topic: voronoi, symbol, infra
branch: feat/plot-style-overlays
base: main
date: 2026-10-16 20:00
related: plot-style-symbol, plot-style-voronoi-proportional, style-system
before: main @ 3055caa
after: feat/plot-style-overlays @ dece1bd
inputs: bundled US states; a population-weighted Voronoi cartogram (RasterBackend 256, 100 iterations); a circle-packing symbol cartogram.
---

`make_figures.py` draws each plot in classic, default and dark on the PR branch. The colors of the Voronoi convergence, displacement, topology and repair plots in `classic` are identical to `main`.

## Voronoi

figure: fig_convergence.png — Convergence curve (series color) and final value (accent color).
figure: fig_voronoi_displacement.png — Base cells use the reference fill and the axes edge color; targets use the accent color, centroids the series color.
figure: fig_topology.png — Satellite cells use the highlight color; the base cells use the reference layer.

## Symbol

figure: fig_symbol_displacement.png — Displacement arrows use the accent color.
figure: fig_adjacency_nodes.png — Nodes use the text color of the style.

## What changes

| | |
|---|---|
| style fields | `series_color`, `accent_color`, `positive_color`, `highlight_color`, `PlotStyle.pick(name, default)` |
| Voronoi | convergence, displacement, topology, repair plots and the history animation |
| symbol | displacement arrows, adjacency nodes, pool tiles of `plot_tiling` (`core_edgecolor`, `ring_edgecolor` default to the style) |
| not yet | the animation of the flow cartogram (`VelocityPlotOptions` colors), the gray legend keys |

## Checks

Suite 1250 passed, ruff and mypy clean. The topology repair overlays were not exercised by the comparison (the test case has no violations); the replaced literals were checked by reading the diff.
