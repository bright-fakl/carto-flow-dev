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
after: feat/plot-style-overlays @ 6b1c55b
inputs: bundled US states; a population-weighted Voronoi cartogram (RasterBackend 256, 100 iterations); a circle-packing symbol cartogram.
---

`make_figures.py` draws each plot in classic, default and dark on the PR branch. The colors of the Voronoi convergence, displacement, topology and repair plots in `classic` are identical to `main`.

## Voronoi

figure: fig_convergence.png — Convergence curve (series color) and final value (accent color).
figure: fig_voronoi_displacement.png — Base cells use the reference fill and the axes edge color; targets use the accent color, centroids the series color.
figure: fig_topology.png — Satellite cells use the highlight color; the base cells use the reference layer.

## Symbol

figure: fig_symbol_displacement.png — Displacement arrows use the accent color (yellow in dark, for contrast with the blue circles).
figure: fig_adjacency_nodes.png — Nodes use the text color of the style.

figure: fig_velocity.png — `plot_velocity_field`: the arrows take the accent color; classic draws them black (they were white on the white axes, invisible).
figure: fig_linewidth_legend.png — Line width by population without an edge color: the edge is the stroke color of the style, the widths follow the `"auto"` scale of the style (log here), and the legend keys are spaced in the scaled units.
figure: fig_width_scales_default.png — `linewidth_norm` linear, sqrt, log and rank on the same data (default style).
figure: fig_width_scales_dark.png — The same in the dark style.

## What changes

| | |
|---|---|
| style fields | `series_color`, `accent_color`, `positive_color`, `highlight_color`, `PlotStyle.pick(name, default)` |
| Voronoi | convergence, displacement, topology, repair plots and the history animation |
| symbol | `"stroke"` channel for data-driven edges (width, hatch), `alpha_norm`/`linewidth_norm`/`label_fontsize_norm` and `Channel(scale=...)`, the key of the line-width legend, displacement arrows, adjacency nodes, pool tiles of `plot_tiling` (`core_edgecolor`, `ring_edgecolor` default to the style) |
| flow | `VelocityPlotOptions.color` defaults to None (the accent color of the style; black on the bare axes and white over a density image in classic); the reference lines of the workflow convergence plot use the axes edge color |
| not yet | the fixed colors of the density and field image overlays beyond these |

## Checks

Suite 1274 passed, ruff and mypy clean. The topology repair overlays were not exercised by the comparison (the test case has no violations); the replaced literals were checked by reading the diff.
