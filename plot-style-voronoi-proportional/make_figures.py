"""Figures for the plot style PR for the Voronoi and proportional plots: classic against default and dark.

    uv run python make_figures.py   # in a checkout of the PR branch
"""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import carto_flow.data as data
import carto_flow.proportional_cartogram as pc
import carto_flow.voronoi_cartogram as vor

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DPI = 80
STYLES = ("classic", "default", "dark")

states = data.load_us_census(population=True, race=True, poverty=True, simplify=1000)
states = states.reset_index(drop=True)
result = vor.create_voronoi_cartogram(
    states,
    weights="Population",
    backend=vor.RasterBackend(resolution=256, boundary=vor.ElasticBoundary(strength=0.02), adjacency_spring=0.2),
    options=vor.VoronoiOptions(n_iter=100, show_progress=False, record_history=True),
)
partition = pc.partition_geometries(
    states,
    columns=["Black or African American", "Asian", "Hispanic or Latino"],
    method="split",
    direction="horizontal",
    alternate=True,
    normalization="row",
)


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


row("fig_voronoi_cells.png", lambda s: result.plot(style=s).ax.figure)
row("fig_voronoi_population.png", lambda s: result.plot(facecolor="Population", legend=True, style=s).ax.figure)
row("fig_voronoi_errors.png", lambda s: result.plot(facecolor="area_error_pct", legend=True, style=s).ax.figure)
row("fig_voronoi_region.png", lambda s: result.plot(facecolor="Region", legend=True, style=s).ax.figure)
row("fig_partitions_category.png", lambda s: pc.plot_partitions(partition, facecolor="category", style=s).ax.figure)
row("fig_partitions_area.png", lambda s: pc.plot_partitions(partition, style=s).ax.figure)
row(
    "fig_dot_density.png",
    lambda s: pc.plot_dot_density(
        states, columns=["Above Poverty Level", "Below Poverty Level"], n_dots=600, normalization="maximum", seed=0, style=s
    ).ax.figure,
)
