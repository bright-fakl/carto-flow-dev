---
pr: 132
url: https://github.com/bright-fakl/carto-flow/pull/132
issue: 93, 109
title: n_iter is the total number of iterations of a ladder of resolutions
description: A ladder (LadderSpec or "auto" in MorphOptions.grid) shares one iteration total: each level may use what the previous levels left, and the ladder stops when the total is used up. A list of options keeps one n_iter per level. Ladders that end before the total (states, districts) are unchanged; counties at 500 iterations stop at grid 1024 and the districts with smooth sigma-2 values end completed.
kind: pr
topic: flow
branch: feat/ladder-iteration-pool
base: main
date: 2026-10-13 00:30
related: exploration-multires-stall, pr128-multires-auto-resolution
before: main @ 5a4a5a2
after: feat/ladder-iteration-pool @ 29c00df
inputs: the cases of exploration-multires-stall (states with area-like and lognormal sigma-2 values, districts with smooth sigma-2, inverse-area and population values, 3,108 counties not bundled); tolerances 1 % / 3 %, n_iter 500, adaptive_dt on, NUMBA_NUM_THREADS=8. True error is the output area against the target share of the total output area.
---

`make_tables.py` regenerates `data/tables.md`. "Per level" is the ladder with a list of options (500 iterations for every level, the old behavior); "total" is a single `MorphOptions` with `n_iter=500`. There are no figures.

| case | n_iter | per level (list of options) | total (single options) |
|---|---|---|---|
| states-area | 500 | converged, 193 it, 1.3 s, mean 0.86 / max 2.7 %: 64 stal 110, 128 stal 50, 256 conv 33 | converged, 193 it, 0.6 s, mean 0.86 / max 2.7 %: 64 stal 110, 128 stal 50, 256 conv 33 |
| states-lognormal2 | 500 | stalled, 270 it, 0.8 s, mean 15.25 / max 106.5 %: 64 stal 160, 128 stal 50, 256 stal 60 | stalled, 270 it, 0.9 s, mean 15.25 / max 106.5 %: 64 stal 160, 128 stal 50, 256 stal 60 |
| districts-smooth2 | 500 | stalled, 570 it, 3.1 s, mean 4.26 / max 44.8 %: 128 stal 170, 256 stal 100, 512 stal 300 | completed, 500 it, 2.2 s, mean 3.64 / max 58.0 %: 128 stal 170, 256 stal 100, 512 comp 230 |
| districts-inverse | 500 | stalled, 490 it, 2.0 s, mean 18.67 / max 330.6 %: 128 stal 230, 256 stal 140, 512 stal 120 | stalled, 490 it, 2.0 s, mean 18.67 / max 330.6 %: 128 stal 230, 256 stal 140, 512 stal 120 |
| districts-pop64 | 500 | converged, 229 it, 0.9 s, mean 0.18 / max 2.6 %: 64 stal 110, 128 conv 119 | converged, 229 it, 1.0 s, mean 0.18 / max 2.6 %: 64 stal 110, 128 conv 119 |
| counties | 500 | stalled, 720 it, 15.3 s, mean 2.18 / max 473.4 %: 512 stal 410, 1024 stal 190, 2048 stal 120 | completed, 500 it, 6.7 s, mean 6.46 / max 496.4 %: 512 stal 410, 1024 comp 90 |
