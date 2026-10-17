---
pr: 169
url: https://github.com/bright-fakl/carto-flow/pull/169
issue: 129, 166, 167
title: County level for load_us_census
description: load_us_census(level="county") returns 3,108 contiguous counties from a bundled ACS 2020 snapshot (2.9 MB), with population, race and poverty columns. Black and Asian counts are zero in 95 and 258 counties, which makes them a second, harder value distribution for county flow cartograms.
kind: pr
topic: data
base: main
branch: feat/county-census-level
date: 2026-10-19 00:30
before: main @ cf7d1bb
after: feat/county-census-level @ 55cf978
inputs: ACS 5-year 2020 via censusdis (scripts/build_census_snapshot.py, new county level); ESRI:102008, coverage-simplified at 1000 m, densified to 5 km segments.
---

## Figures

figure: fig_counties.png — Population density and the Asian share of the 3,108 contiguous counties as loaded by `load_us_census(level="county", race=True)`.

## Dataset

- 3,221 rows in the bundled file (all states, DC and Puerto Rico); `contiguous_only=True` (default) drops Alaska, Hawaii and Puerto Rico and keeps DC, giving 3,108.
- Columns as for the state level plus `County Name`, `COUNTY` (the county FIPS part) and `State Name`; `Region` and `Division` as before.
- Geometries are valid as loaded and after `simplify=2000` (the data validity tests cover all three loads).

## Value distributions in the bundled counties

| column | minimum | median | maximum | counties with 0 |
|---|---|---|---|---|
| Population | 117 | 26,028 | 10,040,682 | 0 |
| White | 12 | 20,095 | 2,603,280 | 0 |
| Black or African American | 0 | 801 | 1,184,373 | 95 |
| Asian | 0 | 151 | 1,467,279 | 258 |
| Hispanic or Latino | 0 | 1,130 | 4,851,344 | 16 |

Population is a mild case (a range of five orders of magnitude). The race columns have zeros and a much heavier tail, so they test the zero-value handling of the flow cartogram, which is a separate known limitation.
