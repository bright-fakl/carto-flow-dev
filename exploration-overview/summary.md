---
issue: 75, 94, 95, 109
title: Overview of the step-scale variants
description: One-glance comparison of the carto-flow step-scale variants tested on the exploration-gsm-scale page, with a glossary: cost relative to the baseline per case, cost against invalid polygons, and the median cost ratio with the number of converged cases.
branch: investigate/gsm-scale
base: fix/stall-detection
date: 2026-10-10 09:30
before: fix/stall-detection @ 8441681
after: investigate/gsm-scale @ bfb4253 (prototype, not for merging)
inputs: the tables of exploration-gsm-scale (states at grids 128, 256 and 512, the multiresolution coarse level, three anisotropy runs, districts at 256 and 512, counties at 256 and 512); each case with refresh on rise off and on; cost = iterations + field recomputes x the case's recompute / step cost ratio
kind: exploration
topic: flow
status: on-hold
---

How to read the figures: the baseline A is one in every case. Cost is in plain-step units (iterations plus field recomputes times the ratio of one recompute to one step, 9 to 47 depending on case). Iteration counts alone mislead: variant B4i takes 5 to 25 iterations because each iteration is a complete round with a recompute, so its cost is 0.3 to 0.7 of A, not 0.05.

figure: overview_scorecard.png — Cost relative to A per case and variant, refresh on rise off (left) and on (right). Green is cheaper than A, hatched cells did not converge, white cells were not run. The second line of each cell is the number of invalid polygons. The multiresolution coarse column shows raw cost because A stalls there.
figure: overview_scatter.png — Cost against invalid polygons for each case (refresh on). Filled markers converged, hollow ones did not. Lower left is better.
figure: overview_summary.png — Median cost relative to A over the cases where both converge, with the range, and the number of converged cases out of those run.

## Glossary

| id | what it is |
|---|---|
| A | baseline: one scale for all vertices, the fastest point moves dt cells per step |
| C3m, C3 dt0.6, C3 dt1.0 | the baseline with a larger constant dt (C3m: the dt that matches B2's mean vertex displacement) |
| C4 | step size shrinks with the score (dt_max 1.0), no density pattern |
| C1 | GSM physical magnitude (displacement proportional to the flux, path length 1 per round), no density pattern |
| C2 | GSM density pattern `rho_mean / rho(x,t)` rescaled to the baseline's mean vertex step |
| B1 | GSM density pattern with the baseline's grid-maximum normalization |
| B2 | GSM density pattern and physical magnitude (cap 1 cell per step) |
| B3 | B2 with the scale field precomputed on the grid for each step |
| B4ii | closed-form time integral of the GSM scale over a round, applied in sub-steps |
| B4i | the same integral applied once per round, with a recompute every iteration (one GSM-style round per iteration) |

## What the figures say

- Cost reductions come from three places: a larger step (C3 variants: about 0.25 to 0.4 of A on states 256 and 512, with refresh on rise needed for stability), the physical magnitude (B2, B3, B4: 0.18 to 0.35 on states, 0.35 to 0.6 on the anisotropy runs), and fewer, larger rounds (B4i).
- The density pattern alone (C2, B1) does not reduce cost and adds invalid polygons (5 to 22 on states against 0).
- The variants that reduce cost most (B2, B3, B4) also have the most invalid polygons (4 to 25 on states and anisotropy, 175 to 213 on districts).
- Counties fail for every variant (they are all hatched), and several variants stall on districts 256.

Source: `data/gsm_scale_tables.md` (a copy of `exploration-gsm-scale/tables.md`); regenerate with `uv run python make_overview.py`. This page covers only the step-scale variants; the stall, refresh, adaptive-step and area-coverage pages are not included.
