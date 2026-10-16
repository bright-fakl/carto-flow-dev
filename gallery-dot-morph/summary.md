---
pr: 153
url: https://github.com/bright-fakl/carto-flow/pull/153
issue: 82
title: Gallery animation: dot density map into a flow cartogram
description: A gallery example carries dots generated on the true-area map as landmarks through a flow cartogram and draws them at every saved iteration with get_landmarks(iteration, uniform=True). With the defaults the carried dots have a border-band z-score of 3.8 and the uniform dots -0.5.
kind: pr
topic: flow, proportional
base: main
branch: docs/gallery-dot-morph
date: 2026-10-17 17:30
related: pr133-landmark-uniform
before: main @ c70dca4
after: docs/gallery-dot-morph @ 497a92c
inputs: bundled US states with poverty counts (simplify 1000); 1,480 dots (one dot is 25,011 people below the poverty line), seed 7; flow morph with the defaults and area_scale 1e-6, snapshot_every 4 (29 frames).
---

The animation is built by the gallery at documentation build time (a GIF of about 1 MB, not committed); the figures here are its first and last frame.

## Figures

figure: fig_start.png — The true-area map with the dots.
figure: fig_end.png — The flow cartogram with the dots carried along: the dot density is the poverty rate.

## Border drift

Border-band z-score over all states (8 seeds in [pr133-landmark-uniform](../pr133-landmark-uniform/index.html); one seed here): carried dots 3.77, `uniform=True` dots -0.46; the share of dots inside their own state at the end is 1.000 and 0.998. The talk needed a grid of 512 and `recompute_every=1` to keep the drift down; the example uses the defaults.

## What changes

| | |
|---|---|
| example | `docs/examples/flow_cartogram/plot_flow_dot_morph.py`, about 13 s with the GIF |
| not taken from the talk | the Hispanic variant and the assertions of the talk script |

## Checks

The example runs; the docs build (including the GIF) runs in CI.
