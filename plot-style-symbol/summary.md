---
pr: 145
url: https://github.com/bright-fakl/carto-flow/pull/145
issue: 99
title: PlotStyle for the symbol plots
description: Part B2 of the style system. SymbolCartogram.plot and the symbol plot functions take style=, with the surface, the palettes by data role, the channels (fill, alpha, edge, linewidth, label), hatch cycle, reference layer and colorbar of the style. plot_symbols takes center= and categorical=. The default look of these plots changes; style="classic" gives the earlier look.
kind: pr
topic: symbol, infra
branch: feat/plot-style-symbol
base: main
date: 2026-10-16 18:00
related: plot-style-voronoi-proportional, plot-style-core, style-system
before: main @ 3a3d273 (equal to style="classic", except legend_kwargs["label"])
after: feat/plot-style-symbol @ 423c3a6
inputs: bundled US states; a circle-packing symbol cartogram of the population (200 iterations) and a hexagon grid layout.
---

`make_figures.py` draws each plot in classic, default and dark on the PR branch. `classic` is the look before this PR: the fill, edge and line colors, line widths, label texts, colorbar labels, legends and adjacency segments of `plot_symbols`, `plot_comparison`, `plot_adjacency`, `plot_adjacency_heatmap`, `plot_tiling` and `plot_displacement` are identical to `main` in the compared cases.

## Symbols

figure: fig_fill_default.png — No data: the fill of the style (`steelblue` in classic, default and dark).
figure: fig_population.png — Population: classic (viridis, linear, scientific notation), default (truncated `YlGnBu`, log colorbar with ticks 1M to 20M) and dark (viridis).
figure: fig_region.png — A text column: the categorical palette of the style.
figure: fig_diverging.png — `center=0`: the diverging palette, symmetric around the center.
figure: fig_edge_hatch_labels.png — Fill by value, edge and hatch by category, labels: the edge palette follows the categorical palette of the style, the label color the text color.

## Other plots

figure: fig_comparison.png — `plot_comparison`: the original panel takes the palette and the surface of the style.
figure: fig_adjacency.png — `plot_adjacency`: link colormap from the sequential palette, colorbar of the style, outline underlay in the axes edge color.
figure: fig_heatmap.png — `plot_adjacency_heatmap`: sequential palette and colorbar of the style.
figure: fig_tiling.png — `plot_tiling`: tiles use the reference layer; occupied tiles are the reference fill moved toward the text color.

## What changes

| | |
|---|---|
| style fields | `hatch_cycle`; `channel_range()` for the output range of data-driven alpha, line width and label size |
| `plot_symbols` | `style=`, `center=`, `categorical=`; defaults of `cmap`, `alpha`, `edgecolor`, `linewidth`, label color and size come from the style |
| other functions | `style=` on `plot_comparison`, `plot_adjacency`, `plot_adjacency_heatmap`, `plot_tiling` (also the method) and `plot_displacement`; `link_cmap` and the heatmap `cmap` default to the sequential palette |
| fix | `legend_kwargs["label"]` sets the colorbar label (it was ignored) |
| not yet | the fixed colors of the displacement arrows, adjacency nodes and tile pool edges |

## Checks

Suite 1244 passed, ruff and mypy clean; the symbol gallery examples and the edited notebooks run without error.
