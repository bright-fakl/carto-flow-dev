---
pr: 184
url: https://github.com/bright-fakl/carto-flow/pull/184
issue: 149
title: PlotStyle persistence and accessibility checks of the built-in palettes
description: PlotStyle.to_dict / from_dict / save / load make styles portable (JSON, versioned). Accessibility tests simulate color vision deficiency for the categorical, diverging and overlay colors of the default and dark styles. The ten categorical colors cannot all differ under red-green deficiency (minimum color difference 4 to 7). The overlay colors of the dark style were close under protanopia and deuteranopia (10.0 and 3.4); they changed and now differ by 12 or more in both styles.
kind: pr
topic: infra
base: main
branch: feat/style-persistence
related: style-system
date: 2026-10-26 18:00
before: main @ 6921aca
after: feat/style-persistence
inputs: PlotStyle.default() and PlotStyle.dark(). Color vision deficiency by the Machado, Oliveira and Fernandes (2009) matrices at severity 1.0 in linear RGB; distances are CIE76 color differences; contrast is the WCAG ratio.
---

`fig.py <output dir>` draws the figure (it imports the helpers of `tests/test_style_accessibility.py`).

figure: fig1_cvd.png — Categorical (first row), diverging (second row) and overlay colors (third row) of the default (left) and dark (right) style under normal vision and simulated protanopia, deuteranopia and tritanopia.

## Persistence

- `to_dict` writes only the fields that are set, with `version: 1`. A colormap is written by name when matplotlib has it under that name, otherwise as its colors (a continuous colormap as 256 samples). `axes.prop_cycle` round-trips. An rc value that is not JSON raises `TypeError`; unknown keys, an unknown version and invalid values raise `ValueError`.
- The built-in styles and a style sheet read with `from_mplstyle` round-trip to an equal style.

## Accessibility (minimum CIE76 difference, 10 or more counted as distinct)

| check | default | dark |
|---|---|---|
| ten categories, normal vision | 23.1 | 27.7 |
| ten categories, protan / deutan / tritan | 4.0 / 5.6 / 12.8 | 4.6 / 7.2 / 15.2 |
| ends of the diverging palette, protan / deutan / tritan | 66.7 / 90.0 / 97.2 | 66.7 / 90.0 / 97.2 |
| overlay colors against each other, protan / deutan / tritan | 16.8 / 26.7 / 12.7 | 22.2 / 14.9 / 20.1 (before: 9.95 / 3.4 / 15.2) |
| overlay colors against the surface (WCAG ratio) | 2.6 to 4.8 | 6.9 to 11.5 |

Findings, marked `xfail(strict=True)` in the tests: ten qualitative colors cannot all differ under protanopia and deuteranopia (the best five of the ten do, and that is tested). The overlay colors of the dark style were close under protanopia (9.95) and deuteranopia (accent yellow and positive green, 3.4). They changed (series `#6cb4ee` to `#85b7e0`, accent `#ffd23f` to `#facc38`, positive `#4cc38a` to `#54d497`, highlight `#c792ea` to `#bf9cfc`): the search kept each hue family and the contrast with the surface (4.5) and the reference layer (3.5), maximized the smallest difference at 15 under all three deficiencies, and took the set closest to the old colors. The tests now require 12 for both styles. The contrast of an overlay against the fills of a sequential ramp is not checked: a single color matches some fill of a ramp that runs from light to dark, so the overlays are checked against the surface and the reference layer.
