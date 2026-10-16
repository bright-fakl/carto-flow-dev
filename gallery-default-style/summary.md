---
pr: 156
url: https://github.com/bright-fakl/carto-flow/pull/156
issue: 99
title: Gallery examples use the default plot style
description: The gallery examples looked like the classic style because they pinned a palette and limits (14 passed cmap=) and created their own figure (about 20 used plt.subplots with ax=), which leaves the figure white. The examples now let the style set the palette, scale and colorbar, and apply the style to their figures with get_style().apply(fig), so a copied snippet gives the same figure.
kind: pr
topic: infra
base: main
branch: docs/gallery-default-style
date: 2026-10-18 10:00
related: style-system, plot-style-core
before: main @ 028f1e8
after: docs/gallery-default-style @ d6738f7
inputs: the 28 gallery example scripts; each run with the Agg backend before and after.
---

## Why the gallery looked classic

Two causes, found by rendering `plot_flow_cartogram.py` on main (figure facecolor `#ffffff`, palette `RdYlGn_r`, linear scale):

1. An explicit `cmap=`, `vmin` or `vmax` in the call wins over the style, so the palette and the log scale of the style never applied (14 examples passed `cmap=`, 6 passed `vmin`).
2. A plot function that is given `ax=` gives that axes the surface of the style but not the figure that the caller created; with the axes turned off the white figure showed (about 20 examples).

After the change the figure of every example has the surface `#eef1f4` (checked by running all 28 examples).

## Before and after

figure: fig_flow_cartogram.png — Flow cartogram: no pinned palette or limits, log scale and style colorbar.
figure: fig_voronoi_cartogram.png — Voronoi cartogram.
figure: fig_voronoi_premorph.png — The two cartograms are drawn with their own plot methods instead of geopandas.
figure: fig_symbol_flow_density.png — Symbols colored with the sequential palette of the style.
figure: fig_symbol_tiling.png — The tiling uses the reference layer and the stroke color of the style.
figure: fig_symbol_displacement.png — The arrows take the accent color.
figure: fig_symbol_adjacency.png — The links take the sequential palette.
figure: fig_symbol_styling.png — Surface only (the palette was not pinned).
figure: fig_flow_convergence.png — Surface only.
figure: fig_election_shares.png — The palette is kept on purpose (blue for Democratic, red for Republican); the figure has the surface.
figure: fig_election_winners.png — The same for the winner colors.

## What changes

| | |
|---|---|
| palettes | the pins of the examples that draw a carto-flow result are removed (the explicit ones that carry a meaning stay) |
| figures | `get_style().apply(fig)` after every `plt.subplots`, with `from carto_flow import get_style` |
| not changed | the notebooks of the how-to and tutorials have the same two patterns (15 pass `cmap=` or `vmin`) |

## Checks

All 28 examples run; the figure facecolor of each is the surface of the default style; the docs build runs in CI.
