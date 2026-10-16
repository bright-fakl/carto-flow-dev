---
pr: 154
url: https://github.com/bright-fakl/carto-flow/pull/154
issue: 82
title: Non-contiguous gallery example with reference_region
description: The gallery example of the non-contiguous cartogram follows the story of the talk: the default reference (DC) makes most states tiny, New Jersey as reference_region with DC capped or grown, and the largest-state reference with the cap.
kind: pr
topic: noncontiguous
base: main
branch: docs/gallery-noncontiguous-region
date: 2026-10-17 18:30
related: noncontiguous-cartogram
before: main @ c70dca4
after: docs/gallery-noncontiguous-region @ 1d83b28
inputs: bundled US states (simplify 1000), population.
---

The example has four cells, each drawing one map. The figure here is from the page of the function (the three references of the first three cells); the gallery renders all four at documentation build time.

figure: fig_reference_region.png — Default reference (DC), New Jersey with DC capped, New Jersey with DC grown.

## What changes

| | |
|---|---|
| example | `docs/examples/noncontiguous_cartogram/plot_noncontiguous_cartogram.py`: four maps instead of two |
| not taken from the talk | the comparison with `shrink`: `method="shrink"` is not offered (#74); the election maps (FEC data, not bundled) |

## Checks

The example runs; the docs build runs in CI.
