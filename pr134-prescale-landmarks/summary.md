---
pr: 134
url: https://github.com/bright-fakl/carto-flow/pull/134
issue: 86
title: prescale_components moves the landmarks and the displacement coordinates with their component
description: The pre-scaling scaled every connected component of the geometries to its target area but left the landmarks and the displacement coordinates where they were, so they started outside a region that was scaled down. With two separate squares (values 1 and 4, 300 dots each) 39 % of the dots of the shrunken square were inside it at the end; they are all inside after the fix. Contiguous inputs such as the US states (one component, factor 1) are unchanged.
kind: pr
topic: flow
branch: fix/prescale-landmarks
base: main
date: 2026-10-14 20:00
related: pr133-landmark-uniform
before: main @ 5a4a5a2 (landmarks not scaled with the components)
after: fix/prescale-landmarks @ 85a0adf
inputs: two separate unit squares (values 1 and 4), 300 uniform random dots in each, MorphOptions(grid=128, prescale_components=True, mean_tol=0.005, max_tol=0.01).
---

`make_figures.py` runs the case in a checkout of main (`before`) and of the fix (`after`) and writes the figure and `data/tables.md`.

figure: fig_before_after.png — Left: the input. Middle: before the fix the dots of the first square, which the pre-scaling shrinks to 0.4 of its area, are mostly outside it (orange). Right: after the fix the dots are scaled with their square and all are inside.

| | share of the dots inside their region (square 1, square 2) | final areas |
|---|---|---|
| Before the fix | 0.39, 1.0 | 0.4, 1.6 |
| After the fix | 1.0, 1.0 | 0.4, 1.6 |
