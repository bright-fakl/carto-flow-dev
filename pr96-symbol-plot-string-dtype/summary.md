---
pr: 96
issue: 88
title: Fix SymbolCartogram.plot column styling for pandas extension dtypes
description: plot(edgecolor="<column>") no longer raises TypeError for pandas string-dtype columns; the fixed plot is shown for object and string dtypes.
url: https://github.com/bright-fakl/carto-flow/pull/96
branch: fix/symbol-plot-string-dtype
base: main
date: 2026-10-08 15:05
before: main (TypeError: Cannot interpret 'string[python]' as a data type)
after: fix/symbol-plot-string-dtype
inputs: US census (bundled), layout="packing", edgecolor="Region" with Region as object and as string dtype
kind: pr
topic: symbol
---

figure: edgecolor_region.png — edgecolor="Region" with an object column (left) and a string-dtype column (right), after the fix. Both give identical colors.

## What changed

`np.issubdtype` cannot interpret pandas extension dtypes (string, category, Int64, Float64). The numeric check in `_apply_color_mapping` and in the legend helper now goes through `_is_numeric_values`, which uses `pd.api.types.is_numeric_dtype` and keeps booleans categorical, as before.

## Before / after

- Before: `plot(edgecolor="Region")` and `facecolor="Region"` raise `TypeError` when `Region` is string or category dtype. The same happens for numeric `Int64` / `Float64` columns.
- After: all of these plot. `hatch=` was not affected (it converts with `astype(str)`).
- The remaining dtype checks in `symbol_cartogram` operate on `np.asarray` output or on arrays built from floats, so no other path has the bug.

## Evidence

- `tests/test_symbol_plot_string_dtype.py`: edgecolor/facecolor/hatch with object, string and category columns, and facecolor/edgecolor with float, Int64 and Float64 columns. 6 of 12 fail on main, all pass with the fix.
- `pytest -k symbol`: 310 passed.
- Checked locally with pandas 2.3.3, where string dtype is opt-in: the plot works for both object and `"string"` Region columns (figure).
