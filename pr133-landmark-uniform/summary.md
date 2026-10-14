---
pr: 133
url: https://github.com/bright-fakl/carto-flow/pull/133
issue: 86
title: Area scaling of the landmarks along the flow and uniform point landmarks
description: The morph sums the divergence of the velocity field along the path of every landmark vertex at no measurable cost; every snapshot stores the area scaling, and Cartogram.get_landmarks(iteration, uniform=True) remaps the distance of point landmarks to the border of their region so that landmarks that were uniform before the morph are uniform again, at any saved iteration. The distribution of the distance to the border is computed deterministically (distance transform, once per cartogram), so the correction changes smoothly between frames of an animation. On the states with 8 seeds of about 1,480 dots the mean border-band z-score is 4.28 for the carried dots, 0.47 with uniform=True and 0.63 on the original map; the median dot moves 0.8 % of the width of its region.
kind: pr
topic: flow
branch: feat/landmark-area-scaling
base: main
date: 2026-10-13 18:00
related: exploration-border-drift
before: main @ 5a4a5a2 (landmarks carried by the flow)
after: feat/landmark-area-scaling @ ef3273e
inputs: 49 states (bundled) with poverty counts, dot density with n_dots = round(max / 25000), normalization "maximum" (about 1,480 dots), 8 seeds; MorphOptions defaults with area_scale 1e-6 (grid 256); NUMBA_NUM_THREADS=8. The border-band z-score counts the dots inside a band of 6 % of sqrt(area) along the border of their own region against the number expected for uniform dots (binomial, summed over regions).
---

`make_figures.py` regenerates the figures and `data/tables.md`, `frames.py` the table of the frames; they use `get_landmarks(uniform=True)` of the library. The cost: within the same checkout, disabling the accumulation does not change the morph time (0.229 against 0.228 s at grid 256 and 0.53 against 0.54 s at grid 512, 1,480 dots, minimum of 5 runs); `get_landmarks(uniform=True)` takes 0.35 s the first time (it includes the distribution of the distance to the border of every region) and 0.054 s afterwards for these dots. More on the mechanism, the measurements and the alternatives that were tried is on `exploration-border-drift`.

Frames: 29 snapshots of one morph (every 4 iterations), correction vector of every corrected dot over the frames. Second difference of the correction: 0.008 % of the width of the region in the median, 0.12 % at the 95th percentile; increment of the correction between two frames relative to the carried motion: 0.011 in the median, 0.135 at the 95th percentile. A version with the distribution of the distance taken from 400 random sample points per region had 0.14 % and 1.1 % and 0.66 at the 95th percentile.

figure: fig_map.png — California (blue) and Nevada (orange), dot seed 7. Left: the original map. Middle: the dots carried by the flow crowd the border band (z 3.8 over all states). Right: the same dots after get_landmarks(uniform=True).
figure: fig_profile.png — Pooled distance profile of the dots on the 49 states (observed / expected, 8 seeds): flat on the original map, 1.4 times the expected number in the first 1 % of the distance after the flow, flat again after the correction.

| seed | original map | carried by the flow | get_landmarks(uniform=True) | shift: median / 95th pct (x sqrt(area)) |
|---|---|---|---|---|
| 0 | -0.11 | 3.19 | -0.23 | 0.0069 / 0.0265 |
| 1 | 2.31 | 6.14 | 3.07 | 0.0078 / 0.0287 |
| 2 | 0.98 | 3.77 | 0.99 | 0.0073 / 0.0305 |
| 3 | 0.98 | 5.56 | 1.68 | 0.0074 / 0.0307 |
| 4 | -0.29 | 3.48 | -0.52 | 0.0077 / 0.0292 |
| 5 | 1.15 | 5.22 | 0.52 | 0.0079 / 0.0329 |
| 6 | -0.58 | 3.13 | -1.27 | 0.007 / 0.033 |
| 7 | 0.63 | 3.77 | -0.46 | 0.0084 / 0.0303 |
| mean | 0.63 | 4.28 | 0.47 | 0.0076 / 0.0302 |

| dots (observed / expected, mean over 8 seeds) | 0-0.01 | 0.01-0.02 | 0.02-0.04 | 0.04-0.06 | 0.06-0.1 | 0.1-0.2 | 0.2-0.4 | 0.4-0.6 |
|---|---|---|---|---|---|---|---|---|
| original | 1.03 | 1.04 | 1.00 | 1.03 | 1.00 | 0.99 | 0.98 | 1.18 |
| carried | 1.40 | 1.27 | 1.10 | 1.02 | 0.96 | 0.93 | 0.90 | 0.88 |
| uniform | 1.10 | 1.03 | 0.97 | 1.00 | 0.99 | 1.00 | 0.98 | 0.91 |
