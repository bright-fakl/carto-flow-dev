---
issue: 109
title: Flow cartogram convergence: what is settled and what is open
description: One page for the convergence work behind the tracking issue. The stall rule, best iterate and recompute-on-rise are merged; step control, area-weighted rasterization and the preset values are decided in principle and wait for their PRs; counties, border drift and the GSM solver are open or on hold. Links to the evidence pages.
kind: exploration
topic: flow
status: open
related: pr110-stall-detection, adaptive-recompute-experiment, exploration-adaptive-step, exploration-area-coverage, exploration-default-dt, exploration-overview
date: 2026-10-11 11:00
---

This page replaces reading the six exploration pages in order. Each statement links to the page that holds the figures and tables. It contains no new measurements.

## Merged

- **Stall rule, best iterate, recompute on rise** (#110, [pr110-stall-detection](../pr110-stall-detection/index.html)). Progress is judged per window of at least 10 iterations and only in a component that is still violated; a run that does not converge returns its best iterate; the velocity field is also recomputed early when the score rises (`recompute_on_rise`, default 0.01), with `recompute_every` as the maximum interval. Origin: [adaptive-recompute-experiment](../adaptive-recompute-experiment/index.html).

## Decided, PR not yet made

| topic | decision | evidence | next step |
|---|---|---|---|
| Area-weighted density (#95) | Add `"exact"` coverage as its own change. It costs no more than cell-centre sampling, conserves mass, and removes the sub-cell failures: the coarse multiresolution plateau, the grid-128 anisotropy failures and the DC error (4.4 % to 0.8 % at grid 256). It does not change the sawtooth, the counties plateau or the border drift. Make it the default only after a visual check. | [exploration-area-coverage](../exploration-area-coverage/index.html) | PR #119 (opt-in `"exact"`; default stays center; [report](../exact-density-coverage/index.html)) |
| Error floor (#87) | A grid-independent floor of about 1e-3 times the mean target area, instead of one grid cell, so the reported error is comparable across grids and does not hide small regions on coarse grids. | tracking issue #109, element 5 | PR |
| Restart cap (#94) | A small cap on the first step after a restart makes continuation from an existing geometry safe (multiresolution levels, workflow refinement); it is neutral on fresh runs. An error-dependent step on top is not a default: it costs 0 to 60 % more iterations, and recompute on rise already gives most of the robustness. | [exploration-adaptive-step](../exploration-adaptive-step/index.html) | PR |
| Preset values | `preset_balanced` to dt 0.3 and `preset_high_quality` to dt 0.2; the default `dt` stays 0.2. A larger constant dt saves 20 to 40 % at default tolerances but costs 1.5 to 2.7 times more at tight tolerances, adds invalid polygons on districts above 0.4, and grows the border drift. | [exploration-default-dt](../exploration-default-dt/index.html) | folded into the preset review, #115 |

## Open

- **Counties never converge** with any step, rasterizer or controller tested. Most targets are smaller than one grid cell (2,096 of 3,108 at grid 256) and must shrink 100 to 500 times with a vanishing driving force. Needs the multiresolution trigger and iteration budget (#93), a resolution warning, and probably a target floor.
- **Border drift of co-advected points** (#86) depends on `dt` times `recompute_every`, not on the rasterizer.
- **Multiresolution trigger and budget** (#93). The coarse-level plateau of districts is a sub-cell region, not a step-size problem.
- **Invalid polygons** (#85, #78): larger steps and the GSM variants raise their count.

## On hold

- **GSM (Gastner, Seguy, More 2018) solver and step scale** (#75): [exploration-overview](../exploration-overview/index.html). The spatial pattern does not help; the physical step magnitude cuts the cost 3 to 5 times on states but adds invalid polygons and fails on districts and counties; the full integrator costs 1.8 to 2.2 times the baseline in this implementation. The benchmark against the R packages is also on hold.

## Cost model used on these pages

Cost is in plain-step units: iterations plus field recomputes times the ratio of one recompute to one step. The ratio is 9, 12, 24 and 71 on the states at grids 128, 256, 512 and 1024. Wall times from earlier drafts were measured under load and are not used.
