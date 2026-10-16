---
pr: 157
url: https://github.com/bright-fakl/carto-flow/pull/157
title: README figure and text up to date
description: The README predated the style system and several cartogram types. Its figure is drawn again in the default plot style (scripts/make_readme_figure.py), its overview lists five cartogram types instead of three, its quick example is replaced by one that runs on the bundled data (the old one used arguments and attributes that do not exist), and the docs home page says Python 3.10+ instead of 3.9+.
kind: pr
topic: infra
base: main
branch: docs/readme-figure
date: 2026-10-18 12:00
related: gallery-default-style, style-system
before: main @ 8cbe591
after: docs/readme-figure @ 7fa5abf
inputs: bundled US states with population, race and poverty counts (simplify 1000); the flow morph with the defaults; a hexagon grid symbol cartogram; the split partition of three groups; 1000 dots.
---

## Figures

figure: fig_before.png — The figure of main (1000 x 600, 225 KiB): classic style.
figure: fig_after.png — The new figure (1430 x 880, 386 KiB): the default plot style, the same four panels.

## What changes

| | |
|---|---|
| figure | `cartogram-example.png` redrawn; the README links it by its raw URL, so GitHub and PyPI show the new one after the merge |
| script | `scripts/make_readme_figure.py` draws it |
| overview | five cartogram types (flow, symbol, Voronoi, non-contiguous, proportional with dot density) instead of three |
| quick example | the old one (`create_flow_cartogram(gdf, values=...)`, `result.cartogram_gdf`, `create_symbol_cartogram(gdf, values=...)`) did not run; the new one runs on the bundled US states for the flow, symbol, Voronoi and non-contiguous cartograms and mentions `style=` |
| features and links | the Voronoi and non-contiguous cartograms, mosaic tile-count maps, plot styles, animations and bundled data are listed; the gallery is linked |
| docs home | `docs/index.md`: Python 3.10+ (it said 3.9+), the two cartogram types and the plot styles added |

## Checks

The script runs; the figure was checked by eye; the quick example was run end to end (the four cartograms and `style="dark"`); the docs build runs in CI.
