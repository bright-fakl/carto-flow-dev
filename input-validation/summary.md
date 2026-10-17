---
pr: 160
url: https://github.com/bright-fakl/carto-flow/pull/160
issue: 78
title: Input validation with clear errors
description: validate_geometries reports null, empty and invalid geometries, bad values, overlapping polygons and repeated vertices by row label; the flow, Voronoi and non-contiguous cartograms run it first and raise a ValueError for errors before the run.
kind: pr
topic: flow, voronoi, noncontiguous, infra
base: main
branch: feat/validate-geometries
date: 2026-10-17 12:00
before: main @ b57f75b
after: feat/validate-geometries @ c996c60
inputs: bundled US states (EPSG:5070) with one polygon replaced by a bowtie or one value set to NaN; bundled world (EPSG:8857) for the coverage check.
---

## What the check reports

| issue | severity | rows named | how it is found |
|---|---|---|---|
| null or empty geometry | error | yes | `shapely.is_missing`, `shapely.is_empty` |
| invalid geometry | error | yes, with the reason | `shapely.is_valid_reason` |
| value missing, infinite or negative (zero where it is not allowed) | error | yes | NumPy on the data column |
| column not found | error | | |
| polygon overlaps a neighbor or shares an edge that does not match | warning, with `coverage=True` | yes | `shapely.coverage_invalid_edges` |
| coordinates in longitude and latitude (geographic CRS) | warning | no (whole input) | `crs.is_geographic` |
| repeated consecutive vertices | information only | yes | `shapely.remove_repeated_points` |

The report is a `GeometryReport`; `raise_for_errors()` raises one `ValueError` that lists all errors, `warn()` issues a `UserWarning` for each warning.

## Messages on real data

| input | before | after |
|---|---|---|
| US states, one polygon replaced by a bowtie | `GEOSException: IllegalArgumentException: Points of LinearRing do not form a closed linestring`, from inside the morph | `ValueError: invalid input: Invalid geometry (first: Self-intersection[0.5 0.5]) in 1 row: 0. Repair with shapely.make_valid or carto_flow.geo_utils.repair_polygons.` |
| US states, one value NaN | the same `GEOSException`, after the morph produced NaN coordinates | `ValueError: invalid input: Value is missing, infinite or negative in 1 row: 3. Fix or drop these rows.` |
| world, flow cartogram | no message | `UserWarning: Polygon overlaps a neighbor or shares an edge that does not match in 3 rows: 14, 165, 176. Neighbors may be missed and the result may overlap; see shapely.coverage_invalid_edges.` |
| bundled world in EPSG:4326 | no message | `UserWarning: The coordinates are longitude and latitude (EPSG:4326), so areas are in square degrees and distorted. Project the data first, ...` |
| bundled US states, census, flow cartogram | no message | no message (6 states have repeated vertices; reported as information only) |

## Where it runs

`create_flow_cartogram`, `CartogramWorkflow`, `create_voronoi_cartogram` and `create_noncontiguous_cartogram`, with `validate=False` to skip. Zero values are accepted, as before (flow shrinks the region; Voronoi has its own message).

Left out: the symbol cartogram works on centroids and areas, and its tests cover degenerate polygons and null sizes, so an invalidity error would be wrong there; the partition functions already repair invalid polygons with a warning; the extreme value ratio from the issue is not included (any cutoff is arbitrary, and the convergence status already reports a region that cannot reach its target). The mosaic layout's internal morph passes `validate=False`, and so does the Voronoi pre-morph, which has been checked already.

## Checks

Suite 1400 passed, ruff clean, mypy shows only the errors of the untracked old `mosaic_cartogram` module. Cost: 0.01 s for the 177 countries, 0.02 s for the 49 census states.
