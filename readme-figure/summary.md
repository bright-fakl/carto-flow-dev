---
pr: 157
url: https://github.com/bright-fakl/carto-flow/pull/157
title: README figure in the default plot style
description: The figure of the README (cartogram-example.png) predates the style system (white background, RdYlGn_r and viridis palettes, grey separators). It is drawn again in the default plot style by scripts/make_readme_figure.py, with the same four panels of the US states.
kind: pr
topic: infra
base: main
branch: docs/readme-figure
date: 2026-10-18 12:00
related: gallery-default-style, style-system
before: main @ 8cbe591
after: docs/readme-figure @ 21a2cc0
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
| not changed | the README text still says that carto-flow supports three cartogram styles, without the Voronoi and the non-contiguous cartograms |

## Checks

The script runs; the figure was checked by eye.
