---
pr: 136
url: https://github.com/bright-fakl/carto-flow/pull/136
title: Landmarks of mixed geometry types
description: Landmarks can combine points, lines and polygons (with holes, multi-part geometries and empties); on main this raised "Point geometries are not supported". Landmark coordinates are now read and written with shapely.get_coordinates and set_coordinates, which also rebuilds the landmark geometries of each snapshot about 30 times faster. Z values are dropped. The figure shows a point, a line, a polygon with a hole and a multipoint carried through a morph of the US states.
kind: pr
topic: flow
branch: fix/mixed-landmarks-coords
base: main
date: 2026-10-15 12:00
related: pr134-prescale-landmarks
before: main @ e78c5a9 (a mix of landmark types raises)
after: fix/mixed-landmarks-coords
inputs: US states (bundled, Population), MorphOptions(grid=128); landmarks: Point, LineString, Polygon with a hole, MultiPoint.
---

`make_figures.py` runs the case in a checkout of main (`before`) and of the fix (`after`) and writes the figure and `data/tables.md`.

figure: fig_mixed.png — Left: the landmarks in the input map. Right: the same landmarks after the morph; the types, the hole and the order are preserved.
