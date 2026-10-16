---
pr: 158
url: https://github.com/bright-fakl/carto-flow/pull/158
title: The style how-to is a notebook with plots and animations
description: The how-to "Style Plots and Animations" was a Markdown page with code blocks and no output, so it showed no plot and no animation. It is now a notebook that the documentation build executes, with the built-in styles on one cartogram, style_context and set_style, the palettes of the data types, your own and combined styles, and two animations.
kind: pr
topic: infra, flow
base: main
branch: docs/style-howto-notebook
date: 2026-10-18 14:00
related: style-system, gallery-default-style
before: main @ 7fa5abf
after: docs/style-howto-notebook @ 3b70eae
inputs: bundled US states with population; a flow cartogram with snapshots every 10 iterations.
---

The page was written as Markdown, which the build does not execute, so it could not show output; this was not a decision. The other how-tos are notebooks.

## Figures

figure: fig_dark.png — The same cartogram in the dark style (the default and classic figures are on the page).
figure: fig_data_types.png — Categories, a diverging scale around a center, a linear scale and a palette of the call.
figure: fig_own_style.png — A registered style with the Blues palette, a linear scale and thinner edges.
figure: fig_dark_large_type.png — The dark style combined with the large type of a slide.

The two animations (the morph with the error in the dark style, and `morph_timeline` with the large type) are shown inline on the built page and are not in this report.

## What changes

| | |
|---|---|
| how-to | `docs/how-to/style-plots.ipynb` replaces `style-plots.md`; the navigation and the how-to index point to it |
| text | the prose and the reference lists of the page are kept as text cells (what a style holds, keeping styles between sessions) |

## Checks

The notebook runs without error (about 10 s); the docs build, which executes it, runs in CI.
