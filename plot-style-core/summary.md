---
pr: 143
url: https://github.com/bright-fakl/carto-flow/pull/143
issue: 99
title: PlotStyle sets the look of the flow plots and animations
description: PR A of the style system. A frozen PlotStyle (matplotlib rc dict, palettes by data role, channels, color scale, colorbar fields) with the built-in styles default (the new look), dark and classic (the look before styles), a registry, style=, style_context and set_style. The flow plots and animations take style=, norm=, center= and categorical=, the data role is decided by the data, and a log colorbar has real-number ticks. morph_timeline builds the keyframes of a hold, eased morph, hold and return. The default look of every flow plot changes; style="classic" gives the earlier look.
kind: pr
topic: flow, infra
branch: feat/plot-style
base: main
date: 2026-10-16 09:00
related: style-system, plot-vocabulary-flow
before: main @ b6a7810 (equal to style="classic")
after: feat/plot-style @ 4cc98b1
inputs: bundled US states with population, MorphOptions.preset_balanced(area_scale=1e-6, n_iter=400); the same plot in the styles classic, default and dark.
---

`make_figures.py` draws each plot in the three styles on the PR branch. `classic` is the look before this PR: the facecolors of the default, `Population` and `density` plots are identical to `main`, and the first frame of the workflow and keyframe animations is pixel-identical. Judge the new default look on the figures below.

## Palettes of the built-in styles

figure: fig_palettes.png — The sequential, diverging and categorical palettes of classic (the former `RdYlGn_r` for everything), default (`YlGnBu` truncated to 0.22-1.0, `RdYlBu_r`, `tab10` mixed 15 % toward the surface) and dark (`viridis` truncated to 0.25-1.0, `RdYlBu_r`, `tab10`).

## Plots

figure: fig_population.png — Population: classic (linear colorbar in scientific notation), default (tinted surface, log colorbar with ticks at 1, 2 and 5 per decade written 1M, 2M, 5M, outlined colorbar) and dark.
figure: fig_errors.png — Area errors: classic (`RdYlGn_r`, range of the data) and default and dark (diverging `RdYlBu_r`, symmetric around 0).
figure: fig_categorical.png — Region (a text column): classic draws the categories with `RdYlGn_r`; default and dark use the categorical palette of the style.
figure: fig_density.png — Population density.
figure: fig_comparison.png — `plot_comparison`: classic and default; the two panels share the normalization of the values of both.
figure: fig_animation_frame.png — A frame of `animate_geometry_keyframes` (Population, `legend=True`).

## What a call can do

| call | effect |
|---|---|
| `cartogram.plot(facecolor="Population", style="dark")` | one plot in a style |
| `with style_context("dark"): ...`, `set_style("dark")` | a block, the session |
| `facecolor="Population", norm="log"` | a normalization of the call; also a `Normalize` instance |
| `facecolor="Population", center=1e7` | diverging around the center |
| `facecolor="STATE", categorical=True` | the categorical role for numeric data |
| `cmap="Reds"` | wins over the palette of the style |
| `style=("dark", talk_fonts)`, `PlotStyle.dark() \| talk_fonts` | a sequence of styles, or `a \| b`: what the right style sets wins; `rc`, palettes and channels merge field by field |
| `facecolor="Population", vmin=0, vmax=3e7` | the limits fix a linear normalization; with `norm="log"` they are the limits of the log scale; with a `Normalize` instance they raise |
| `norm="linear"`, `color_scale="linear"`, `log_span=3` | keep a linear scale for data that spans more than one decade |
| `morph_timeline(cartogram)` | keyframes and times of hold, eased morph, hold, return |

## Checks

Suite 1191 passed, ruff and mypy clean; the flow gallery examples and the eight flow notebooks run without error. Tests cover the style fields and validation, the palettes and norms, the colorbar ticks, the selection order (call, block, session, default), thread isolation, rcParams restored after an exception, the classic look against plain geopandas, the roles, the shared normalization of the comparison, the animation frames after the axes is cleared, the saved frame color and `morph_timeline`, merging and sequences of styles, and the limits of a call.

## Not in this PR

`defaults`, the reference layer, annotation sizes and the hatch, alpha and per-channel palette use (they need the symbol plot), `to_dict` / `from_dict`, and the symbol, Voronoi and proportional plots (PR B). Saving an animation to a directory of PNG frames writes no frames, on `main` as well.
