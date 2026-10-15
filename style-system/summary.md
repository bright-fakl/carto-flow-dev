---
title: Style system and presets for plots and animations
description: Proposal for issue 99. A frozen PlotStyle dataclass (surface, boundary, text, colormap with truncation, color scale, typography, colorbar, figure size) with the built-in presets default and slides, a small registry for custom presets, a per-call style argument and a style_context manager. Explicit arguments beat the style, the style beats the library defaults, and the default look does not change. Animation timing is a separate morph_timeline helper, not part of the style. The flow animations accept norm=, and a log norm gets real-number tick labels from the style. First PR covers the flow plots and animations; symbol, Voronoi and proportional plots follow.
issue: 99
kind: proposal
topic: flow, infra
status: open
related: exploration-border-drift
inputs: ANIMATION-STYLE.md, reference_implementation.py and style.py of the GeoDC talk bundle; the plot and animation signatures of the four cartogram types (survey below).
---

A design proposal. Nothing is implemented. Issue 82 (talk visuals in the docs) depends on it.

## What the talk style consists of

Collected from `ANIMATION-STYLE.md` and the talk's `style.py` (about 30 lines repeated by every script):

| group | settings |
|---|---|
| surface | `#eef1f4` on the figure and every axes, also as `savefig` facecolor |
| boundary | `#dde4ea`, linewidth 1.5 (slightly darker than the surface) |
| text | `#222222`; tick labels 20 pt, labels 22 pt |
| colormap | `YlGnBu` truncated to 0.22-1.0, so no fill is close to the surface |
| color scale | log for a variable spanning more than about one decade; tick labels in real numbers (`1M`, `2M`, `5M`), never "log10" |
| colorbar | outline `#7a848c`, linewidth 1.0; horizontal (shrink 0.62, pad 0.04, aspect 32) in the square frame, vertical on the right in the 16:9 frame |
| frame | 1080 x 1080 at dpi 120 (social), or 1920 x 1080 (slides) |
| motion | hold 1.5 s, eased morph 7 s, hold 2.5 s, eased return 5 s; cosine easing; fixed extent; solver snapshots as keyframes |

The first seven rows are look. The last row is timing, which is a different concern (see "Animation timing").

## What the library offers now (survey)

- Flow: `Cartogram.plot` / `plot_cartogram` take `cmap` (default `RdYlGn_r`), `legend` and `**kwargs` for `GeoDataFrame.plot`. The six `animate_*` functions take `cmap` (default `viridis`), `colorbar`, `colorbar_label`, `colorbar_kwargs`, `title`, `figsize`. The color normalization is built inside as `plt.Normalize(vmin, vmax)`; `norm=` is not accepted, which is why the talk passes log10 values and relabels the ticks by hand.
- Symbol: `SymbolCartogram.plot` has 38 parameters (`cmap`, `norm`, `facecolor`, `edgecolor`, `linewidth`, ten legend options, label options). Voronoi has its own `cell_style`, `point_style`, `geometry_style` dicts. Proportional has `background_*` and `complement_*` parameters.
- No shared object, no way to set the look once, no surface color, no typography, no colormap truncation.

## Proposed design

### `PlotStyle`

A frozen dataclass in a new module `carto_flow/style.py`, exported from the package. Every field defaults to `None` (meaning: leave the matplotlib or library default alone), so `PlotStyle()` changes nothing.

| field | meaning |
|---|---|
| `background` | facecolor of the figure and the axes (also used by `save_animation` as `savefig` facecolor) |
| `boundary_color`, `boundary_width` | region edge color and width, used where the call does not pass `edgecolor` / `linewidth` |
| `text_color`, `font_family` | tick labels, labels, title |
| `tick_size`, `label_size`, `title_size` | font sizes in points |
| `cmap` | sequential colormap (continuous data): name or `Colormap` |
| `cmap_range` | `(lo, hi)` truncation of `cmap`, default `(0, 1)` |
| `diverging_cmap` | colormap for data with a meaningful center (errors, differences, election margins) |
| `categorical_colors` | colormap name or list of colors for categories |
| `color_scale` | `"linear"`, `"log"` or `"auto"` (log when all values are positive and span more than `log_span` decades, else linear) |
| `log_span` | decades that trigger `"auto"`, default 1.0 |
| `colorbar_orientation`, `colorbar_shrink`, `colorbar_pad`, `colorbar_aspect` | colorbar placement |
| `colorbar_outline_color`, `colorbar_outline_width` | colorbar spines |
| `tick_format` | `"plain"` or `"si"` (`1M`, `2.5k`); with a log norm the ticks are placed at 1, 2, 5 per decade |
| `figsize`, `dpi` | used when the plot function creates the figure, and by `save_animation` as default |

Methods: `copy_with(**changes)` (the convention of `MorphOptions`), `colormap()` (the truncated colormap object), `norm(values)` (the `Normalize` or `LogNorm` the scale implies), `colorbar(fig, ax, mappable, label)` (applies the colorbar fields and tick labeling, so users of plain matplotlib can reuse it), `apply(fig)` (surface and text colors on a figure and its axes).

### Presets and registry

- `PlotStyle.default()`: all `None`, today's output (nothing changes unless a style is selected).
- `PlotStyle.slides()`: the talk look for a 16:9 frame (surface, boundary, truncated `YlGnBu`, `color_scale="auto"`, 20/22 pt, vertical colorbar with outline, 1920 x 1080 at dpi 120).
- Custom presets: `register_style("social", PlotStyle.slides().copy_with(figsize=(9, 9), colorbar_orientation="horizontal", colorbar_shrink=0.62, colorbar_pad=0.04, colorbar_aspect=32))`; `get_style(name)`; `style="social"` is accepted wherever a style is. The 1080 x 1080 social look of `ANIMATION-STYLE.md` is this example in the docs, not a third built-in preset.

### Selecting a style

1. `style=` argument on the plot and animation functions (a `PlotStyle`, a registered name, or `None`).
2. `with carto_flow.style_context(PlotStyle.slides()): ...` sets the style for a block, for example a docs gallery script (a `contextvars.ContextVar`, so it is safe in threads and async code).
3. Otherwise `PlotStyle.default()`.

No global setter: process-wide state is easy to forget in notebooks.

Precedence for every setting: explicit argument of the call, then the style, then the library default. For this to work the library defaults that are now in signatures (`cmap="RdYlGn_r"`, `cmap="viridis"`) become `None` in the signature and are resolved inside, with the same effective default as now.

### Matplotlib stylesheets

A `PlotStyle` is not an `rcParams` dict, because the main fields (truncated colormap, log colorbar, boundary color relative to the surface) are not rcParams. `PlotStyle` does not conflict with `plt.style.context`; the style only sets what it names. A `PlotStyle.rc_params()` method could return the font and color subset for users' own plots; I would add it only if asked.

### Data types: continuous, diverging, categorical

The look of a map depends on the kind of data as well as on the style: a log scale, a truncated sequential colormap and a colorbar make sense for continuous data and none of them for categories (which need a distinct-color palette and a legend). The style therefore holds one palette per role, and the plot function picks the role from the data:

| role | detected when | style fields used | colorbar or legend |
|---|---|---|---|
| sequential | numeric column (default) | `cmap`, `cmap_range`, `color_scale`, `tick_format` | colorbar |
| diverging | the plot says so (`center=` given, or the built-in error and difference columns such as `_morph_error_pct`) | `diverging_cmap`, symmetric norm around the center | colorbar |
| categorical | categorical, string or boolean dtype, or `categorical=True` | `categorical_colors` | legend (font sizes from the style) |

Rules: the role is decided by the data and the call, never by the style; the style only supplies the palette for each role. Fields of other roles are ignored (a categorical column ignores `color_scale` and `cmap_range`). An explicit `cmap` argument of the call overrides the palette of the detected role. The same detection is used by the animations (`color_values` or `column`). A binary variable (such as the election winner) is categorical; a share between 0 and 1 is sequential or diverging around 0.5. What this does not settle is ordinal data (ordered categories): proposed to treat it as categorical with a sequential palette sampled at the number of levels (`ordered=True` on the categorical dtype), to be confirmed.

### Log color scale and `norm=`

- The flow animations and plots accept `norm=` (a `Normalize`), with `vmin` / `vmax` taken from it. This removes the log10-values workaround.
- With `color_scale="log"` (or `"auto"` resolving to log) the style builds the `LogNorm` and its colorbar uses real-number tick labels (`tick_format="si"`). Zeros or negatives under `"log"` raise a clear error; `"auto"` falls back to linear.

### Animation timing is not part of the style

Hold, morph and return durations, easing and the loop are about time, not appearance, and they are already expressed through `keyframe_times` and `linear_over("time")`. Proposal: a small helper `morph_timeline(snapshots, hold_start=1.5, morph=7.0, hold_end=2.5, back=5.0, easing="cosine")` returning `(keyframes, times)` to pass to `animate_geometry_keyframes`, replacing the talk's `loop_timeline` and `ease_inv`. Optional `back=0` for a time series that plays forward only. `fps` and `dpi` stay explicit arguments; `figsize` and `dpi` defaults come from the style.

### Other parts (issue point 4)

Preset bundles for `MorphOptions` and layout options already exist as classmethods and do not share fields with a plotting style. No shared mechanism is proposed; the convention (`copy_with`, classmethod presets) is already the same.

## Scope and order

1. PR A: `style.py`, flow `Cartogram.plot`, `plot_cartogram`, `plot_comparison`, the six `animate_*` functions and `save_animation`; `norm=`; `morph_timeline`; tests with before/after figures of the default (unchanged) and `slides`; docs page on styling.
2. PR B: symbol, Voronoi and proportional plots (their existing `facecolor`, `edgecolor`, `cell_style` parameters stay and win over the style).
3. Issue 82: the talk visuals as gallery examples under `style_context(PlotStyle.slides())`.

## Open decisions

1. Name: `PlotStyle` (proposed) or `Style`.
2. Should `figsize` and `dpi` be in the style (proposed, so a preset reproduces a frame size), or stay call arguments only.
3. Built-in presets: `default` and `slides` (proposed), or also a built-in `social`.
4. Docs gallery: keep the current docs look (proposed) and use `slides` only for the talk visuals of issue 82, or move the whole gallery to one style.
5. Data types: one palette per role (sequential, diverging, categorical) with the role detected from the data (proposed), or a single `cmap` field and the user switches per call.
6. `style=` as a string name: accept registered names (proposed) or only objects.
