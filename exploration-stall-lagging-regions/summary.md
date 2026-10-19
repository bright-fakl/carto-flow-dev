---
issue: 171
title: Do the lagging counties still make progress when the stall rule stops the run?
description: The stall rule judges progress by the mean and the maximum error over all regions. At the stall of the finest county level, the 72 counties above 10 % error continue to improve for another 1,400 iterations (their median error falls from 23 % to 1.2 %, the number above 10 % from 72 to about 27), while the mean error over all counties first falls to 1.1 % and then rises above 4 %. The two aggregates cannot see the progress of a small lagging group.
kind: exploration
topic: flow
status: open
related: stall-rule-grid-scaling, exploration-county-error-relation, exploration-quadtree-windows
date: 2026-10-19 15:00
before: main @ 06d4ff0
after: the same checkout; script only, no library change
inputs: 3,108 bundled counties (population), max_segment_length 1000, auto ladder, n_iter 1000, area_scale 1e-6; then `w.morph(grid=2048, n_iter=1500, stall_patience=None, snapshot_every=50)` continued from the stalled finest level. Single run.
---

## The question

`StallMonitor` records, for every cycle of 10 iterations, the minimum of the mean-error ratio and of the max-error ratio. A cycle is progress if one of the two is still above 1 and has fallen by at least `min_efficiency` times the distance moved. The mean is taken over all regions and the max over a single region, so a small group of lagging regions can make steady progress without either moving: the mean is dominated by the regions that are already close, and the max is held by the single worst region, which can be stuck while the others improve.

## Continuing past the stall

`continue_past_stall.py` runs the baseline ladder (the finest level stalls after 170 iterations with 72 counties above 10 %), then continues the finest grid for 1,500 iterations with the stall rule off, taking a snapshot every 50 iterations.

figure: fig1_past_stall.png — Left: median error of the 72 counties that were above 10 % at the stall, against the iterations after it (23 % to 1.2 %). Right: the mean and the median error of all counties over the same iterations.

| iterations after the stall | counties above 10 % | median error of the 72 | mean error, all | median error, all | p95 | invalid polygons |
|---|---|---|---|---|---|---|
| 0 | 72 | 23.2 % | 1.47 % | 0.22 % | 2.6 % | 57 |
| 150 | 61 | 14.5 % | 1.22 % | 0.096 % | 1.2 % | 68 |
| 300 | 39 | 9.5 % | 1.11 % | 0.12 % | 0.7 % | 74 |
| 450 | 32 | 5.3 % | 1.75 % | 0.19 % | 0.6 % | 74 |
| 600 | 29 | 4.4 % | 2.74 % | 0.36 % | 0.6 % | 81 |
| 900 | 26 | 2.3 % | 2.95 % | 0.42 % | 0.5 % | 88 |
| 1,500 | 27 | 1.2 % | 4.27 % | 0.63 % | 0.7 % | 100 |

- Over the first 300 iterations everything improves, including the mean, and the number of counties above 10 % falls from 72 to 39. A mean-based progress test would have seen this progress, so the stall at iteration 170 is premature, as far as these numbers go.
- After about 400 iterations the lagging counties continue to improve (median 23 % to 1.2 %, 72 to 27 above 10 %), but the bulk gets worse: the median error of all counties rises from 0.1 % to 0.6 %, the maximum error to 3,500 %, and the number of invalid polygons from 57 to 100. The mean error rises with them.
- So no aggregate of all regions describes this run: the mean and the maximum follow the few regions that diverge, and the median follows the bulk. The lagging group has its own trajectory.

## Reading

The concern is confirmed in the first half of the run: progress of the lagging regions is invisible or weak in the mean and max ratios, and the stall can end the run while many regions are still improving. The second half shows the cost of running on: the bulk and some outliers degrade. A progress measure aimed at the lagging regions has to be combined with a returned iterate that is chosen with the same measure, and probably with a check that regions already within tolerance do not leave it.

Candidate measures, not tested here: the count of regions above `max_tol` and the median (or a high quantile) of the ratio among them; the sum of the log ratios over the regions above tolerance, which weights each lagging region equally and is not dominated by one outlier; progress if the count falls or the median ratio among the unsatisfied falls.
