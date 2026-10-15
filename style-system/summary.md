---
title: Style system and presets for plots and animations
description: Proposal for issue 99. PlotStyle is a frozen dataclass that builds on matplotlib: an rcParams dict for text and surface settings (loadable from a matplotlib stylesheet), plus library-specific fields (palettes per data role with optional per-channel overrides, color scale, boundary, colorbar, reference geometry) and a defaults mapping for the appearance parameters of single plot functions. The call says which data drives a channel; the style supplies the default look of everything else, and an explicit argument wins. Presets default (new look of all library plots), dark and classic (today's output), a registry for custom styles, a per-call style argument, a style_context manager and a session-level set_style. Animation timing is a separate morph_timeline helper. The first PR covers the flow plots and animations; symbol, Voronoi and proportional plots follow.
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
| frame | 1080 x 1080 at dpi 120 (social), or 1920 x 1080 (talk) |
| motion | hold 1.5 s, eased morph 7 s, hold 2.5 s, eased return 5 s; cosine easing; fixed extent; solver snapshots as keyframes |

The first six rows are look. Frame size and motion are not look; see "Figure size" and "Animation timing".

## What the library offers now (survey)

- Flow: `Cartogram.plot` / `plot_cartogram` take `cmap` (default `RdYlGn_r`), `legend` and `**kwargs` for `GeoDataFrame.plot`. The six `animate_*` functions take `cmap` (default `viridis`), `colorbar`, `colorbar_label`, `colorbar_kwargs`, `title`, `figsize`. The color normalization is built inside as `plt.Normalize(vmin, vmax)`; `norm=` is not accepted, which is why the talk passes log10 values and relabels the ticks by hand. `DensityPlotOptions` and `VelocityPlotOptions` have their own `cmap`, `color` and `colorbar_kwargs`.
- Symbol: `SymbolCartogram.plot` has 38 parameters (`cmap`, `norm`, `facecolor`, `edgecolor`, `linewidth`, ten legend options, label options, `alpha_range`, `linewidth_range`, `edge_cmap`, hatches). Voronoi has `cell_style`, `point_style`, `geometry_style`, `adjacency_style`, `displacement_style` dicts. Proportional has `background_*` and `complement_*` parameters.
- No shared object, no way to set the look once, no surface color, no typography, no colormap truncation. Fixed values are spread over the plot code: overlay colors (`#e74c3c`, `#27ae60`, `#e67e00`, `#2c7bb6`, black, gray), reference geometry (`#f0f0f0` / `#888888`, `lightgray`), font sizes (8-12 pt), legend and grid settings.
- Plot functions are mostly axes-level (`ax=None` creates a figure; about 30 of them), a few are figure-level (the animations, `plot_comparison`, some Voronoi plots), and some take both `ax` and `figsize`.

## Principles

1. **The call says what is encoded; the style says what it looks like.** The call carries the binding of data to a channel (which column or array drives fill, edge, alpha, line width, hatch or label), legend toggles, `show_axes`, titles and `norm=`. The style carries the default value of every appearance parameter: colors, palettes, ranges, widths and sizes. An explicit argument of the call always wins over the style.
2. **Precedence:** explicit argument of the call, then the style, then the library default. For this to work, defaults that are in signatures today (`cmap="RdYlGn_r"`, `cmap="viridis"`, `edge_cmap="viridis"`) become `None` in the signature and are resolved inside.
3. **Build on matplotlib, do not duplicate it.** Whatever `rcParams` can express stays in `rcParams`; the style adds only what matplotlib cannot express.
4. **Predictable palettes.** A palette follows the data type of its channel and nothing else; it does not depend on the channel or on which other channels are present.

## Design

### `PlotStyle`

A frozen dataclass in a new module `carto_flow/style.py`, exported from the package. It has three parts.

**1. `rc`: matplotlib rcParams.** A dict of rcParams, applied with `matplotlib.rc_context` while a plot function draws. It holds everything matplotlib already expresses: figure, axes and savefig facecolor, text and tick colors, font family and sizes (`font.size`, `axes.labelsize`, `axes.titlesize`, `xtick.labelsize`, `legend.fontsize`), grid, legend frame, the color cycle (`axes.prop_cycle`, used for line series and overlays). `PlotStyle.from_mplstyle(name_or_path)` builds a style from an existing matplotlib stylesheet, so a user's own stylesheets are a usable base.

**2. Library-specific fields.** What `rcParams` cannot express:

| field | meaning |
|---|---|
| `palettes` | a `Palettes(sequential, sequential_range, diverging, categorical)` that applies to every color channel: `sequential` and `diverging` are colormaps (name or `Colormap`), `sequential_range` is the `(lo, hi)` truncation of the sequential map, `categorical` is a colormap name or a list of colors |
| `channel_palettes` | optional overrides per channel, `{"edge": Palettes(sequential="Oranges"), "label": ...}`; the channels are `fill`, `edge` (also lines, arrows and adjacency links) and `label`; a field left `None` falls back to `palettes` |
| `color_scale` | `"linear"`, `"log"` or `"auto"` (log when all values are positive and span more than `log_span` decades) |
| `log_span` | decades that trigger `"auto"`, default 1.0 |
| `tick_format` | `"plain"` or `"si"` (`1M`, `2.5k`); with a log norm, ticks at 1, 2, 5 per decade |
| `boundary_color`, `boundary_width` | region edge color and width, where the call does not pass `edgecolor` / `linewidth` (to be checked: whether geopandas takes its default edge from `patch.edgecolor`; if so these move to `rc`) |
| `colorbar_orientation`, `colorbar_shrink`, `colorbar_pad`, `colorbar_aspect` | colorbar placement |
| `colorbar_outline_color`, `colorbar_outline_width` | colorbar spines |
| `reference_fill`, `reference_edge`, `reference_width` | context geometry (original outline in comparisons, `background_*` of the partition plot, `base_*` of dot density) |
| `annotation_size` | in-map labels; their color stays automatic (white or black by fill luminance) unless the call sets it |

**3. `defaults`: a mapping for appearance parameters of single plot functions.** The long tail (the symbol plot alone has about 40 appearance parameters) cannot each be a typed field. `defaults` is keyed by parameter name, for example `{"alpha_range": (0.3, 1.0), "linewidth_range": (0.5, 3.0), "hatch_linewidth": 0.8}`. It applies to every plot function that has a parameter of that name, when the call does not set it; functions without such a parameter ignore it. Names are validated when a style is created or registered, against the parameter names of the public plot functions, so a typo raises an error. These parameter names are treated as public API (a rename would break styles that use them). Voronoi's `cell_style`, `point_style` and other element dicts stay as the last, most specific override of the call; the defaults they override come from the style fields above.

Methods: `copy_with(**changes)` (the convention of `MorphOptions`), `colormap(role, channel)` (the palette object, truncated where it applies), `norm(values, role, center=None)`, `colorbar(fig, ax, mappable, label)` and `legend(ax, ...)` (apply the colorbar and legend settings, so users of plain matplotlib can reuse them), `apply(fig)` (surface and text on a figure and its axes), `rc_params()` (the `rc` dict, for `plt.rc_context(style.rc_params())` in the user's own code), `to_dict()` / `from_dict()` (sharing a style as a file). Validation at construction: color and colormap names, `cmap_range` in 0..1 with lo < hi, enumerated values.

### Palettes by data role and channel

A role (sequential, diverging, categorical) is a property of the data; a channel (fill, edge, label) is where the color is drawn. The style therefore has one set of role palettes, `palettes`, and optional per-channel sets, `channel_palettes`. Each channel's own data decides the role (the plot function detects it); the palette is then `channel_palettes[channel].<role>` if set, else `palettes.<role>`.

| role | detected when | palette field | colorbar or legend |
|---|---|---|---|
| sequential | numeric column (default) | `sequential`, `sequential_range`; `color_scale`, `tick_format` apply | colorbar |
| diverging | the call gives `center=`, or the plot function declares it for its own columns (the signed error columns) | `diverging`, symmetric norm around the center | colorbar |
| categorical | categorical, string or boolean dtype, or `categorical=True` | `categorical` | legend (sizes from `rc`) |

- The rule is local: the palette depends on the role of the channel's own data and on the channel, never on other channels. A continuous fill with a categorical edge uses `palettes.sequential` and `palettes.categorical`; no counting or cycling.
- An edge map is not a role: an edge can be continuous, diverging or categorical, and `channel_palettes["edge"]` can override any of the three. The built-in presets set no channel overrides, so the default behavior is "numeric data is always drawn with the style's ramp, wherever it appears".
- Call arguments (`cmap=`, `edge_cmap=`, `label_cmap=`) name a palette for that channel and override the style whatever the role.
- The role palettes of a preset are designed together (similar saturation and lightness, tuned to the surface); a figure in PR A checks that a continuous fill with a categorical edge reads as one family.
- Integer-coded categories (FIPS-like codes) are numeric and take the sequential palette unless `categorical=True` is passed (the same as geopandas). An ordered categorical dtype is categorical with a sequential palette sampled at the number of levels (to be confirmed).
- New call arguments this needs: `center=`, `categorical=`, `norm=`.

### Color scale and `norm=`

- The flow animations and plots accept `norm=` (a `Normalize`); `vmin` / `vmax` are taken from it. This removes the log10-values workaround.
- The scale is a data transform, so the call can always set it (`norm=` or `scale=`). The style supplies the default (`color_scale`) and the tick format. With `"auto"`, the scale is resolved once over all data shown by the call (all keyframes of an animation, both panels of a comparison), never per frame or per axes, and the colorbar label says when the scale is logarithmic. `"log"` with zeros or negatives raises a clear error; `"auto"` falls back to linear.

### Presets and registry

- `PlotStyle.default()`: the new look of the library, used when nothing else is selected. It is the talk look with ordinary type sizes (tinted surface, boundary slightly darker than the surface, truncated `YlGnBu`, `color_scale="auto"`, outlined colorbar). It changes the output of every flow plot and animation, so the PR carries before/after figures and a prominent CHANGELOG entry under Changed.
- `PlotStyle.dark()`: the same design on a dark surface (dark surface and boundary slightly lighter than it, light text, `viridis` truncated to 0.25-1.0, the same diverging and categorical maps without the softening). It is a separate preset, not derived from `default`, because the sequential ramps and the contrast relations invert.
- `PlotStyle.classic()`: no rc entries and every library field `None`, today's output. `PlotStyle()` equals `classic()`.
- Palettes of `default`, to be checked on the PR A palette figure: sequential `YlGnBu` truncated to 0.22-1.0; diverging `RdYlBu_r` (its pale-yellow center differs from the blue-gray surface, which a white-centered map would not); categorical `tab10` mixed 15 % toward the surface so fills do not glare.
- No size in a preset name or preset. The large type of the talk (20 / 22 pt) and the frame sizes are recipes in the docs: `register_style("talk", PlotStyle.default().copy_with(rc={**default.rc, "xtick.labelsize": 20, "axes.labelsize": 22}))`, with `figsize` and `dpi` passed to the call.
- Custom presets: `register_style(name, style)`, `get_style(name)`, and `style="name"` is accepted wherever a style is. The built-in names `default` and `classic` cannot be overwritten (`overwrite=True` is not offered for them); other names raise on a duplicate unless `overwrite=True`.

### Selecting a style

1. `style=` on the plot and animation functions: a `PlotStyle`, a registered name, or `None`. `None` means "use the context or session style"; to get no styling at all, pass `classic`.
2. `with carto_flow.style_context(style): ...` sets the style for a block, for example a docs gallery script (a `contextvars.ContextVar`, so it is safe in threads and async code). It accepts a name or an object.
3. `carto_flow.set_style(style)` sets the session-level style (like `plt.style.use`); `set_style(None)` resets to `default`; `get_style()` returns the style in effect. It is process-wide state by design, documented as such.
4. Otherwise `PlotStyle.default()`.

Order of precedence for the style itself: `style=` of the call, then `style_context`, then `set_style`, then `default`.

### Axes-level and figure-level functions

The style always applies to the axes it draws on, set explicitly on a passed-in `ax` (axes facecolor, boundary, colorbar or legend). The figure facecolor is set only when the function creates the figure; on a figure the user passed in, the user calls `style.apply(fig)`. `rc_context` affects only artists created while it is open, as with any matplotlib style: text the user adds after the call (`ax.set_title(...)`) uses the user's own rcParams, unless they wrap the code in `style_context` or `plt.rc_context(style.rc_params())`. In animations the context is open while the artists are created and while `save_animation` saves, so the saved frame has the surface color.

### Figure size

`figsize` and `dpi` are not in the style: most plot functions are axes-level, and a style that forced a size would be wrong for a plot placed in a user's subplot grid. They stay call arguments.

### Existing options objects

`DensityPlotOptions` and `VelocityPlotOptions` stay. Their `cmap` and `color` defaults become `None` and are resolved from the style with the same precedence.

### Coordination with the symbol plot's per-symbol channels

The symbol plot has face color, edge color, alpha, line width, hatch and label color/size, each a literal, a column name or an array. The style does not duplicate the binding. Contact points: (1) every color channel resolves its role with the same helper and takes the palette from the style; (2) the per-channel `*_legend_kwds` start from the legend settings of the style; (3) the same precedence. This is PR B, where the symbol plot is refactored around a shared channel resolver.

### Combining with matplotlib

- The user's `plt.style.use(...)` or rcParams still apply to everything the style does not set (`classic` sets nothing). A style that sets an rc entry wins over the user's rcParams for that entry; an explicit argument of the call wins over both.
- Fields depend on each other: the truncated colormap and the near-background boundary work on a tinted surface. `copy_with(rc=... new background)` does not change them. The docs state that these move together; there is no automatic derivation.

### Animation timing is not part of the style

Hold, morph and return durations, easing and the loop are about time and are already expressed through `keyframe_times` and `linear_over("time")`. Proposal: a helper `morph_timeline(snapshots, hold_start=1.5, morph=7.0, hold_end=2.5, back=5.0, easing="cosine")` returning `(keyframes, times)` for `animate_geometry_keyframes`, replacing the talk's `loop_timeline` and `ease_inv`; `back=0` for a time series that plays forward only. `fps`, `dpi` and `figsize` stay explicit arguments.

### Other parts (issue point 4)

Preset bundles for `MorphOptions` and layout options already exist as classmethods and do not share fields with a plotting style. No shared mechanism is proposed; the convention (`copy_with`, classmethod presets) is already the same.

## Scope and order

1. PR A: `style.py` with only what the flow plots and animations use (`rc`, `palettes`, `channel_palettes`, `color_scale`, `tick_format`, `boundary_*`, `colorbar_*`, `defaults`), `Cartogram.plot`, `plot_cartogram`, `plot_comparison`, the field plots, the six `animate_*` functions, `save_animation`, `norm=`, `center=`, `categorical=`, `set_style` and `style_context`, the `dark` preset, `morph_timeline`, the palette figure, before/after figures (classic against default), a docs page on styling.
2. PR B: symbol, Voronoi and proportional plots; `reference_*`, `annotation_size`, the hatch and range defaults; the shared channel resolver. Until B lands those plots keep their current look, so the docs gallery is consistent only after B.
3. Issue 82: the talk visuals as gallery examples, using the `talk` recipe.

## Tests

Precedence (call over style over library default) for every resolved setting; role detection (numeric, string, boolean, categorical dtype, integer codes, `center=`); `style_context` isolation across threads; rcParams unchanged after a plot call, also after an exception; the saved animation frame has the surface color; `norm=` accepted by every animation; unknown names in `defaults` raise; the registry rejects overwriting `default` and `classic`; `classic` output is identical to the output before the PR.

## Decisions (from review)

1. Name: `PlotStyle`; the old-look preset is `classic`.
2. Figure size and dpi are not in the style.
3. `default` is a good-looking new style; no `slides` preset.
4. The docs use one consistent style (`default`).
5. One palette per data role, detected from the data, local to the channel; no colormap cycle.
6. Users can register styles; `style="name"` is accepted.
7. The style builds on matplotlib: an `rc` dict plus library-specific fields and a `defaults` mapping.
8. The style holds the default of every appearance parameter, including the per-channel palettes and ranges; the call holds the data binding.

9. `set_style(...)` exists for session-level use; `style_context` and `style=` override it.
10. A `dark` preset is included. In the docs the gallery images are built with `default`; the light-and-dark theme question for static images (for example a dark variant of each image shown with Material's `#only-dark` / `#only-light` suffix) is part of issue 82, not of the style PRs.
11. Accessibility checks are not part of the style system; users can check a style with external tools. The built-in palettes start from matplotlib's perceptually reasonable maps.
12. Palettes of `default` and `dark`: as listed under Presets, adjusted on the PR A palette figure.

## Open decisions

None open at the design level. Items to verify during PR A: whether geopandas takes its default edge color from `patch.edgecolor` (then `boundary_*` move to `rc`), that `rc_context` covers the animation artists, and the ordered-categorical rule.
