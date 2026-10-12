---
pr: 125
url: https://github.com/bright-fakl/carto-flow/pull/125
issue: 85, 109
title: Valid output regions of the flow cartogram, repaired by default
description: A region that is much narrower than a grid cell somewhere can be pinched during the morph until its boundary crosses itself, and the computed region is then not a valid polygon. The morph now warns and lists the regions (Cartogram.invalid_regions); shapely.make_valid repairs them on request in to_geodataframe but adds vertices, which breaks keyframe animations, so the computed geometries keep the vertices of the input. Vertex-preserving options (a nudge, input densification) are measured.
kind: pr
topic: flow
branch: fix/output-validity
base: main
date: 2026-10-11 20:06
related: exact-ring-orientation, adaptive-step-control
before: main @ c24907e (output returned as computed)
after: fix/output-validity @ 4ab1f28
inputs: US states (49 incl. DC) and congressional districts (432), bundled; the minority-population map of issue 85 (states simplified by 1000 m, grid 512); 3,108 counties (prepared set, ESRI:102008, total_votes, area_scale 1e-6, not bundled). MorphOptions defaults except where stated; NUMBA_NUM_THREADS=8. The repair is shapely.make_valid, keeping the polygonal parts with more than a millionth of the area.
---

`make_figures.py` regenerates the figure and `data/tables.md`; the counties rows run when `COUNTIES_PARQUET` points at a GeoDataFrame file with `total_votes` and `geometry`.

## What goes wrong

Vertices move independently, so a region that is much narrower than a grid cell somewhere (a thin neck) can be pinched until one part of its boundary passes the other and the boundary crosses itself. The returned region is then not a valid polygon; nothing in the result said so, and anything downstream (overlays, exports, `partition_geometries`) can misbehave. Issue 85 shows it for Maryland on the minority-population map: the morph converges, the output is invalid from iteration 181 on, and `partition_geometries` returns empty parts for it without an error.

figure: maryland.png — Maryland of the issue's map, a window of 0.24 x 0.24 grid cells around the first self-intersection (red cross). Left: the last valid iteration, a thin neck of the region (shaded) between two parts of its own boundary. Middle: the vertex has crossed the opposite bank. Right: after the repair.

Maryland (issue 85) is valid up to snapshot 180 and invalid from snapshot 181 of 233. At the crossing the closest pair of non-adjacent vertices of the previous iteration is 0.0174 grid cells apart; the vertices there move 0.0204 cells per iteration (maximum 0.0227). The crossing is 0.000 cells from the ring of the part it belongs to (771 vertices, 562 cells^2).

The input geometries are valid in every run below; the crossings come from the morph.

## How common it is

| run | status, iterations | invalid regions | regions with another part count after the repair | area change of the repaired regions: median / max | check + repair time (ms) |
|---|---|---|---|---|---|
| states, grid 256 | converged, 112 | 0 of 49 | | | 5.5 |
| states, grid 512, 0.2 % / 0.4 % | converged, 229 | 0 of 49 | | | 5.6 |
| districts, grid 256 | converged, 145 | 12 of 432 | 9 | 0.0178 % / 0.179 % | 36.1 |
| districts, grid 256, 0.5 % / 1 % | converged, 160 | 12 of 432 | 9 | 0.0274 % / 0.240 % | 35.3 |
| districts, grid 512, 0.5 % / 1 % | stalled, 310 | 19 of 432 | 11 | 0.0027 % / 7.678 % | 40.9 |
| issue 85: minority population, simplified states, grid 512 | converged, 234 | 1 of 49 | 1 | 0.0003 % / 0.000 % | 13.2 |
| counties, grid 256 | stalled, 210 | 7 of 3108 | 3 | 0.0002 % / 0.037 % | 28.4 |
| counties, grid 512 | completed, 300 | 51 of 3108 | 35 | 0.0169 % / 2.915 % | 53.9 |


The states stay valid in every run tried; the districts and the counties end with 12 to 51 invalid regions at the larger grids and the tighter tolerances (the stalled district run at grid 512 is the exception to the small area change: one region changes by 7.7 %). Most repairs leave the part count of a Polygon region unchanged; a region with a pinched lobe of zero area loses the lobe, and a bowtie becomes a MultiPolygon of two parts. The check is one `shapely.is_valid` call per morph and the repair touches only the invalid regions; both are included in the time column.

## What changes

- The morph warns when regions of the returned iterate are invalid, and `Cartogram.invalid_regions` lists them.
- `MorphOptions.repair_output` (default `False`): `Cartogram.to_geodataframe` makes the invalid regions valid with `shapely.make_valid` (zero-area parts dropped). The repair adds vertices, so it is off by default: the keyframe animations between cartograms (the population-over-years example) interpolate vertex by vertex and failed in the docs build when the repaired region had two more vertices than in the other keyframes. `get_geometry` and the snapshots are never repaired.
- `partition_geometries` repairs invalid input geometries with `shapely.make_valid` and warns with the rows; it returned empty or wrong parts before.

## Where the crossings happen

For each region that ends invalid, the gap between the two closest non-adjacent boundary vertices just before the first invalid iteration (`crossing_sites.py`): is its midpoint inside the region itself, inside another region, or outside all regions?

| run | invalid regions | inside the region itself (thin neck pinching) | inside a neighboring region | outside all regions (water or a gap) |
|---|---|---|---|---|
| issue 85 map, grid 512 | 1 | 1 | 0 | 0 |
| districts, grid 256 | 12 | 8 | 4 | 0 |
| districts, grid 512, 0.5 % / 1 % | 21 | 14 | 7 | 0 |
| counties, grid 256 | 62 | 51 | 10 | 1 |
| counties, grid 512 | 55 | 42 | 12 | 1 |

The crossings are almost never across water: they are regions pinched at a thin neck (the region itself lies between the two boundary points), and in 7 to 20 % of the cases a thin wedge of a neighboring region is squeezed between two parts of the boundary. Maryland on the map of issue 85 is a pinched neck (the gap before the crossing is 0.017 grid cells); the median gap over the districts and counties is 0.03 to 0.18 cells. (The counts of invalid regions differ slightly from the table above because the runs here store every iteration.)

## A repair that keeps the vertices (prototype, not in the PR)

A vertex-preserving repair moves the vertex that has crossed an edge back to the other side of that edge (the endpoint of the crossing segments with the smallest distance to the other segment; one pass per crossing, up to 20 passes). It keeps the vertex count and order. On the final geometries of the runs above:

| run | invalid regions | valid after the nudge | area change: median / max | largest vertex move (grid cells) |
|---|---|---|---|---|
| issue 85 map | 1 | 1 | 0.00004 % / 0.000 % | 0.001 |
| districts, grid 256 | 12 | 10 | 0.009 % / 0.43 % | 0.046 |
| districts, grid 256, 0.5 % / 1 % | 12 | 8 | 0.015 % / 0.39 % | 0.036 |
| districts, grid 512, 0.5 % / 1 % | 19 | 15 | 0.005 % / 2.9 % | 0.38 |
| counties, grid 256 | 7 | 3 | 0 % / 0.012 % | 0.001 |
| counties, grid 512 | 51 | 33 | 0.03 % / 8.5 % | 0.046 |

It leaves 4 to 18 regions per run invalid (touching rings, several crossings at one vertex), so it is not a repair that can be on by default without more work. Preventing the crossings during the morph (limiting the step of a vertex by its distance to the nearest boundary) would keep every geometry valid and the vertices unchanged; a 2025 paper on topology-preserving line densification for flow-based cartograms ([arXiv 2511.08121](https://arxiv.org/abs/2511.08121)) takes another route to the same guarantee.

## Densifying the input (`densify_check.py`)

The 2025 paper on topology-preserving line densification for flow-based cartograms ([arXiv 2511.08121](https://arxiv.org/abs/2511.08121)) inserts vertices where polygon edges cross the triangles of a Delaunay triangulation, so that each segment is mapped affinely; its vertex count rises by 62 % on average (median 20 %), the output is simplified afterwards, and the guarantee is a proof sketch for a one-shot projection of the polygons, not for a step-by-step advection like this one. A deterministic version that keeps the vertex count identical across maps of the same input is to densify the input once (`densify_coverage`). Invalid output regions after densifying to a maximum segment length of 0.5 to 0.1 grid cells:

| run | input | 0.5 cell | 0.25 cell | 0.1 cell | vertices at 0.1 cell (input) |
|---|---|---|---|---|---|
| issue 85 map, grid 512 | 1 | 1 | 1 | 0 | 80,988 (34,510) |
| districts, grid 256 | 12 | 12 | 12 | 4 | 137,250 (92,202) |
| districts, grid 512, 0.5 % / 1 % | 19 | 19 | 14 | 2 | 217,965 (92,202) |
| counties, grid 512 | 51 | 51 | 36 | 10 | 484,063 (193,857) |

Densifying to 0.1 cell reduces the crossings a lot but does not remove them (and the districts at grid 512 converge in 278 iterations at 0.1 cell although they stall without densifying); the run time grows with the vertex count (counties at grid 512: 3.5 s to 5.7 s).

## Not included

- The crossings are not prevented; the iterations of the morph are unchanged, and the error metrics of the run still use the signed area of the unrepaired ring (the difference is the area change in the table).
- Input validation is #78.
