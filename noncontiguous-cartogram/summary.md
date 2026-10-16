---
pr: 148
url: https://github.com/bright-fakl/carto-flow/pull/148
issue: 76
title: Non-contiguous (Olson) cartogram
description: New noncontiguous_cartogram module with create_noncontiguous_cartogram(gdf, column): every region keeps its shape and is scaled about its centroid to an area proportional to its value. reference sets the density (densest, largest, or a number), max_scale limits growth, multipart scales a multipolygon as a group or by part. The result has plot(style=) over the original outlines.
kind: pr
topic: noncontiguous, infra
branch: feat/noncontiguous-cartogram
base: main
date: 2026-10-17 10:00
related: plot-style-magnitude-scales, style-system
before: main @ aff2719
after: feat/noncontiguous-cartogram @ 5d8e795
inputs: bundled US states (simplify=1000), population; Michigan for the multipolygon modes.
---

`make_figures.py` draws the figures on the PR branch.

## Reference density

figure: fig_references.png — US states by population. Left: the default reference (the densest region, DC): nothing grows, every area is proportional to the population, and 43 of 49 states are below 5 % of their area. Middle: the reference of the region with the largest value (California) with growth capped at the original size: the 11 denser states keep their original size and are smaller than proportional to their population, and the other states are scaled relative to California. Right: the same reference without the cap: New Jersey grows to 4.6 times its area and DC to 41.6 times.

The default is the only reference under which every area is proportional without growth; for US population it makes most states very small. A float reference or `reference="largest"` with the cap gives a more readable map at the price of capped states.

figure: fig_reference_region.png — `reference_region` set to New Jersey: only DC is denser than the reference. Middle: DC is kept at its size (smaller than proportional); right: DC grows to 3.0 times its linear size. The median scale is 0.30 (0.10 with the default) and 16 states are below 5 % of their area (43 with the default). Regions are drawn largest first, so the grown DC lies under its neighbors.

## Multipolygons

figure: fig_multipart.png — Michigan (111 parts) at a scale of 0.5. `"group"` (default) is a smaller copy of the whole state, so the upper peninsula stays at its distance in proportion; `"parts"` keeps each part at its place and the gap between the peninsulas grows relative to them.

## Styles

figure: fig_styles.png — The default reference colored by region in classic, default and dark: the reference fill of the style for the original outlines.

## What changes

| | |
|---|---|
| new module | `carto_flow.noncontiguous_cartogram`: `create_noncontiguous_cartogram(gdf, column, *, reference, max_scale, multipart)`, `NoncontiguousCartogram` (`geometries`, `source`, `scale`, `capped`, `reference_density`, `area_error_pct`, `to_geodataframe()`, `plot()`), `plot_cartogram` |
| reference | `reference_region=<index label>` sets the density of that region as the reference (not combinable with `reference`) |
| drawing order | regions are drawn in order of decreasing area, so a region that grew does not hide the smaller ones |
| shared code | `fill_plan` in `carto_flow/_fill.py` resolves `facecolor` into a `Fill` for the flow and non-contiguous plots (built-in quantities, labels and diverging columns are arguments); the flow plots are unchanged (classic output identical to `main`). The Voronoi `_fill_of` is not folded in: it builds its cells from arrays and colors by index for `facecolor=None` |
| docs | reference section, explanation page, gallery example, changelog |
| not yet | `method="shrink"` (depends on #74); labels in the plot |

## Checks

Suite 1373 passed, ruff and mypy clean; the gallery example runs.
