---
pr: 156
url: https://github.com/bright-fakl/carto-flow/pull/156
issue: 99
title: Gallery examples and notebooks use the default plot style
description: The gallery examples and the how-to and tutorial notebooks looked like the classic style because they pinned a palette and limits (cmap=, vmin=, vmax=) and created their own figure with plt.subplots and ax=, which leaves the figure white. They now let the style set the palette, scale and colorbar, and apply the style to their figures with get_style().apply(fig), so a copied snippet gives the same figure. Every figure of the 28 examples and the 19 notebooks has the surface of the default style.
kind: pr
topic: infra
base: main
branch: docs/gallery-default-style
date: 2026-10-18 10:00
related: style-system, plot-style-core
before: main @ 028f1e8
after: docs/gallery-default-style @ 8b3ee02
inputs: the 28 gallery example scripts and the 19 how-to and tutorial notebooks; each run with the Agg backend before and after.
---

## Why the gallery and the notebooks looked classic

Two causes, found by rendering `plot_flow_cartogram.py` on main (figure facecolor `#ffffff`, palette `RdYlGn_r`, linear scale):

1. An explicit `cmap=`, `vmin` or `vmax` in the call wins over the style, so the palette and the log scale of the style never applied (14 examples passed `cmap=`, 6 passed `vmin`).
2. A plot function that is given `ax=` gives that axes the surface of the style but not the figure that the caller created; with the axes turned off the white figure showed (about 20 examples).

After the change the figure of every example and of every notebook cell has the surface `#eef1f4` (checked by running all 28 examples and all 19 notebooks; on main the figures of the notebooks were white).

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

## Notebooks

figure: fig_nb_basic_flow.png — Tutorial: the original map and the cartogram with the sequential palette of the style.
figure: fig_nb_basic_voronoi.png — Tutorial: the Voronoi cartogram without the pinned palette and colorbar.
figure: fig_nb_save_export.png — How-to: the original and the reloaded cartogram, plotted with `Cartogram.plot`.
figure: fig_nb_reduce_boundary.png — How-to: the results of the prescaling comparison, plotted with `Cartogram.plot` instead of `to_geodataframe().plot`.
figure: fig_nb_style_symbols.png — How-to: the symbols without the pinned `YlOrRd`.
figure: fig_nb_choose_backend.png — How-to: the area error of the two backends on the diverging palette of the style, without the fixed limits.

## What changes

| | |
|---|---|
| palettes | the pins of the examples that draw a carto-flow result are removed (the explicit ones that carry a meaning stay) |
| figures | `get_style().apply(fig)` after every `plt.subplots`, with `from carto_flow import get_style` |
| notebooks | `get_style().apply(fig)` after the 51 `plt.subplots` calls of 18 notebooks (with the import); the pins of the carto-flow plots removed; plain GeoDataFrame plots of the original geography use `cmap=get_style().colormap("sequential")`; the JSON of the notebooks is edited line by line, not re-serialized |
| left explicit | meaningful palettes (election colors, category dictionaries, dot density), the covid and population-evolution encodings, the error colormap with caps of the multiresolution tutorial, the benchmark charts of the performance page, lightblue symbols of the adjacency example |

## Checks

All 28 examples and 19 notebooks run; the figure facecolor of each is the surface of the default style; the docs build (which executes the notebooks) runs in CI.
