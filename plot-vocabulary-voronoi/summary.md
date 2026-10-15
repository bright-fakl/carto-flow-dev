---
pr: 139
url: https://github.com/bright-fakl/carto-flow/pull/139
issue: 99
title: One parameter vocabulary for the Voronoi plot functions
description: Third part of the parameter vocabulary of the style-system proposal. facecolor binds the fill of the Voronoi plots (a column, the built-in area_error_pct, a numeric array or a color; column is a deprecated alias) and the *_style dicts become *_kwargs. Old names stay as deprecated aliases. No change of output. Stacked on the symbol PR; the proportional module follows.
kind: pr
topic: voronoi
branch: feat/plot-vocabulary-voronoi
base: feat/plot-vocabulary-symbol
date: 2026-10-15 23:00
related: plot-vocabulary-symbol, plot-vocabulary-flow, style-system
before: main @ 93165f3
after: feat/plot-vocabulary-voronoi
inputs: a 3 x 3 grid of squares with random populations, RasterBackend(resolution=50), VoronoiOptions(n_iter=5).
---

No figures: the change is parameter names. On the 3 x 3 grid the facecolors of the categorical plot, `facecolor="population"`, `facecolor="area_error_pct"` and of both panels of the comparison are identical to `main` with `column=` (`np.array_equal`).

## Renames

| function | old | new |
|---|---|---|
| `VoronoiCartogram.plot`, `plot_cartogram`, `plot_comparison` | `column` | `facecolor` |
| `plot_displacement` (function and method) | `geometry_style`, `adjacency_style`, `centroid_style`, `position_style`, `displacement_style` | `geometry_kwargs`, `adjacency_kwargs`, `centroid_kwargs`, `position_kwargs`, `displacement_kwargs` |
| `animate_voronoi_history` | `cell_style`, `point_style` | `cell_kwargs`, `point_kwargs` |

## Behavior of `facecolor`

| input | result |
|---|---|
| `None` | categorical by cell index (as before) |
| a column of the source GeoDataFrame | choropleth |
| `"area_error_pct"` | signed area error of the cells, diverging colormap |
| a numeric array, one value per cell | choropleth by value |
| a color | constant fill |
| a column that is also the built-in quantity or a color | the column, `UserWarning` |
| any other string | `ValueError` (before: only a missing column raised) |

## Checks

Suite 1120 passed, ruff and mypy clean. The edited notebooks were executed locally without error.
