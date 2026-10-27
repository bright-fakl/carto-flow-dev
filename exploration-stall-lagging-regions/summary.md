---
issue: 171, 177
title: Do the lagging counties still make progress when the stall rule stops the run?
description: The stall rule judges progress by the mean and the maximum error over all regions. At the stall of the finest county level, the lagging counties continue to improve for another 1,400 iterations (the 72 above 10 % have a median error that falls from 23 % to 1.2 %), and the valid polygons converge (mean 1.3 % to 0.11 %, 60 to 6 above 10 %), while the mean over all counties first falls and then rises above 4 %. The rise comes from the invalid polygons (57 to 100, mostly Virginia), whose areas explode and shift the targets of all regions.
kind: exploration
topic: flow
status: led-to
related: stall-rule-grid-scaling, exploration-county-error-relation, exploration-quadtree-windows
date: 2026-10-19 15:00
before: main @ 06d4ff0
after: the same checkout; script only, no library change
inputs: 3,108 bundled counties (population), max_segment_length 1000, auto ladder, n_iter 1000, area_scale 1e-6; then `w.morph(grid=2048, n_iter=1500, stall_patience=None, snapshot_every=50)` continued from the stalled finest level. Single run.
closed: 2026-10-26 20:32
---

**Outcome (2026-10-27).** Superseded by the follow-up measurements: with valid polygons the gain from continuing is smaller than measured here (see exploration-stall-after-validity). The stall rule now follows the lagging regions (PR 186).

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
- After about 400 iterations the lagging counties continue to improve (median 23 % to 1.2 %, 72 to 27 above 10 %), but the error of all counties rises: the median from 0.1 % to 0.6 %, the maximum to 3,500 %, and the number of invalid polygons from 57 to 100.
- The rise of the median is a measurement artifact, not a degradation of the bulk (see below).

## What drives the rise of the mean and median

`continue_per_region.py` stores the area and validity of every region at every snapshot. The invalid polygons are mostly the counties and independent cities of Virginia: their shoelace areas explode (one goes from 238 to 11,804 km2, another from 3,273 to 11,790 km2 against a target of a few hundred). The total output area grows by 0.60 %, and the target of every region is its population share of that total, so every region gets the same apparent error: the median signed error is -0.628 % at iteration 1,500 and the median error is 0.628 % in every shrink class, from 0.629 % (shrink below 0.03) to 0.628 % (above 1). Taking the targets from the valid polygons only:

| iterations after the stall | valid polygons | invalid | mean error, valid | median, valid | p95, valid | valid counties above 10 % | mean error, invalid |
|---|---|---|---|---|---|---|---|
| 0 | 3,051 | 57 | 1.31 % | 0.22 % | 2.2 % | 60 | 9.4 % |
| 150 | 3,040 | 68 | 0.68 % | 0.005 % | 0.57 % | 47 | 21.7 % |
| 300 | 3,034 | 74 | 0.46 % | 0.001 % | 0.31 % | 24 | 23.0 % |
| 600 | 3,027 | 81 | 0.30 % | 0.000 % | 0.16 % | 10 | 81.6 % |
| 900 | 3,020 | 88 | 0.20 % | 0.000 % | 0.09 % | 8 | 84.1 % |
| 1,500 | 3,008 | 100 | 0.11 % | 0.001 % | 0.06 % | 6 | 111.7 % |

figure: fig2_valid_vs_invalid.png — Left: the mean and median error of the valid polygons and the mean error of the invalid polygons against the iterations after the stall. Right: the number of invalid polygons.

The valid polygons do not degrade: they converge (median 0.22 % to 0.001 %, mean 1.31 % to 0.11 %, 60 to 6 above 10 %) while the number of invalid polygons grows from 57 to 100 and their error from 9 % to 112 %. The earlier statement that the bulk gets worse was wrong: it was the effect of a few invalid polygons on the normalization of the targets of all regions. The same effect enters the mean and max of the runs on the earlier pages, where the baseline has 57 invalid polygons, to a smaller degree (total area +0.09 % at iteration 300).

## Reading

The concern is confirmed in the first half of the run: progress of the lagging regions is invisible or weak in the mean and max ratios, and the stall can end the run while many regions are still improving. The valid polygons keep converging far past the stall, and what grows is the number and error of the invalid polygons. The mean and max of the stall rule and of the best-iterate selection are dominated by those, so the invalid polygons, not the sub-cell regions, are what the aggregates track late in the run.

Candidate measures, not tested here: the count of regions above `max_tol` and the median (or a high quantile) of the ratio among them; the sum of the log ratios over the regions above tolerance, which weights each lagging region equally and is not dominated by one outlier; progress if the count falls or the median ratio among the unsatisfied falls.
