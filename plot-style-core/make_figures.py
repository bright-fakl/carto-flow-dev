"""Figures for the plot style PR: the palettes of the built-in styles and classic against default and dark.

    uv run python make_figures.py   # in a checkout of the PR branch
"""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import carto_flow.data as data
import carto_flow.flow_cartogram as flow
from carto_flow import PlotStyle
from carto_flow.flow_cartogram.animation import animate_geometry_keyframes
from carto_flow.flow_cartogram.visualization import plot_comparison

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DPI = 80

states = data.load_us_census(population=True).reset_index(drop=True)
cartogram = flow.create_flow_cartogram(
    states,
    "Population",
    options=flow.MorphOptions.preset_balanced().copy_with(area_scale=1e-6, n_iter=400, show_progress=False),
)


def triptych(name, draw, styles=("classic", "default", "dark"), figsize=(15, 4.8)):
    """One row of the same plot in several styles: draw(style) returns a figure; the figures are pasted together."""
    images = []
    for style in styles:
        fig = draw(style)
        fig.set_size_inches(*figsize)
        fig.canvas.draw()
        images.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
        plt.close(fig)
    h = min(i.shape[0] for i in images)
    fig, axes = plt.subplots(1, len(images), figsize=(5 * len(images), 4.2), gridspec_kw={"wspace": 0.02})
    for ax, img, style in zip(axes, images, styles):
        ax.imshow(img[:h])
        ax.set_title(style, fontsize=11)
        ax.axis("off")
    fig.savefig(HERE / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def single(**kwargs):
    def draw(style):
        r = cartogram.plot(style=style, **kwargs)
        r.ax.figure.set_size_inches(5, 4.2)
        return r.ax.figure

    return draw


triptych("fig_population.png", single(facecolor="Population"), figsize=(5.2, 4.4))
triptych("fig_errors.png", single(), figsize=(5.2, 4.4))
triptych("fig_categorical.png", single(facecolor="Region"), figsize=(5.2, 4.4))
triptych("fig_density.png", single(facecolor="Population Density"), figsize=(5.2, 4.4))


def comparison(style):
    return plot_comparison(states, cartogram, facecolor="Population", style=style).ax_left.figure


triptych("fig_comparison.png", comparison, styles=("classic", "default"), figsize=(9, 3.6))


def frame(style):
    anim = animate_geometry_keyframes(
        [states, cartogram.to_geodataframe()], duration=1.0, fps=5, facecolor="Population", legend=True, style=style
    )
    anim._init_draw()
    anim._func(3)
    return anim._fig


triptych("fig_animation_frame.png", frame, figsize=(5.2, 4.4))

# palettes of the built-in styles
fig, axes = plt.subplots(3, 3, figsize=(11, 3.6), gridspec_kw={"hspace": 0.9, "wspace": 0.05})
for col, name in enumerate(("classic", "default", "dark")):
    style = PlotStyle.classic() if name == "classic" else (PlotStyle.default() if name == "default" else PlotStyle.dark())
    surface = style.rc.get("figure.facecolor", "white")
    seq = style.colormap("sequential") or matplotlib.colormaps["RdYlGn_r"]
    div = style.colormap("diverging") or matplotlib.colormaps["RdYlGn_r"]
    cats = style.categorical_colors(list(range(10))) or [matplotlib.colormaps["RdYlGn_r"](i / 9) for i in range(10)]
    ramp = np.linspace(0, 1, 256)[None, :]
    for row, (label, cmap_) in enumerate((("sequential", seq), ("diverging", div))):
        ax = axes[row, col]
        ax.imshow(ramp, aspect="auto", cmap=cmap_)
        ax.set_facecolor(surface)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{name}: {label}", fontsize=9, loc="left")
    ax = axes[2, col]
    ax.imshow([[matplotlib.colors.to_rgb(c) for c in cats]], aspect="auto")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{name}: categorical", fontsize=9, loc="left")
fig.savefig(HERE / "fig_palettes.png", dpi=DPI, bbox_inches="tight")
