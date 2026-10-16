---
issue: 109
title: Flow cartogram convergence: what is settled and what is open
description: One page for the convergence work behind the tracking issue 109, now closed. The stall rule, best iterate, recompute-on-rise, exact rasterization, error floor, adaptive step, presets and the resolution check of the multiresolution ladder are merged; counties (hierarchical morph, 129), the GSM solver (75) and pre-flight validation (78) are the open items, each with its own issue. Links to the evidence pages.
kind: exploration
topic: flow
status: open
related: pr110-stall-detection, adaptive-recompute-experiment, exploration-adaptive-step, exploration-area-coverage, exploration-default-dt, exploration-overview, exact-density-coverage, error-floor, adaptive-step-control, exact-ring-orientation, output-validity, preset-review, pr128-multires-auto-resolution, exploration-multires-start, exploration-multires-stall, exploration-counties-subcell, exploration-hierarchical-morph, pr133-landmark-uniform
date: 2026-10-17 12:00
---

This page replaces reading the exploration pages in order. Issue 109 is closed; each open item has its own issue. Each statement links to the page that holds the figures and tables. It contains no new measurements.

## Merged

- **Stall rule, best iterate, recompute on rise** (#110, [pr110-stall-detection](../pr110-stall-detection/index.html)). Progress is judged per window of at least 10 iterations and only in a component that is still violated; a run that does not converge returns its best iterate; the velocity field is also recomputed early when the score rises (`recompute_on_rise`, default 0.01), with `recompute_every` as the maximum interval. Origin: [adaptive-recompute-experiment](../adaptive-recompute-experiment/index.html).

## Merged since

| topic | what was decided and merged | evidence | PR |
|---|---|---|---|
| Area-weighted density (#95) | `"exact"` coverage is the default rasterization. It costs no more than cell-centre sampling, conserves mass, and removes the sub-cell failures: the coarse multiresolution plateau, the grid-128 anisotropy failures and the DC error (4.4 % to 0.8 % at grid 256). It does not change the sawtooth, the counties plateau or the border drift. | [exploration-area-coverage](../exploration-area-coverage/index.html), [exact-density-coverage](../exact-density-coverage/index.html) | #119 |
| Error floor (#87) | A grid-independent floor of 1e-3 times the mean target area, instead of one grid cell, so the reported error is comparable across grids and does not hide small regions on coarse grids. | [error-floor](../error-floor/index.html) | #121 |
| Step control (#94) | The late phase is a limit cycle: the fastest point moves `dt` cells whatever the error, so the areas alternate around their targets with an amplitude proportional to `dt`. A step that shrinks when more than 30 % of the regions change the sign of their error (never growing back), plus a cap on the first steps of a restart, removes it: 32 of 32 tight-tolerance runs converge against 17, restarts from a converged result take 1 iteration instead of 4. | [adaptive-step-control](../adaptive-step-control/index.html), [exploration-adaptive-step](../exploration-adaptive-step/index.html) | #123 (`adaptive_dt`, default on) |
| Exact rasterizer fix | A ring with a small self-intersecting loop was judged counter-clockwise, so its region dropped out of the density field (a stalled districts run converges). | [exact-ring-orientation](../exact-ring-orientation/index.html) | #124 |
| Output validity (#85) | The morph warns about self-intersecting regions of the result; `repair=True` makes them valid. The crossings are not prevented. | [output-validity](../output-validity/index.html) | #125 |
| Presets (#115) | The iteration limits of the presets are raised so that they converge on states and districts; `preset_balanced` equals the defaults. The larger default `dt` was not adopted: it saves 20 to 40 % at default tolerances but costs 1.5 to 2.7 times more at tight tolerances, adds invalid polygons on districts above 0.4 and grows the border drift. | [preset-review](../preset-review/index.html), [exploration-default-dt](../exploration-default-dt/index.html) | #127 |
| Multiresolution (#93) | A warning when the smallest target region covers fewer than 2.5 cells at the coarsest grid, `"auto"` for the ladder, one entry point (`create_flow_cartogram`), `n_iter` as the total of a ladder. Refinement on stagnation was measured and not adopted. | [pr128-multires-auto-resolution](../pr128-multires-auto-resolution/index.html), [exploration-multires-start](../exploration-multires-start/index.html), [exploration-multires-stall](../exploration-multires-stall/index.html) | #128, #130, #131, #132 |
| Border drift of carried points (#86) | The drift is inherent to the flow (it depends on `dt` times `recompute_every`, not on the rasterizer). `Cartogram.get_landmarks(iteration, uniform=True)` remaps the distance of point landmarks to the border of their region so that landmarks that were uniform are uniform again (border-band z-score 0.47 against 4.28 for the carried dots, 0.63 on the original map). | [pr133-landmark-uniform](../pr133-landmark-uniform/index.html), [exploration-border-drift](../exploration-border-drift/index.html) | #133 |

## Open

- **Counties never converge** with any step, rasterizer or controller tested. Most targets are smaller than one grid cell (2,096 of 3,108 at grid 256) and must shrink 100 to 500 times with a vanishing driving force; starts at grid 1024 and finer diverge. Grids fitted to each group take the sub-cell share to 0.2 % at grid 512 ([exploration-hierarchical-morph](../exploration-hierarchical-morph/index.html)). Tracked in #129; the rubber-sheet alternative is #79. Evidence: [exploration-counties-subcell](../exploration-counties-subcell/index.html).
- **Pre-flight geometry validation** (#78): invalid input still fails late; larger steps and the GSM variants raise the count of invalid output polygons.
- **Follow-ups of the adaptive step**, only if needed: a shorter restart window, the slow convergence of sub-cell regions such as DC, the untested `"center"` rasterizer with `prescale_components`; the districts multiresolution at 0.5 % / 1 % and dt 0.4 stalls in both modes.

## On hold

- **GSM (Gastner, Seguy, More 2018) solver and step scale** (#75, open): [exploration-overview](../exploration-overview/index.html). The spatial pattern does not help; the physical step magnitude cuts the cost 3 to 5 times on states but adds invalid polygons and fails on districts and counties; the full integrator costs 1.8 to 2.2 times the baseline in this implementation. The benchmark against the R packages is also on hold.

## Cost model used on these pages

Cost is in plain-step units: iterations plus field recomputes times the ratio of one recompute to one step. The ratio is 9, 12, 24 and 71 on the states at grids 128, 256, 512 and 1024. Wall times from earlier drafts were measured under load and are not used.
