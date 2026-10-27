---
issue: 129, 93
title: Hierarchical flow morph: sub-cell regions with a grid fitted to each group
description: Counties on a grid fitted to each state have 10.8 % of the counties below one cell at 128, 2.3 % at 256, 0.2 % at 512 and none at 1024, against 88.9 %, 67.3 %, 27.4 % and 5.3 % on one global grid. Only Texas (254 counties) has any at 512. This is the first feasibility check of morphing the groups first and the members on group-fitted grids; the stable outline of a group is not tested.
kind: exploration
topic: flow
status: superseded
related: exploration-multires-start, exploration-counties-subcell
date: 2026-10-12 05:10
before: main @ c080423
after: the same checkout; no morph is run
inputs: 3,108 counties (prepared set, ESRI:102008, total_votes, GEOID, not bundled); the target area of a county is its vote share of the total area; a group grid is the square grid with margin 0.5 on the bounding box of the state's original geometry.
closed: 2026-10-27 15:00
---

`group_subcell.py` regenerates `data/tables.md` (the tables below); it reads the counties from `COUNTIES_PARQUET` and runs no morph. It assumes each state ends with the sum of its counties' targets as area, which holds when the state stage has converged.

The tables count counties whose target is below one cell of the grid. The other conditions for the idea (a fixed outline for each group, the error handed down from the group stage, the cost) are listed in issue 129 and not measured here.

## Counties with a target below one cell: one global grid and a grid per state

| grid | global grid | grid fitted to each state | states with at least one such county |
|---|---|---|---|
| 128 | 2762 (88.9 %) | 335 (10.8 %) | 25 of 49 |
| 256 | 2093 (67.3 %) | 73 (2.3 %) | 7 of 49 |
| 512 | 852 (27.4 %) | 6 (0.2 %) | 1 of 49 |
| 1024 | 164 (5.3 %) | 1 (0.0 %) | 1 of 49 |

## Smallest county of the states with the smallest values, in cells of the state grid

| grid | state (counties): smallest county in cells |
|---|---|
| 128 | 48 (254): 0.00851, 16 (44): 0.079, 06 (58): 0.0962, 30 (56): 0.0996 |
| 256 | 48 (254): 0.034, 16 (44): 0.316, 06 (58): 0.385, 30 (56): 0.398 |
| 512 | 48 (254): 0.136, 16 (44): 1.26, 06 (58): 1.54, 30 (56): 1.59 |
| 1024 | 48 (254): 0.545, 16 (44): 5.05, 06 (58): 6.16, 30 (56): 6.38 |
