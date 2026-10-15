---
pr: 140
url: https://github.com/bright-fakl/carto-flow/pull/140
issue: 99
title: One parameter vocabulary for the proportional plot functions
description: Fourth and last part of the parameter vocabulary of the style-system proposal. facecolor binds the fill of plot_partitions (area, category, a column, a list of columns or a color; color_by is a deprecated alias), cmap accepts the category dict (palette is deprecated), the background and complement layers use *_facecolor, and plot_dot_density uses markersize and the reference_ layer. No change of output. Stacked on the Voronoi PR.
kind: pr
topic: proportional
branch: feat/plot-vocabulary-proportional
base: feat/plot-vocabulary-voronoi
date: 2026-10-16 01:00
related: plot-vocabulary-voronoi, plot-vocabulary-symbol, plot-vocabulary-flow, style-system
before: main @ 93165f3
after: feat/plot-vocabulary-proportional
inputs: a 3 x 3 grid of squares with two random columns and one random share; plot_partitions on the split partition, plot_dot_density with 20 dots per category.
---

No figures: the change is parameter names. On the 3 x 3 grid the facecolors of the default, `facecolor="category"` with a dict, `facecolor="rv"` (one column) and the dot-density plot, the marker sizes and the base polygons are identical to `main` with the old names (`np.array_equal`).

## Renames

| function | old | new |
|---|---|---|
| `plot_partitions` | `color_by` | `facecolor` (`None`/`"area"`, `"category"`, a column name, a list of columns or a color) |
| `plot_partitions` | `background_color`, `complement_color`, `complement_color_by` | `background_facecolor`, `complement_facecolor` (a column or a color) |
| `plot_partitions`, `plot_dot_density` | `palette` | `cmap` accepts the `{category: color}` dict |
| `plot_dot_density` | `size`, `base_color`, `base_edgecolor`, `base_linewidth`, `base_alpha` | `markersize`, `reference_facecolor`, `reference_edgecolor`, `reference_linewidth`, `reference_alpha` |

## Behavior of `facecolor` in `plot_partitions`

| input | result |
|---|---|
| `None` or `"area"` | partition area, continuous colormap (the default; it does not look up a column named `area`) |
| `"category"` | categorical by partition |
| a column name | all partitions colored by that column (as the one-element list was) |
| a list of columns | one column per partition |
| a color | constant fill, no colorbar or legend |
| a column that is also `"area"`, `"category"` or a color | the column, `UserWarning` |
| any other string | `ValueError` |

When `palette` and a colormap name were both given, the dict now replaces the name and the unlisted categories take the `tab10` colors.

## Checks

Suite 1129 passed, ruff and mypy clean. The proportional gallery examples run without deprecation warnings from the library. The edited notebooks were executed locally without error.
