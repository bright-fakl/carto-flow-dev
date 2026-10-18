---
pr: 175
url: https://github.com/bright-fakl/carto-flow/pull/175
issue: 174
title: Densify at load time with max_segment_length
description: load_us_census(max_segment_length=...) densifies the bundled boundaries so that no segment exceeds the given length, with identical vertices on both sides of a shared boundary. The county gallery example uses it.
kind: pr
topic: data
base: main
branch: feat/census-max-segment-length
date: 2026-10-19 23:00
before: main @ 08f3edf
after: feat/census-max-segment-length @ 5773846
related: segment-density-warning, census-county-level
inputs: bundled states, congressional districts and counties (ACS 2020 snapshot).
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
