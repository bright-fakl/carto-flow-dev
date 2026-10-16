"""Figures for the plot style PR for the symbol plots: classic against default and dark.

    uv run python make_figures.py   # in a checkout of the PR branch
"""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import carto_flow.data as data
import carto_flow.symbol_cartogram as sym

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DPI = 80
STYLES = ("classic", "default", "dark")

states = data.load_us_census(population=True, race=True, poverty=True, simplify=1000).reset_index(drop=True)
states["change"] = (states["Population"] - states["Population"].mean()) / states["Population"].mean() * 100
circles = sym.create_symbol_cartogram(
    states, "Population", layout=sym.CirclePackingLayout(max_iterations=200), show_progress=False
)
grid = sym.create_symbol_cartogram(states, "Population", layout=sym.GridBasedLayout(), show_progress=False)


def row(name, draw, styles=STYLES, size=(5.0, 4.0)):
    images = []
    for style in styles:
        fig = draw(style)
        fig.set_size_inches(*size)
        fig.canvas.draw()
        images.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
        plt.close(fig)
    h = min(i.shape[0] for i in images)
    fig, axes = plt.subplots(1, len(images), figsize=(5 * len(images), 4.0), gridspec_kw={"wspace": 0.02})
    for ax, img, style in zip(np.atleast_1d(axes), images, styles):
        ax.imshow(img[:h])
        ax.set_title(style, fontsize=11)
        ax.axis("off")
    fig.savefig(HERE / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


row("fig_fill_default.png", lambda s: circles.plot(style=s).ax.figure)
row("fig_population.png", lambda s: circles.plot(facecolor="Population", style=s).ax.figure)
row("fig_region.png", lambda s: circles.plot(facecolor="Region", style=s).ax.figure)
row("fig_diverging.png", lambda s: circles.plot(facecolor="change", center=0, style=s).ax.figure)
row(
    "fig_edge_hatch_labels.png",
    lambda s: circles.plot(
        facecolor="Population", edgecolor="Region", hatch="Region", linewidth=1.5, labels="State Abbreviation", style=s
    ).ax.figure,
)
row("fig_comparison.png", lambda s: sym.plot_comparison(states, circles, facecolor="Region", style=s).fig, size=(10, 4))
row("fig_adjacency.png", lambda s: sym.plot_adjacency(circles, show_original=True, original_gdf=states, style=s).ax.figure)
row("fig_heatmap.png", lambda s: sym.plot_adjacency_heatmap(circles, labels="State Abbreviation", style=s).ax.figure)
row("fig_tiling.png", lambda s: sym.plot_tiling(grid, style=s).ax.figure)
