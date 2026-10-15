---
pr: 137
url: https://github.com/bright-fakl/carto-flow/pull/137
issue: 99
title: One parameter vocabulary for the flow plot, animate and preview functions
description: First part of the parameter vocabulary of the style-system proposal. facecolor is the fill (a column, a built-in quantity, an array or a color) of the flow plots and animations, replacing column, color_by and color_values; colorbar, colorbar_label and colorbar_kwargs become legend, legend_label and legend_kwargs. Old names stay as deprecated aliases. Strings resolve as column, then built-in quantity, then color, with a warning on ambiguity. No change of output. The symbol, Voronoi and proportional modules follow in separate PRs.
kind: pr
topic: flow
branch: feat/plot-vocabulary-flow
base: main
date: 2026-10-15 18:00
related: style-system
before: main @ 8f3d49b
after: feat/plot-vocabulary-flow @ ce479e1
inputs: bundled US states, MorphOptions(grid=64, n_iter=20); the flow gallery examples plot_flow_animation, plot_flow_animation_density, plot_flow_animation_velocity.
---

No figures: the change is parameter names and the resolution of string arguments; the output is unchanged. On the bundled states the facecolors of the default plot, `facecolor="Population"` and `facecolor="density"` are identical to `main` with `column=` (`np.array_equal` on the RGBA arrays of the collection).

## Renames

| function | old | new |
|---|---|---|
| `Cartogram.plot`, `plot_cartogram`, `plot_comparison` | `column` | `facecolor` |
| `animate_morph_history`, `animate_workflow` | `color_by` | `facecolor` |
| `animate_geometry_keyframes` | `column`, `color_values` | `facecolor` |
| the three animations above | `colorbar`, `colorbar_label`, `colorbar_kwargs` | `legend`, `legend_label`, `legend_kwargs` |
| `Cartogram.plot`, `plot_cartogram` | `legend_kwds` | `legend_kwargs` |
| both `preview_modulator` functions | `show_colorbar`, `colorbar_kwargs`, `diff_colorbar_kwargs`, `heatmap_colorbar_kwargs` | `legend`, `legend_kwargs`, `diff_legend_kwargs`, `heatmap_legend_kwargs` |
| `DensityPlotOptions`, `VelocityPlotOptions` | `colorbar`, `colorbar_kwargs` | `legend`, `legend_kwargs` |

## Behavior

| input | result |
|---|---|
| `facecolor="Population"` (a column) | data fill |
| `facecolor="errors_pct"`, `"density"` | built-in quantity (static plots: the columns `_morph_error_pct`, `_morph_density`) |
| `facecolor="#d4e6f1"` | constant fill; with `legend=True` in an animation no colorbar is drawn (one axes, checked) |
| a column that is also a built-in quantity or a color | read as the column, `UserWarning` |
| a string that is none of these | `ValueError` (before: `column="typo"` drew an uncolored map without a message) |
| old name | works, `DeprecationWarning`; old and new together raise `TypeError` |

## Checks

Suite 1101 passed, ruff and mypy clean. The three flow gallery examples run without deprecation warnings from the library. The edited notebooks were not executed.
