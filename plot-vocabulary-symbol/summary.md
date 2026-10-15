---
pr: 138
url: https://github.com/bright-fakl/carto-flow/pull/138
issue: 99
title: One parameter vocabulary for the symbol plot functions
description: Second part of the parameter vocabulary of the style-system proposal, after the flow module. facecolor binds the fill (column is a deprecated alias), labels replaces label, the *_legend_kwds become *_legend_kwargs, plot_adjacency draws a link layer (link_color, link_cmap, link_alpha, link_linewidth, link_legend, node_markersize), plot_displacement is styled by arrows_kwargs, and the tiling plots use assigned_facecolor, unassigned_facecolor, facecolor, edgecolor and cmap. Old names stay as deprecated aliases. No change of output. The Voronoi and proportional modules follow.
kind: pr
topic: symbol
branch: feat/plot-vocabulary-symbol
base: main
date: 2026-10-15 21:00
related: plot-vocabulary-flow, style-system
before: main @ 93165f3
after: feat/plot-vocabulary-symbol @ 6a232c1
inputs: a 3 x 3 grid of squares with random populations, CirclePackingLayout(max_iterations=20); the symbol gallery examples plot_symbol_cartogram, circle_packing_adjacency, circle_packing_displacement, circle_packing_adjacency_heatmap, plot_tiling, plot_tiling_2, styling, centroid_layout, mosaic_layout.
---

No figures: the change is parameter names. On the 3 x 3 grid the facecolors of `plot(facecolor="population", labels="name", legend_kwargs=...)`, the label texts and the segments of `plot_adjacency(link_alpha=0.4)` are identical to `main` with the old names (`np.array_equal`).

## Renames

| function | old | new |
|---|---|---|
| `SymbolCartogram.plot`, `plot_symbols` | `column`, `label` | `facecolor`, `labels` |
| `SymbolCartogram.plot`, `plot_symbols` | `legend_kwds`, `edge_legend_kwds`, `hatch_legend_kwds`, `linewidth_legend_kwds`, `alpha_legend_kwds`, `label_legend_kwds` | the same with `_kwargs` |
| `plot_comparison` | `column` | `facecolor` |
| `plot_adjacency` | `edge_color`, `edge_cmap`, `edge_alpha`, `edge_width`, `node_size`, `colorbar`, `colorbar_kwds` | `link_color`, `link_cmap`, `link_alpha`, `link_linewidth`, `node_markersize`, `link_legend`, `link_legend_kwargs` |
| `plot_adjacency_heatmap` | `colorbar`, `colorbar_kwds`, `tick_fontsize` | `legend`, `legend_kwargs`, `tick_labelsize` |
| `plot_displacement` | `arrow_color`, `arrow_alpha` | keys of `arrows_kwargs` |
| the `plot_tiling` functions | `assigned_color`, `unassigned_color` | `assigned_facecolor`, `unassigned_facecolor` |
| the plot methods of a tiling and of a tile | `face_color`, `edge_color`, `colormap` | `facecolor`, `edgecolor`, `cmap` |

## Decisions

- The adjacency links are a layer with the prefix `link_` because the `edge` names are the edge channel of the symbols. A line has a color, so `link_color` and not `link_edgecolor`.
- The `plot_tiling` functions keep `tile_edgecolor`, `tile_linewidth` and `tile_alpha`: they forward `**kwargs` to the symbol plot, where `edgecolor`, `linewidth` and `alpha` belong to the symbols. The tiles are a layer with its own prefix, like `core_`, `ring_` and `pool_`.
- `Tiling.plot(color_by=...)` stays: it selects a scheme (uniform, aspect, index, x, y, random), not a column.
- When `column` and `facecolor` are both given, `facecolor` wins and `column` warns, as in the old shorthand.

## Checks

Suite 1112 passed, ruff and mypy clean. The nine symbol gallery examples above run without deprecation warnings from the library. The edited notebooks were not executed. By position, `plot_displacement` moved `show_symbols` up by one and `SymbolCartogram.plot` has `facecolor` where `column` was.
