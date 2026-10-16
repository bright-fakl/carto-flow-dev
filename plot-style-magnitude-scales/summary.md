---
pr: 147
url: https://github.com/bright-fakl/carto-flow/pull/147
issue: 99
title: Scales for the velocity and displacement magnitudes, style palettes for the field plots
description: VelocityPlotOptions(norm=) and the Voronoi plot_displacement(norm=) take a scale (linear, sqrt, log, auto or a Normalize) for the magnitude that sets arrow color, opacity and the colorbar; sqrt joins the color scales. The density and velocity plots and the Voronoi displacement arrows take the palettes of the style, and the flow convergence plots the series colors.
kind: pr
topic: flow, voronoi, infra
branch: feat/plot-style-magnitude-scales
base: main
date: 2026-10-16 22:00
related: plot-style-overlays, plot-style-symbol, style-system
before: main @ aff2719 (equal to style="classic")
after: feat/plot-style-magnitude-scales @ f5efe1c
inputs: bundled US states; a population flow cartogram (grid 64, 30 iterations); a population Voronoi cartogram (RasterBackend 256, 100 iterations).
---

`make_figures.py` draws the plots on the PR branch. The colors of the velocity (color by magnitude, direction, opacity by magnitude, solid), density (none, ratio, difference), convergence and Voronoi displacement plots under `style="classic"` are identical to `main`.

## Scales

figure: fig_velocity_scales.png — Velocity arrows colored by magnitude with `norm` linear, sqrt and log (default style); the colorbar follows the scale.
figure: fig_velocity_alpha_scales.png — Opacity by magnitude with the same three scales.
figure: fig_displacement_scales.png — Voronoi displacement arrows with `norm` linear, sqrt and log; the scale is spread over the arrows that are drawn.

## Palettes of the style

figure: fig_density_palettes.png — Density field in classic (viridis), default and dark: the sequential palette of the style.
figure: fig_density_ratio_palettes.png — Density relative to the mean: the diverging palette of the style (RdBu_r in classic).
figure: fig_velocity_palettes.png — Velocity arrows colored by magnitude: the sequential palette of the style.
figure: fig_convergence.png — Max and mean error lines take the series and highlight colors of the style (C0 and C1 in classic).

figure: fig_velocity_direction.png — Arrows colored by direction: twilight in classic (arrows pointing left are as light as the surface), the cyclic palette hsv in default and dark.

## What changes

| | |
|---|---|
| scales | `VelocityPlotOptions.norm`, `plot_displacement(norm=)` of the Voronoi cartogram (function and method); `"sqrt"` is a color scale everywhere (`PowerNorm(0.5)`) |
| palettes | density cmap (sequential, diverging for ratio and difference), velocity magnitude cmap, Voronoi displacement cmap: the style, then the former default |
| series colors | `plot_convergence` and the workflow convergence plot: `series_color`, `highlight_color` |
| colorbars | the density and velocity colorbars (static plots and animations) are drawn by the style; `legend_kwargs["label"]` replaces the label |
| cyclic palette | `Palettes(cyclic=...)` is a fourth palette role, used for the direction of the velocity: `hsv` in default and dark (the ends of `twilight` are as light or as dark as the surface, so arrows in those directions vanish), `twilight` in classic |
| not yet | `plot_density` of the density module and the anisotropy plots still use plain matplotlib colorbars |

## Checks

Suite 1308 passed, ruff and mypy clean.
