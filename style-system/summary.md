---
title: Style system and presets for plots and animations
description: Proposal for issue 99. PlotStyle is a frozen dataclass that builds on matplotlib: an rcParams dict for text and surface settings (loadable from a matplotlib stylesheet), plus library-specific fields (the appearance of each visual channel when it is not data-driven and its palettes or range when it is, color scale, colorbar, reference layer) and a defaults mapping for the remaining parameters. The plot functions first get one consistent parameter vocabulary, so that every channel has the same parameter names in every function; the style addresses channels, not function-specific names. The call says which data drives a channel; the style supplies the default look of everything else, and an explicit argument wins. Presets default (new look of all library plots), dark and classic (today's output), a registry for custom styles, a per-call style argument, a style_context manager and a session-level set_style. Animation timing is a separate morph_timeline helper. The first PR covers the flow plots and animations; symbol, Voronoi and proportional plots follow.
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

- Flow: `Cartogram.plot` / `plot_cartogram` take `cmap` (default `RdYlGn_r`), `legend` and `**kwargs` for `GeoDataFrame.plot`. Of the seven flow `animate_*` functions, `animate_morph_history`, `animate_geometry_keyframes` and `animate_workflow` take `cmap` (default `viridis`), `colorbar`, `colorbar_label`, `colorbar_kwargs`, `title`, `figsize`; the field animations take none of the color parameters. The color normalization is built inside as `plt.Normalize(vmin, vmax)`; `norm=` is not accepted, which is why the talk passes log10 values and relabels the ticks by hand. `DensityPlotOptions` and `VelocityPlotOptions` have their own `cmap`, `color` and `colorbar_kwargs`.
- Symbol: `SymbolCartogram.plot` has 38 parameters (`cmap`, `norm`, `facecolor`, `edgecolor`, `linewidth`, ten legend options, label options, `alpha_range`, `linewidth_range`, `edge_cmap`, hatches). Voronoi has `cell_style`, `point_style`, `geometry_style`, `adjacency_style`, `displacement_style` dicts. Proportional has `background_*` and `complement_*` parameters.
- No shared object, no way to set the look once, no surface color, no typography, no colormap truncation. Fixed values are spread over the plot code: overlay colors (`#e74c3c`, `#27ae60`, `#e67e00`, `#2c7bb6`, black, gray), reference geometry (`#f0f0f0` / `#888888`, `lightgray`), font sizes (8-12 pt), legend and grid settings.
- Plot functions are mostly axes-level (`ax=None` creates a figure; about 30 of them), a few are figure-level (the animations, `plot_comparison`, some Voronoi plots), and some take both `ax` and `figsize`.

## Principles

1. **The call says what is encoded; the style says what it looks like.** The call carries the binding of data to a channel (which column or array drives fill, edge, alpha, line width, hatch or label), legend toggles, `show_axes`, titles and `norm=`. The style carries the default value of every appearance parameter: colors, palettes, ranges, widths and sizes. An explicit argument of the call always wins over the style.
2. **Precedence:** explicit argument of the call, then the style, then the library default. For this to work, defaults that are in signatures today (`cmap="RdYlGn_r"`, `cmap="viridis"`, `edge_cmap="viridis"`) become `None` in the signature and are resolved inside.
3. **Build on matplotlib, do not duplicate it.** Whatever `rcParams` can express stays in `rcParams`; the style adds only what matplotlib cannot express.
4. **Predictable palettes.** A palette follows the data type of its channel and the channel's own override, never other channels.
5. **One vocabulary.** The same visual concept has the same parameter name in every plot function of every cartogram type. The style addresses channels, so a style works for all functions only if the parameters are named consistently; the renames are done first (PR 0 below).

## Parameter vocabulary

### Channels

The visual channels of a map plot are `fill`, `edge`, `hatch`, `alpha`, `linewidth` and `label` (text). Each has the same parameters wherever it exists:

| channel | binding or literal | palette or range | guide |
|---|---|---|---|
| fill | `facecolor` | `cmap`, `norm`, `vmin`, `vmax` | `legend`, `legend_kwargs`, `legend_label` |
| edge | `edgecolor` | `edge_cmap`, `edge_norm` | `edge_legend`, `edge_legend_kwargs` |
| hatch | `hatch` | `hatch_map` | `hatch_legend`, `hatch_legend_kwargs` |
| alpha | `alpha` | `alpha_range` | `alpha_legend`, `alpha_legend_kwargs` |
| linewidth | `linewidth` | `linewidth_range` | `linewidth_legend`, `linewidth_legend_kwargs` |
| label | `label_color` (and `labels` for the text) | `label_cmap`, `label_fontsize`, `label_fontsize_range` | `label_legend`, `label_legend_kwargs` |

- The fill channel uses matplotlib and geopandas names without prefix (`facecolor`, `cmap`, `norm`, `vmin`, `vmax`, `legend`). Every other channel uses its channel name as prefix for its palette and guide parameters.
- A channel parameter takes a literal, a column name (or built-in quantity such as `"errors_pct"`), or a per-geometry array, the rule the symbol plot already has. For the fill channel this is open decision 1 (geopandas passthrough); the rule below holds for all other channels. A string is resolved by the rule in "Resolving a string parameter" below.
- Layers other than the main geometry use a layer prefix with the channel names: `reference_facecolor`, `reference_edgecolor`, `reference_linewidth`, `reference_alpha` (the original or base layer), `complement_*`, `assigned_*` / `unassigned_*` (tiles).
- Matplotlib keyword overrides of an element are `<element>_kwargs` dicts everywhere (`legend_kwargs`, `arrows_kwargs`, `label_kwargs`, `cell_kwargs`, `point_kwargs`).
- Booleans that show an element are `show_<element>`; `legend` is the one switch of the guide of the fill channel (a colorbar for a continuous role, a legend for a categorical one).

### Resolving a string parameter

A channel parameter that is a string can be a column name, a built-in quantity of the function (`"errors_pct"`, `"density"`, `"area"`) or a color literal (`"red"`, `"#d4e6f1"`, `"C0"`, a gray level such as `"0.5"`). The symbol plot already has this ambiguity and resolves it as follows (`_resolve_color` in `symbol_cartogram/visualization.py`): if the string is a column and also a valid color, it is treated as the **column** and a `UserWarning` is issued; if it is only a color, it is a color; if it is neither, a `ValueError` lists the available columns. This proposal keeps that rule for all functions and extends it to the built-in quantities:

1. an existing column of the data,
2. else a built-in quantity of the function,
3. else a color (or the special values `"none"` and `"face"` for edges, which are never columns),
4. else an error that lists the columns and built-in quantities.

A `UserWarning` is issued when a string matches more than one of the three kinds, and it says how to force each reading: pass the values (`gdf["wheat"]`, an array) to bind data, pass a color tuple (`matplotlib.colors.to_rgb("wheat")`) for a color. Values given by a style (`Channel.value`) are always literals and are never looked up as columns.

Why the column wins: a column that exists in the frame is something the user put there, while color names are a large and unmanaged vocabulary (about 150 CSS names plus single letters, `C0`-`C9`, gray levels such as `"0.5"`), and many are plausible data columns (`wheat`, `gold`, `olive`, `salmon`, `coral`, `snow`, `tan`, `r`, `g`, `b`, a pivoted column named `1`). If the literal won, the call would silently draw a constant color where the user asked for a data-driven map, and the figure would look plausible. If the column wins and the user wanted the literal, the warning appears and the fix is one tuple. An error on every ambiguity would be stricter, but it would break a call that worked as soon as the data gained a column, so it is not proposed.

### Renames

Found by listing the parameters of all public plot, animate and preview functions. Old names stay for one minor release as aliases with a `DeprecationWarning`, using the mechanism the library already has for `grid_size`.

| concept | names found now | one name |
|---|---|---|
| fill by data or color | `column` (flow `plot`, `plot_cartogram`, `plot_comparison`, `animate_geometry_keyframes`, `preview_modulator`; symbol `plot`, `plot_comparison`; Voronoi `plot`, `plot_cartogram`, `plot_comparison`), `color_by` (flow `animate_morph_history`, `animate_workflow`; proportional `plot_partitions`; symbol tiling `plot`), `color_values`, symbol `facecolor` (already a column or a literal; `column` is its backward-compatible shorthand), tiling `face_color` | `facecolor` for every plot (decision 14); `column`, `color_by` and `color_values` are deprecated aliases; `color_values` becomes `facecolor=[arrays]` for keyframes |
| fill colormap | `cmap`, symbol tiling `colormap`, `heatmap_cmap`, `diff_cmap` | `cmap`; the flow modulator preview keeps `heatmap_cmap` and `diff_cmap` for its two extra panels, named `<panel>_cmap` |
| constant fill | `facecolor`, `face_color`, `assigned_color`, `unassigned_color`, `background_color`, `base_color`, `complement_color` | `facecolor`; `assigned_facecolor`, `unassigned_facecolor`, `reference_facecolor`, `complement_facecolor` |
| edge color | `edgecolor`, `edge_color`, `tile_edgecolor`, `core_edgecolor`, `ring_edgecolor`, `background_edgecolor`, `base_edgecolor`, `complement_edgecolor` | `edgecolor`; `tile_edgecolor` stays: the tiling plots forward `**kwargs` to the symbol plot, where `edgecolor` is the edge of the symbols, so the tiles are a layer with its own prefix (`tile_`, like `core_`, `ring_`, `pool_`) |
| line width | `linewidth`, `edge_width`, `tile_linewidth`, `pool_linewidth`, `background_linewidth`, `base_linewidth`, `complement_linewidth` | `linewidth` with the layer prefixes above; `edge_width` becomes `linewidth` of the adjacency links |
| alpha | `alpha`, `edge_alpha`, `arrow_alpha`, `tile_alpha`, `background_alpha`, `base_alpha`, `complement_alpha` | `alpha` with layer prefix; the links of `plot_adjacency` are the layer `link_` (`link_color`, `link_cmap`, `link_alpha`, `link_linewidth`, `link_legend`, `link_legend_kwargs`; a line has a color, not an edge color) and its nodes `node_markersize`; `arrow_alpha`, `arrow_color` move into `arrows_kwargs` |
| colorbar switch and options | `colorbar` (flow animations), `show_colorbar` (modulator previews), `legend` (flow plot, others), `colorbar_kwargs`, `colorbar_label`, `legend_kwds`; symbol `plot_adjacency` and `plot_adjacency_heatmap`: `colorbar`, `colorbar_kwds` (in `plot_adjacency` the guide of the edge color) | `legend`, `legend_kwargs`, `legend_label` for the fill guide; `link_legend`, `link_legend_kwargs` for the colorbar of the link weights of `plot_adjacency` |
| `*_kwds` | symbol `legend_kwds`, `edge_legend_kwds`, `hatch_legend_kwds`, ... | `*_kwargs` |
| element style dicts | Voronoi `cell_style`, `point_style`, `geometry_style`, `adjacency_style`, `displacement_style`, `centroid_style`, `position_style` | `cell_kwargs`, `point_kwargs`, ... |
| text size | `tick_fontsize`, `label_fontsize` | `tick_labelsize` (matplotlib name), `label_fontsize` |
| markers | `node_size`, dot density `size` and `marker` | `markersize`, `marker` |
| text binding | symbol `label` (`plot`, `plot_symbols`), `labels` (Voronoi, adjacency heatmap) | `labels` |
| palette dicts | proportional `palette` (`plot_partitions`, `plot_dot_density`) next to `cmap` | `cmap` accepts a `{category: color}` dict (as the symbol plot does); `palette` is deprecated |
| other | `complement_color_by`, `background_saturation`, `background_lightness`, `highlight`, `arrow_scale`, `label_location`, `color_by_run`, `heatmap_*`, `diff_*`, `image_kwargs`, `show_edges`, `log_scale` (a y-axis scale of the Voronoi convergence plot, not a color scale) | decided in PR 0 from the complete listing |

The table is built from `data/plot_parameters.md` (`list_parameters.py` in this page's folder), the complete list of parameters of every public plot, animate and preview function and of the `DensityPlotOptions` and `VelocityPlotOptions` fields. PR 0 completes it by going through the whole list; the two `preview_modulator` functions (flow `anisotropy` and `density`) are two functions with different panels. `DensityPlotOptions` and `VelocityPlotOptions` (`colorbar`, `colorbar_kwargs`, `color_by`, `normalize`, `color`) follow the vocabulary too, with aliases. Left as they are because they are a different concept: `normalization` (dot density) and `normalize` (compactness) are not color norms; `show_*` toggles; `figsize`, `title`, `show_axes`.

A test lists every public plot, animate and preview function and the plot options dataclasses and fails if a parameter is not on an allowlist (the vocabulary plus the functional parameters such as `ax`, `iteration`, `show_*`), so the vocabulary cannot drift; a regular expression on names would miss `palette`, `size` or `marker`.

## Design

### `PlotStyle`

A frozen dataclass in a new module `carto_flow/style.py`, exported from the package. It has three parts.

**1. `rc`: matplotlib rcParams.** A dict of rcParams, applied with `matplotlib.rc_context` while a plot function draws. It holds everything matplotlib already expresses: figure, axes and savefig facecolor, text and tick colors, font family and sizes (`font.size`, `axes.labelsize`, `axes.titlesize`, `xtick.labelsize`, `legend.fontsize`), grid, legend frame, the color cycle (`axes.prop_cycle`, used for line series and overlays). `PlotStyle.from_mplstyle(name_or_path)` builds a style from an existing matplotlib stylesheet, so a user's own stylesheets are a usable base.

**2. Library-specific fields.** What `rcParams` cannot express:

| field | meaning |
|---|---|
| `palettes` | a `Palettes(sequential, sequential_range, diverging, categorical)` that applies to every color channel: `sequential` and `diverging` are colormaps (name or `Colormap`), `sequential_range` is the `(lo, hi)` truncation of the sequential map, `categorical` is a colormap name, a list of colors or a `{category: color}` dict (the forms the symbol and proportional plots already accept) |
| `channels` | `{"fill": Channel(...), "edge": Channel(...), ...}` for the channels of the vocabulary; a `Channel` has `value` (what the channel looks like when it is not data-driven: a color, a width, an alpha, a hatch pattern or `None`), `palettes` (a `Palettes` that overrides the style-wide one for this channel, color channels only; a field left `None` falls back) and `range` (the output range of a scalar channel when data-driven: `alpha`, `linewidth`, `label_fontsize`). The `hatch` channel has no palettes; the style has a plain `hatch_cycle` field (a tuple of hatch patterns) used for categorical hatching |
| `color_scale` | `"linear"`, `"log"` or `"auto"` (log when all values are positive and span more than `log_span` decades) |
| `log_span` | decades that trigger `"auto"`, default 1.0 |
| `tick_format` | `"plain"` or `"si"` (`1M`, `2.5k`); with a log norm, ticks at 1, 2, 5 per decade |
| `colorbar_orientation`, `colorbar_shrink`, `colorbar_pad`, `colorbar_aspect` | colorbar placement |
| `colorbar_outline_color`, `colorbar_outline_width` | colorbar spines |
| `reference_facecolor`, `reference_edgecolor`, `reference_linewidth`, `reference_alpha` | the reference layer (original outline in comparisons, background of the partition plot, base of dot density), named like the call parameters |
| `semantic_colors` | colors of overlays with a meaning, `{"error", "ok", "warning", "accent", "muted"}` (today `#e74c3c`, `#27ae60`, `#e67e00`, `#2c7bb6`, gray in the Voronoi plots); `axes.prop_cycle` in `rc` is used only for series of lines, because a cycle would reorder semantic colors by draw order |
| `annotation_size` | in-map labels; their color stays automatic (white or black by fill luminance) unless the call sets it |

**3. `defaults`: a mapping for the remaining parameters.** What is neither a channel nor a typed field (legend keyword dicts, label placement, tile layer colors) is keyed by parameter name, for example `{"legend_kwargs": {"frameon": False}}`. Because the vocabulary gives each concept one name in every function, a name-keyed default reaches all functions that have the parameter. Names are validated when a style is created or registered against the parameter names of the public plot functions, so a typo raises an error; the names are public API. A `defaults` key that a typed field or a channel already covers (`facecolor`, `cmap`, `edgecolor`, `reference_*`, ...) is rejected, so there is one way to set each thing. A dict default (`legend_kwargs`) is merged shallowly with the call's dict, and the call's keys win. The element dicts of the call (`cell_kwargs`, `point_kwargs`, ...) stay the last, most specific override; the defaults they override come from the channels and fields above.

Methods: `copy_with(**changes)` (the convention of `MorphOptions`), `colormap(role, channel)` (the palette object, truncated where it applies), `norm(values, role, center=None)`, `colorbar(fig, ax, mappable, label)` and `legend(ax, ...)` (apply the colorbar and legend settings, so users of plain matplotlib can reuse them), `apply(fig)` (surface and text on a figure and its axes), `rc_params()` (the `rc` dict, for `plt.rc_context(style.rc_params())` in the user's own code), `to_dict()` / `from_dict()` (sharing a style as a file; colormaps must be given by name, a `Colormap` object raises a clear error). Validation at construction: color and colormap names, `sequential_range` in 0..1 with lo < hi, enumerated values.

### Palettes by data role and channel

A role (sequential, diverging, categorical) is a property of the data; a channel (fill, edge, label, hatch) is where it is drawn. The style therefore has one set of role palettes, `palettes`, and optional per-channel sets, `channels[channel].palettes`. Each channel's own data decides the role (the plot function detects it); the palette is then `channels[channel].palettes.<role>` if set, else `palettes.<role>`. A channel that is not data-driven uses `channels[channel].value`.

| role | detected when | palette field | colorbar or legend |
|---|---|---|---|
| sequential | numeric column (default) | `sequential`, `sequential_range`; `color_scale`, `tick_format` apply | colorbar |
| diverging | the call gives `center=`, or the plot function declares it for its own columns (the signed error columns) | `diverging`, symmetric norm around the center | colorbar |
| categorical | categorical, string or boolean dtype, or `categorical=True` | `categorical` | legend (sizes from `rc`) |

- The rule is local: the palette depends on the role of the channel's own data and on the channel, never on other channels. A continuous fill with a categorical edge uses `palettes.sequential` and `palettes.categorical`; no counting or cycling.
- An edge map is not a role: an edge can be continuous, diverging or categorical, and `channels["edge"].palettes` can override any of the three. The built-in presets set no channel overrides, so the default behavior is "numeric data is always drawn with the style's ramp, wherever it appears".
- Call arguments (`cmap=`, `edge_cmap=`, `label_cmap=`) name a palette for that channel and override the style whatever the role. A user gets a predictable look for every channel from two rules: not bound to data, it uses `channels[channel].value`; bound to data, it uses the palette for the role of its data (or the `range` of a scalar channel).
- The role palettes of a preset are designed together (similar saturation and lightness, tuned to the surface); a figure in PR A checks that a continuous fill with a categorical edge reads as one family.
- Integer-coded categories (FIPS-like codes) are numeric and take the sequential palette unless `categorical=True` is passed (the same as geopandas). An ordered categorical dtype is categorical with a sequential palette sampled at the number of levels (to be confirmed).
- New call arguments this needs: `center=`, `categorical=`, and `norm=` (also the strings `"linear"`, `"log"`, `"auto"`) in the functions that lack it.

### Color scale and `norm=`

- The flow animations and plots accept `norm=` (a `Normalize`); `vmin` / `vmax` are taken from it. This removes the log10-values workaround.
- The scale is a data transform, so the call can always set it: `norm=` takes a `Normalize` instance or one of `"linear"`, `"log"`, `"auto"`. The style supplies the default (`color_scale`) and the tick format. With `"auto"`, the scale is resolved once over all data shown by the call (all keyframes of an animation, both panels of a comparison), never per frame or per axes, and the colorbar label says when the scale is logarithmic. `"log"` with zeros or negatives raises a clear error; `"auto"` falls back to linear.

### Presets and registry

- `PlotStyle.default()`: the new look of the library, used when nothing else is selected. It is the talk look with ordinary type sizes (tinted surface, boundary slightly darker than the surface, truncated `YlGnBu`, `color_scale="auto"`, outlined colorbar). It changes the output of every flow plot and animation, so the PR carries before/after figures and a prominent CHANGELOG entry under Changed.
- `PlotStyle.dark()`: the same design on a dark surface (dark surface and boundary slightly lighter than it, light text, `viridis` truncated to 0.25-1.0, the same diverging and categorical maps without the softening). It is a separate preset, not derived from `default`, because the sequential ramps and the contrast relations invert.
- `PlotStyle.classic()`: no rc entries and every library field `None`, today's output. `PlotStyle()` equals `classic()`; a custom style starts from `PlotStyle.default().copy_with(...)` (documented). "Library default" in the precedence rule stays per function: today's defaults differ (`RdYlGn_r` in the flow plot, `viridis` in the animations, `tab10` in the workflow convergence plot), and `classic` reproduces each of them.
- Palettes of `default`, to be checked on the PR A palette figure: sequential `YlGnBu` truncated to 0.22-1.0; diverging `RdYlBu_r` (its pale-yellow center differs from the blue-gray surface, which a white-centered map would not); categorical `tab10` mixed 15 % toward the surface so fills do not glare.
- No size in a preset name or preset. The large type of the talk (20 / 22 pt) and the frame sizes are recipes in the docs: `register_style("talk", PlotStyle.default().copy_with(rc_update={"xtick.labelsize": 20, "axes.labelsize": 22}))` (`copy_with(rc=...)` replaces the dict, `copy_with(rc_update=...)` merges into it), with `figsize` and `dpi` passed to the call.
- Custom presets: `register_style(name, style)`, `get_style(name)`, and `style="name"` is accepted wherever a style is. The built-in names `default` and `classic` cannot be overwritten (`overwrite=True` is not offered for them); other names raise on a duplicate unless `overwrite=True`.

### Selecting a style

1. `style=` on the plot and animation functions: a `PlotStyle`, a registered name, or `None`. `None` means "use the context or session style"; to get no styling at all, pass `classic`.
2. `with carto_flow.style_context(style): ...` sets the style for a block, for example a docs gallery script (a `contextvars.ContextVar`, so it is safe in threads and async code). It accepts a name or an object.
3. `carto_flow.set_style(style)` sets the session-level style (like `plt.style.use`); `set_style(None)` resets to `default`; `get_style()` returns the style in effect. It is process-wide state by design, documented as such.
4. Otherwise `PlotStyle.default()`.

Order of precedence for the style itself: `style=` of the call, then `style_context`, then `set_style`, then `default`.

### Axes-level and figure-level functions

The style always applies to the axes it draws on, set explicitly on a passed-in `ax` (axes facecolor, boundary, colorbar or legend). The figure facecolor is set only when the function creates the figure; on a figure the user passed in, the user calls `style.apply(fig)`. `rc_context` affects only artists created while it is open, as with any matplotlib style: text the user adds after the call (`ax.set_title(...)`) uses the user's own rcParams, unless they wrap the code in `style_context` or `plt.rc_context(style.rc_params())`. Animations are rendered later than they are built: the flow animations call `ax.clear()` and replot on every frame (`animation.py`), and the frames are produced by `anim.save()`, `to_jshtml()` or a notebook display, outside any context. So an animation captures the style when it is built and re-enters `rc_context(style.rc)` inside the frame-update callback; `ax.clear()` rebuilds ticks, spines and title from the rcParams in effect at that moment. The figure and axes facecolors are set explicitly on the artists, not through `savefig.facecolor`. This applies to the flow and the Voronoi animations and to both save paths (`save_animation` in each module).

An animation interpolates numeric color values between keyframes. A categorical `facecolor` is not interpolated: the geometry is, and the colors come from one fixed category-to-color map built from the union of the categories of all keyframes, with a legend. A categorical value in a place that needs interpolation (a numeric-only channel such as `alpha`) raises a clear error.

### Figure size

`figsize` and `dpi` are not in the style: most plot functions are axes-level, and a style that forced a size would be wrong for a plot placed in a user's subplot grid. They stay call arguments.

### Existing options objects

`DensityPlotOptions` and `VelocityPlotOptions` stay. Their `cmap` and `color` defaults become `None` and are resolved from the style with the same precedence.

### Coordination with the symbol plot's per-symbol channels

The symbol plot has face color, edge color, alpha, line width, hatch and label color/size, each a literal, a column name or an array. The style does not duplicate the binding. Contact points: (1) every color channel resolves its role with the same helper and takes the palette from the style; (2) the per-channel `*_legend_kwds` start from the legend settings of the style; (3) the same precedence. This is PR B, where the symbol plot is refactored around a shared channel resolver.

### GeoPandas passthrough

The flow plot functions forward `**kwargs` to `GeoDataFrame.plot`. For the fill channel the library passes `legend=False` to geopandas and draws the guide itself with `style.colorbar` or `style.legend`, so the outline, the tick format and the log label of the style apply (geopandas creates its colorbar inside `plot`, where they cannot be patched afterwards). Parameters that only geopandas knows (`missing_kwds`, `scheme`, `k`) pass through unchanged.

### Combining with matplotlib

- The user's `plt.style.use(...)` or rcParams still apply to everything the style does not set (`classic` sets nothing). A style that sets an rc entry wins over the user's rcParams for that entry; an explicit argument of the call wins over both.
- Fields depend on each other: the truncated colormap and the near-background boundary work on a tinted surface. `copy_with(rc=... new background)` does not change them. The docs state that these move together; there is no automatic derivation.

### Animation timing is not part of the style

Hold, morph and return durations, easing and the loop are about time and are already expressed through `keyframe_times` and `linear_over("time")`. Proposal: a helper `morph_timeline(snapshots, hold_start=1.5, morph=7.0, hold_end=2.5, back=5.0, easing="cosine")` returning `(keyframes, times)` for `animate_geometry_keyframes`, replacing the talk's `loop_timeline` and `ease_inv`; `back=0` for a time series that plays forward only. `fps`, `dpi` and `figsize` stay explicit arguments.

### Other parts (issue point 4)

Preset bundles for `MorphOptions` and layout options already exist as classmethods and do not share fields with a plotting style. No shared mechanism is proposed; the convention (`copy_with`, classmethod presets) is already the same.

## Examples

Sketches of the proposed API (nothing is implemented).

**The same call shape for the fill channel in every cartogram type**

| call | note |
|---|---|
| `cart.plot(facecolor="Population")` | flow; was column="Population" |
| `sym.plot(facecolor="Population")` | symbol; unchanged |
| `vor.plot(facecolor="Population")` | Voronoi; was column= |
| `plot_comparison(cart, facecolor="Population")` |  |
| `animate_morph_history(cart, facecolor="density", legend=True)` | was color_by="density", colorbar=True |
| `plot_partitions(gdf, facecolor="area")` | proportional; was color_by="area" |

**Literal, data, scale and role in one parameter set**

| call | note |
|---|---|
| `cart.plot(facecolor="#d4e6f1")` | constant fill |
| `cart.plot(facecolor="Population", cmap="Blues")` | data-driven, palette named in the call |
| `cart.plot(facecolor="Population", norm="log")` | also a Normalize instance |
| `cart.plot(facecolor="Population", center=0)` | diverging around 0 |
| `cart.plot(facecolor="Region", categorical=True)` | force the categorical role |
| `cart.plot(facecolor=gdf["wheat"])` | force data when a column name is also a color name |

**Other channels follow the same rule**

| call | note |
|---|---|
| `sym.plot(facecolor="gdp", edgecolor="region", edge_cmap="Set2", linewidth="pop", linewidth_range=(0.5, 3), hatch="party", alpha="density", alpha_range=(0.3, 1))` | one data-driven channel each |
| `sym.plot(facecolor="gdp", legend=True, edge_legend=True, hatch_legend=False)` |  |
| `sym.plot(labels="name", label_color="black", label_fontsize=7)` | `label=` deprecated for `labels=` |
| `plot_adjacency(sym, edgecolor="weight", edge_cmap="viridis", edge_legend=True)` | was colorbar=True |

**Guides and element dicts use `*_kwargs`**

| call | note |
|---|---|
| `cart.plot(facecolor="Population", legend=True, legend_kwargs={"shrink": 0.6}, legend_label="People")` |  |
| `animate_geometry_keyframes(frames, facecolor=[a0, a1, a2], legend=True)` | was color_values=..., colorbar=True |
| `vor.plot_displacement(arrows_kwargs={"color": "k"}, cell_kwargs={"alpha": 0.5})` | was *_style dicts |

**Layers use a prefix plus the channel name**

| call | note |
|---|---|
| `plot_dot_density(gdf, reference_facecolor="#f0f0f0", reference_edgecolor="#888", marker="o", markersize=4)` |  |
| `sym.plot_tiling(assigned_facecolor="#d4e6f1", unassigned_facecolor="#f5f5f5", core_edgecolor="k")` |  |

**Selecting a style**

| call | note |
|---|---|
| `cart.plot(facecolor="Population")` | default style |
| `cart.plot(facecolor="Population", style="dark")` | a registered name |
| `cart.plot(facecolor="Population", style=PlotStyle.classic())` | today's look |
| `with carto_flow.style_context("dark"): cart.plot(facecolor="Population")` | a block, for example one gallery script |
| `carto_flow.set_style("dark")` | the session, like plt.style.use |

**A style that sets fill, edge and hatch predictably**

| call | note |
|---|---|
| `my = PlotStyle.default().copy_with(channels={"fill": Channel(value="#d4e6f1"), "edge": Channel(value="#444444", palettes=Palettes(sequential="Oranges")), "linewidth": Channel(value=0.6, range=(0.5, 2.5))}, hatch_cycle=("//", "..", "xx"))` | the fill is pale and the edges dark and thin when not data-driven; an edge bound to numeric data uses the orange ramp |
| `register_style("house", my)` | |
| `sym.plot(style="house")` | pale fill, dark thin edges |
| `sym.plot(facecolor="gdp", style="house")` | fill from the sequential palette of the style |
| `sym.plot(edgecolor="weight", style="house")` | edge from the orange ramp |

**Slides and animation**

| call | note |
|---|---|
| `register_style("talk", PlotStyle.default().copy_with(rc_update={"xtick.labelsize": 20, "axes.labelsize": 22}))` |  |
| `keyframes, times = morph_timeline(snapshots)` |  |
| `anim = animate_geometry_keyframes(keyframes, keyframe_times=times, style="talk", figsize=(16, 9), legend=True)` |  |
| `save_animation(anim, "map.mp4", fps=30, dpi=120)` | the saved frame has the style's surface color |

**The look in the user's own matplotlib code**

| call | note |
|---|---|
| `with plt.rc_context(my.rc_params()): fig, ax = plt.subplots()` | the style in the user's own matplotlib code |
| `style.apply(fig)` | a figure the plot function did not create |

**Old names**

| call | note |
|---|---|
| `cart.plot(column="Population")` | works; DeprecationWarning: use facecolor= |
| `animate_morph_history(cart, colorbar=True)` | works; DeprecationWarning: use legend=True |

## Scope and order

0. PR 0 (vocabulary): the renames of the table above in all plot, animate and preview functions of the four cartogram types, with deprecated aliases, the vocabulary test and the docs. No change of output.
1. PR A: `style.py` with only what the flow plots and animations use (`rc`, `palettes`, `channels` for `fill`, `edge` and `label` (`Channel.value`; the per-channel `Channel.palettes` overrides come with PR B, where the symbol plot is the first user), `color_scale`, `tick_format`, `colorbar_*`, `defaults`), `Cartogram.plot`, `plot_cartogram`, `plot_comparison`, the field plots, the seven `animate_*` functions (with `legend` replacing `colorbar`), `save_animation`, `norm=`, `center=`, `categorical=`, `set_style` and `style_context`, the `dark` preset, `morph_timeline`, the palette figure, before/after figures (classic against default), a docs page on styling.
2. PR B: symbol, Voronoi and proportional plots; the `reference_*` layer, `annotation_size`, the `hatch`, `alpha` and `linewidth` channels; the shared channel resolver. Until B lands those plots keep their current look, so the docs gallery is consistent only after B.
3. Issue 82: the talk visuals as gallery examples, using the `talk` recipe.

## Tests

Precedence (call over style over library default) for every resolved setting; role detection (numeric, string, boolean, categorical dtype, integer codes, `center=`); `style_context` isolation across threads; rcParams unchanged after a plot call, also after an exception; the saved animation frame has the surface color; `norm=` accepted by every animation; unknown names in `defaults` raise; the registry rejects overwriting `default` and `classic`; `classic` output is identical to the output before the PR; every deprecated alias gives the same result as the new name and warns; the vocabulary test passes.

## Decisions (from review)

1. Name: `PlotStyle`; the old-look preset is `classic`.
2. Figure size and dpi are not in the style.
3. `default` is a good-looking new style; no `slides` preset.
4. The docs use one consistent style (`default`).
5. One palette per data role, detected from the data, local to the channel; no colormap cycle.
6. Users can register styles; `style="name"` is accepted.
7. The style builds on matplotlib: an `rc` dict plus library-specific fields and a `defaults` mapping.
8. The style holds the default of every appearance parameter, per channel (`value`, `palettes`, `range`); the call holds the data binding.
9. `set_style(...)` exists for session-level use; `style_context` and `style=` override it.
10. A `dark` preset is included. In the docs the gallery images are built with `default`; the light-and-dark theme question for static images (for example a dark variant of each image shown with Material's `#only-dark` / `#only-light` suffix) is part of issue 82, not of the style PRs.
11. Accessibility checks are not part of the style system; users can check a style with external tools. The built-in palettes start from matplotlib's perceptually reasonable maps.
12. Palettes of `default` and `dark`: as listed under Presets, adjusted on the PR A palette figure.
13. All plotting functions use one parameter vocabulary (channels with fixed parameter names, `*_kwargs`, `legend`, layer prefixes); the old names are deprecated aliases for one minor release.
14. The fill channel is bound by `facecolor` in every function (a column, a built-in quantity, an array or a literal); `column`, `color_by` and `color_values` are deprecated aliases, and the flow plots translate to `GeoDataFrame.plot` themselves.

## Open decisions

1. Items to verify: whether geopandas takes its default edge color from `patch.edgecolor` (then the `edge` channel value is partly an `rc` entry) and the ordered-categorical rule.
2. Ambiguous strings: the rule under "Resolving a string parameter" (column, then built-in quantity, then color, with a warning on multiple matches) is a recommendation to be confirmed; the alternatives are literal first (silent wrong map) and an error on ambiguity (breaks working calls when the data gains a column).
