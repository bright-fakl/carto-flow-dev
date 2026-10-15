---
pr: 141
url: https://github.com/bright-fakl/carto-flow/pull/141
issue: 99
title: Name the flow animation variables after the vocabulary parameters
description: Follow-up to the flow parameter vocabulary. The animations that take facecolor, legend, legend_label and legend_kwargs kept the old names as local variables through assignments at the top of each function; the variables now use the new names and the aliasing lines are gone. No change of behavior.
kind: pr
topic: flow
branch: refactor/flow-animation-names
base: main
date: 2026-10-16 03:00
related: plot-vocabulary-flow
before: main @ 93165f3
after: refactor/flow-animation-names
inputs: the flow vocabulary tests and the flow animation gallery examples.
---

No figures: a rename of local variables. The three animations (`animate_morph_history`, `animate_geometry_keyframes`, `animate_workflow`) and the helper `_create_patch_collection` use `facecolor`, `legend`, `legend_label` and `legend_kwargs` throughout; `resolved_colorbar_label` is `resolved_legend_label`. The messages of the errors that named `color_by` say `facecolor`. `column` and `color_values` in `animate_geometry_keyframes` stay: they are the resolved column and the resolved arrays, not aliases of a parameter.

Checks: ruff, mypy and the vocabulary tests pass; CI runs the full suite. The same cleanup was done in the symbol PR (the legend and label variables of `plot_symbols`) and in the proportional PR (the derived background and complement variables).
