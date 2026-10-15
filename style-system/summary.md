---
title: Style system and presets for plots and animations
description: Proposal for issue 99. A frozen PlotStyle dataclass (surface, boundary, text, colormaps per data role, color scale, typography, colorbar) with a default preset that is the new look of all library plots and a classic preset that reproduces today's output, a small registry for custom presets, a per-call style argument and a style_context manager. Explicit arguments beat the style and the style beats the library defaults. Figure size and dpi are not part of the style. Animation timing is a separate morph_timeline helper, not part of the style. The flow animations accept norm=, and a log norm gets real-number tick labels from the style. First PR covers the flow plots and animations; symbol, Voronoi and proportional plots follow.
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

A frozen dataclass in a new module `carto_flow/style.py`, exported from the package. A field set to `None` leaves the matplotlib or library default alone; `PlotStyle()` is therefore the classic look, and `PlotStyle.default()` sets the fields of the new look.

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
| `reference_fill`, `reference_edge`, `reference_width` | context geometry drawn under or beside a cartogram (original outline in comparisons, `background_*` of the partition plot, `base_*` of dot density) |
| `series_colors` | short color cycle for annotation overlays and line series (convergence lines, threshold lines, displacement arrows, adjacency and centroid markers, velocity arrows) |
| `annotation_size`, `legend_size` | in-map labels (symbol and cell labels) and legend text; label color stays automatic (white or black by fill luminance) unless the call sets it |
| `grid_color` | grid and axes lines of non-map plots (convergence, histograms) |
| `tick_format` | `"plain"` or `"si"` (`1M`, `2.5k`); with a log norm the ticks are placed at 1, 2, 5 per decade |

Methods: `copy_with(**changes)` (the convention of `MorphOptions`), `colormap()` (the truncated colormap object), `norm(values)` (the `Normalize` or `LogNorm` the scale implies), `colorbar(fig, ax, mappable, label)` (applies the colorbar fields and tick labeling, so users of plain matplotlib can reuse it), `apply(fig)` (surface and text colors on a figure and its axes).

### Presets and registry

- `PlotStyle.default()`: the new look of the library, used when nothing else is selected. It is the talk look with ordinary type sizes (tinted surface, boundary slightly darker than the surface, truncated `YlGnBu`, `color_scale="auto"`, outlined colorbar). It changes the output of every flow plot and animation, so the PR carries before/after figures and a CHANGELOG entry under Changed.
- `PlotStyle.classic()`: all fields `None`, today's output, for users who want the old look.
- No size in a preset name or preset. The large type of the talk (20 / 22 pt) and the frame sizes (1920 x 1080, 1080 x 1080) are recipes in the docs: `register_style("talk", PlotStyle.default().copy_with(tick_size=20, label_size=22))`, with `figsize` and `dpi` passed to the call.
- Custom presets: `register_style(name, style)`, `get_style(name)`, and `style="name"` is accepted wherever a style is.

### Axes-level and figure-level functions

The plot functions are mostly axes-level (`ax=None` creates a figure; about 30 of them), a few are figure-level (the animations, `plot_comparison`, some Voronoi plots) and some have both `ax` and `figsize`. The style follows that: it always applies to the axes it draws on (axes facecolor, boundary, text, colorbar or legend). The figure facecolor is set only when the function creates the figure; on a figure the user passed in, the user calls `style.apply(fig)`. Hence `figsize` and `dpi` stay call arguments: a style that forced a size would be wrong for a plot placed in a user's subplot grid.

### Selecting a style

1. `style=` argument on the plot and animation functions (a `PlotStyle`, a registered name, or `None`).
2. `with carto_flow.style_context(PlotStyle.slides()): ...` sets the style for a block, for example a docs gallery script (a `contextvars.ContextVar`, so it is safe in threads and async code).
3. Otherwise `PlotStyle.default()`.

No global setter: process-wide state is easy to forget in notebooks.

The docs gallery and notebooks use `PlotStyle.default()` without per-script code, so the docs have one consistent style; the talk visuals of issue 82 use the `talk` recipe above.

Precedence for every setting: explicit argument of the call, then the style, then the library default. For this to work the library defaults that are now in signatures (`cmap="RdYlGn_r"`, `cmap="viridis"`) become `None` in the signature and are resolved inside, with the same effective default as now.

### Elements the plot functions do not style now but should

Found by reading the plot code. These are hard-coded today and become style fields (the new fields above):

- Overlay and line colors: Voronoi uses `#e74c3c`, `#27ae60`, `#e67e00`, `#2c7bb6`, black and gray for centroids, displacement, thresholds and convergence lines; the flow convergence plots use `gray`; the flow field animations draw velocity arrows in `black`.
- Reference geometry: Voronoi comparison draws the original as `#f0f0f0` with `#888888` edges, the symbol plot draws it as `lightgray`, the partition plot and dot density have their own `background_*` and `base_*` parameters.
- Font sizes: titles 10-12 pt, labels 8-9 pt, colorbar labels 8-9 pt, legends 8 pt, set per call.
- Legend frame and text, grid lines of the non-map plots, the axes and tick colors of the convergence plots.
- Animations: figure and axes facecolor, the `savefig` facecolor (without it the saved video has a white frame around a tinted axes), the colorbar outline.

Left to call arguments: the mappings of data to a visual channel (which column drives it, `alpha_range`, `linewidth_range`, `hatch_map`, `edge_cmap` when a dict maps categories, legend toggles), `show_axes` and titles. The rule is: **the call says what is encoded, the style says what it looks like by default.** So the defaults that are hard-coded today become style defaults, and an explicit argument still wins:

| element | what the call keeps | what the style provides |
|---|---|---|
| `edge_cmap` (default `viridis`) | which column or weights drive the edge color | the palette, by data role (`cmap` for numeric, `categorical_colors` for categories) when `edge_cmap` is not given |
| hatches | the column and `hatch_map` | the default hatch cycle and hatch line width (low priority; stays in code in PR B unless wanted) |
| Voronoi `cell_style`, `point_style`, `geometry_style`, `adjacency_style`, `displacement_style` | per-element matplotlib keyword overrides (they stay as the last, most specific layer) | the defaults those dicts override: edge and fill colors, marker colors (from `boundary_*`, `reference_*`, `series_colors`) |
| tile colors (`assigned_color` `#d4e6f1`, `unassigned_color` `#f5f5f5`) | the argument | the defaults: assigned = a pale tint of the sequential palette, unassigned = `reference_fill` |

### Coordination with the data-driven channels of the symbol plot

The symbol plot already has a per-symbol system: each of face color, edge color, alpha, line width, hatch and label color/size is a literal, a column name or an array, with its own `cmap`, `norm`, range and legend arguments. The new style system should not duplicate it, but the two need three points of contact:

1. One role resolution. Every color channel decides continuous, diverging or categorical from its data in the same way as the fill (one shared helper), and takes the palette for that role from the style. Today each channel has its own default palette argument.
2. One legend default. The per-channel `*_legend_kwds` start from the style's legend size and frame.
3. Same precedence. Channel argument, then style, then library default, so `facecolor="gdp", cmap="Reds"` behaves as before.

This belongs to PR B, where the symbol plot is refactored around a shared channel resolver; PR A (flow) has only the fill channel and needs no more than the role detection.

### Other cartograms

The proposed fields are enough for the colors, type and surfaces of all four cartogram types once the fields above are added; no cartogram-specific keywords are needed in the style. What is cartogram-specific (symbol sizes and shapes, hatch patterns, Voronoi point markers, tile layout) is geometry or data encoding and stays in the plot functions' own arguments. A function that needs a color the style does not name takes it from `series_colors` by position.

### Matplotlib stylesheets and rcParams

A `PlotStyle` is not an `rcParams` dict, because the main fields (colormap roles and truncation, log colorbar, boundary color relative to the surface, reference geometry) are not rcParams. The two systems combine like this:

- A user's `plt.style.use(...)` or `rcParams` still applies to everything the style leaves at `None` (`classic` leaves everything). `PlotStyle.default()` sets values explicitly, so for the elements it names (surface, text color, font sizes, boundary, colormaps) it wins over a stylesheet; an explicit argument of the call wins over both.
- Generic text and axes settings (font family and sizes, text and tick colors, axes and figure facecolor, grid color, `savefig.facecolor`) are applied through one `matplotlib.rc_context` that the plot functions open while drawing, so every element is covered, including legends and tick labels, without styling each artist. The context is open while the animation creates its artists and while `save_animation` saves, so the saved frame uses the surface color.
- The library-specific fields are applied by explicit calls on the artists.
- `PlotStyle.rc_params()` returns the generic subset as a dict, so a user can reuse the look in own matplotlib code with `plt.rc_context(style.rc_params())`. 

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

Hold, morph and return durations, easing and the loop are about time, not appearance, and they are already expressed through `keyframe_times` and `linear_over("time")`. Proposal: a small helper `morph_timeline(snapshots, hold_start=1.5, morph=7.0, hold_end=2.5, back=5.0, easing="cosine")` returning `(keyframes, times)` to pass to `animate_geometry_keyframes`, replacing the talk's `loop_timeline` and `ease_inv`. Optional `back=0` for a time series that plays forward only. `fps`, `dpi` and `figsize` stay explicit arguments.

### Other parts (issue point 4)

Preset bundles for `MorphOptions` and layout options already exist as classmethods and do not share fields with a plotting style. No shared mechanism is proposed; the convention (`copy_with`, classmethod presets) is already the same.

## Scope and order

1. PR A: `style.py`, flow `Cartogram.plot`, `plot_cartogram`, `plot_comparison`, the six `animate_*` functions and `save_animation`; `norm=`; `morph_timeline`; tests; before/after figures (classic against default) and a docs page on styling.
2. PR B: symbol, Voronoi and proportional plots (their existing `facecolor`, `edgecolor`, `cell_style` parameters stay and win over the style). Until B lands those plots keep their current look, so the docs gallery is consistent only after B.
3. Issue 82: the talk visuals as gallery examples, using the `talk` recipe.

## Decisions (from review)

1. Name: `PlotStyle`; the old-look preset is `classic`.
2. Figure size and dpi: not in the style (the plot functions are mostly axes-level).
3. The default preset is a good-looking style and may differ from today's output; `classic` keeps the old look; no `slides` preset (size is not a style).
4. The docs use one consistent style (`default`).
5. One palette per data role (sequential, diverging, categorical), detected from the data.
6. Users can register styles; `style="name"` is accepted.

## Still open

1. Which look the new default should have beyond the talk palette: proposed as the talk palette with ordinary type sizes; the diverging and categorical palettes are not decided (suggested: `RdBu_r`-based diverging truncated like the sequential one, and `tab10`-like categorical softened toward the surface).
