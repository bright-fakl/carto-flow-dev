---
pr: 175
url: https://github.com/bright-fakl/carto-flow/pull/175
issue: 174
title: Densify at load time with max_segment_length (all geometry loaders)
description: load_us_census, load_world and load_us_states take max_segment_length, which densifies the boundaries so that no segment exceeds the given length, with identical vertices on both sides of a shared boundary. The census data is in meters, the world and US states data in degrees, where densifying before projecting follows the graticule. The county gallery example uses it.
kind: pr
topic: data
base: main
branch: feat/census-max-segment-length
date: 2026-10-19 23:00
before: main @ 08f3edf
after: feat/census-max-segment-length @ e539ba0
related: segment-density-warning, census-county-level
inputs: bundled states, congressional districts and counties (ACS 2020 snapshot), world (177 countries) and US states (51), both EPSG:4326.
---

## Behavior

| call | segments | counties: vertices |
|---|---|---|
| `load_us_census(level="county")` | at most 5 km (4,999.6 m) | 193,856 |
| `max_segment_length=5000` or more | unchanged | 193,856 |
| `max_segment_length=2000` | at most 1,999.9 m | 451,364 |
| `max_segment_length=1000` | at most 999.97 m | 768,580 |

- The result has the same rows, columns and CRS, valid geometries, and the same total area; the shared boundaries of the coverage stay identical.
- Non-positive, boolean or non-numeric values raise `ValueError`.
- The county gallery example loads with `max_segment_length=1000` (median error 0.26 %, 95th percentile 2.9 %, mean 1.7 %), replacing its explicit `densify_coverage` call.
- Densification is applied after the contiguous filter, so Alaska, Hawaii and Puerto Rico are not densified unless requested.

## World and US states, in degrees

The world and US states datasets are in EPSG:4326, so `max_segment_length` is in degrees (a degree is about 111 km). Degrees are better than a projected length here: the vertices are inserted on straight lines in longitude and latitude, and a border along a parallel then curves correctly after the projection, whereas densifying after projecting only subdivides the straight chord. On 6 degrees of the 49th parallel the parallel is 3.5 km away from the chord between its projected ends in EPSG:5070.

| dataset | longest segment | `max_segment_length=0.1` | vertices |
|---|---|---|---|
| world, 177 countries | 1.0 degrees | 0.1 degrees | 14,541 to 98,411 |
| US states, 51 | 5.7 degrees | 0.1 degrees | 2,366 to 12,177 |

Both stay valid and keep the total area; a value at or above the longest segment changes nothing. `load_sample_cities` has points and takes no argument.
