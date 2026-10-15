---
pr: 142
url: https://github.com/bright-fakl/carto-flow/pull/142
issue: 99
title: One resolve_fill for the facecolor of the flow and Voronoi plots
description: The static flow plots and the Voronoi plots each had their own copy of the rules for facecolor (None, a string that is a column, a built-in quantity or a color, a numeric array, a color array). They share resolve_fill in _plot_params.py, which returns (kind, value). The flow animations, the proportional plot_partitions and the symbol plot keep their own handling on top of classify_string. No change of output.
kind: pr
topic: infra
branch: refactor/resolve-fill
base: main
date: 2026-10-16 05:00
related: plot-vocabulary-flow, plot-vocabulary-voronoi
before: main @ 8214930
after: refactor/resolve-fill
inputs: the 49 US states (flow plots, 64 x 64 grid), a 3 x 3 grid (Voronoi plots).
---

No figures: a refactor. The facecolors of the default, column, built-in and array fills of the flow plots and of the categorical, column, `area_error_pct` and comparison plots of the Voronoi module are identical to the output before the change (`np.array_equal`).

| kind | meaning | example |
|---|---|---|
| `none` | no fill given | `None` |
| `column`, `builtin`, `color` | a string, in this order, with a warning when it matches more than one | `"Population"`, `"density"`, `"#d4e6f1"` |
| `values` | numeric array with one value per geometry | `gdf["Population"].to_numpy()` |
| `color` | any other value (an array of colors) | `["red", "blue", ...]` |

Each module passes its own built-in names and decides what `none` means (flow: the errors, Voronoi: categorical by index). Tests: `test_resolve_fill_kinds`, the flow and Voronoi vocabulary tests and the Voronoi suite (104 passed); ruff and mypy clean.
