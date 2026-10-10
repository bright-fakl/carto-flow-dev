---
pr: 39
title: Raise when a symbol-cartogram layout does not honour group_by
description: No figures - this is a behaviour change with no visual output. group_by on the grid and physics layouts now raises instead of silently placing symbols as if no grouping had been given.
url: https://github.com/bright-fakl/carto-flow/pull/39
branch: fix/group-by-unsupported-error
base: main
date: 2026-09-22
after: e562d14 (merged)
kind: pr
topic: symbol
---

## No figures, and why

There is nothing to render. The change does not move a symbol: every
configuration that produced a plot before still produces the identical plot.
What changed is that two configurations which used to produce a plot now raise
`ValueError` instead, because the plot they produced was misleading. A
before/after figure pair would be "a cartogram" next to "a traceback".

The evidence is therefore written, not drawn: the audit below, and the error
and warning text as they landed.

## The defect

`prepare_layout_data` sets `group_ids_G` when the user passes `group_by`.
`GridBasedLayout` and `CirclePhysicsLayout` never read it - grid passes
`group_ids` into the `LayoutResult` constructor for labelling only, physics
does not reference the grouping at all. The user got a plausible-looking
cartogram in which `group_by` had no effect on placement.

## Audit of all layouts

Verified against the merged tree, not only the PR description:

| Layout | Honours `group_by` | Evidence in the merged tree |
|---|---|---|
| `mosaic` | yes | `group_ids_G` drives region blocks, contiguity scoring, swap repair |
| `centroid` | yes | `group_attraction`, default `0.15`, pulls group members together |
| `packing` | only when enabled | `group_weight` group-centroid force, default `0.0` (inert) |
| `flow_density` | only when enabled | `cross_group_pull_scale`, default `1.0` (no distinction) |
| `grid` | no | one `group_ids` reference, in the result constructor |
| `physics` | no | no group reference at all |

`topology` is a registered alias of `packing`.

## Mechanism

- `Layout` gains `supports_group_by: ClassVar[bool] = False`.
- `Layout.compute` becomes a template method: it checks the flag (from
  `data.group_ids_G is not None`), then delegates to a new abstract `_compute`
  that subclasses implement. A layout instance called directly therefore
  cannot bypass the check - there is no unvalidated entry point left.
- `create_layout` runs the same `check_group_by_support` as soon as the layout
  string is resolved, so the error is raised before any preprocessing work.
- The list of supporting layouts in the message is derived from the registry
  (`group_by_layouts()`, aliases dropped), so it cannot drift from the flags.

```
ValueError: Layout GridBasedLayout does not support group_by: it would ignore
the grouping and place symbols as if it were absent. Layouts that honour
group_by: centroid, flow_density, mosaic, packing. Drop group_by or use one of
those layouts.
```

## Inert-default warning

`packing` and `flow_density` read the grouping only through an option that
defaults to a no-op. At those defaults `group_by` is accepted and changes
nothing - the same defect as grid, just quieter. Both now emit a
`UserWarning` through a `_inert_group_by_warning` hook on `Layout`, called from
the same template method, naming the option to set:

- packing: `group_weight is 0.0` - set e.g. `CirclePackingLayout(group_weight=0.5)`
- flow_density: `cross_group_pull_scale is 1.0` - set it below 1.0

Centroid and mosaic inherit the default no-op hook and never warn. The shipped
grouped presets set the options, so they stay silent too.

## The documentation example that did nothing

`docs/reference/symbol_cartogram/index.md` carried

```python
result = create_symbol_cartogram(gdf, size="population", group_by="region")
```

with no `layout=`, and the default is `layout="physics"`. So the documented
way to use `group_by` was one of the two layouts that ignored it entirely.
The example now passes `layout="packing"` and names the layouts that honour
the grouping. Under the new check the old line would raise.

## Breaking change for 2.0

Any caller passing `group_by` with `grid` or `physics` now raises where it
previously ran. That is the intent - the previous result was wrong in a way
the user could not see - but it is a hard break, not a deprecation.

**Accepted consequence.** `collapse_group` acts on starting positions inside
`prepare_layout_data` (`if collapse_group > 0 and group_ids is not None`), so
it used to reach every layout, grid and physics included. Since
`check_group_by_support` now fires in `create_layout` *before* preprocessing,
`group_by` + `collapse_group` + grid/physics is closed off. Collapsing the
starting positions of a grouping the layout then ignores was a thin use case,
and the alternative - allowing `group_by` through when `collapse_group > 0` -
would reintroduce exactly the silent-no-effect surface the PR removes.

`tile_count` is unaffected: it leaves `group_ids_G` as `None`, so the check
stays silent.

## Tests

`tests/test_symbol_cartogram_group_by_support.py` (new, 193 lines): each
non-supporting layout raises via both `create_layout` and `compute`, the
message names the supporting layouts, supporting layouts never raise, and the
check stays silent with no `group_by` and with `tile_count`. The inert-grouping
warning fires for packing and flow_density at their defaults, and is silent
once the option is set, without `group_by`, and for both grouped presets.
