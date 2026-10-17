---
pr: 165
url: https://github.com/bright-fakl/carto-flow/pull/165
title: Rename CirclePackingLayout to PackingLayout
description: CirclePackingLayout, CirclePackingLayoutOptions and CirclePackingAdvancedOptions are renamed PackingLayout, PackingLayoutOptions and PackingAdvancedOptions. The old names stay importable as deprecated aliases. No behavior change, so there are no figures.
kind: pr
topic: symbol
base: main
branch: refactor/packing-layout-rename
date: 2026-10-18 19:00
before: main @ 50859fe
after: refactor/packing-layout-rename @ 452eb3e
related: square-packing-layout
inputs: none (name change only).
---

## Changes

- The three classes are renamed because the layout packs squares as well as circles.
- The old names resolve to the new classes through a module `__getattr__` in `carto_flow.symbol_cartogram`, `carto_flow.symbol_cartogram.layouts` and `carto_flow.symbol_cartogram.layouts.packing`, and emit a `DeprecationWarning` that names the replacement and says the old name is removed in the next major release. `isinstance` checks and subclasses are unaffected because the class object is the same.
- Layout keys `"packing"` and `"topology"` are unchanged.

## Checks

- Full test suite: 1435 passed. New tests cover each old name from both public modules and an unknown attribute still raising `AttributeError`.
- `mkdocs build --strict` passes.
- Source, tests, docs, examples and the Unreleased changelog use the new names. Released changelog entries and `migrating-to-2.0.md` keep the 2.0 names.
