"""Figures for the scales of the field and displacement magnitudes: classic against default, and the scales side by side.

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
import carto_flow.voronoi_cartogram as vor
from carto_flow.flow_cartogram.visualization import (
    DensityPlotOptions,
    VelocityPlotOptions,
    plot_convergence,
    plot_density_field,
    plot_velocity_field,
)

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DPI = 80

states = data.load_us_census(population=True, simplify=1000).reset_index(drop=True)
cartogram = flow.create_flow_cartogram(
    states, "Population", options=flow.MorphOptions(grid=64, n_iter=30, save_internals=True, show_progress=False)
)
voronoi = vor.create_voronoi_cartogram(
    states,
    weights="Population",
    backend=vor.RasterBackend(resolution=256, boundary=vor.ElasticBoundary(strength=0.02), adjacency_spring=0.2),
    options=vor.VoronoiOptions(n_iter=100, show_progress=False),
)


def strip(name, draws, titles, size=(5.0, 4.0)):
    images = []
    for draw in draws:
        fig = draw()
        fig.set_size_inches(*size)
        fig.canvas.draw()
        images.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
        plt.close(fig)
    h = min(i.shape[0] for i in images)
    fig, axes = plt.subplots(1, len(images), figsize=(5 * len(images), 4.0), gridspec_kw={"wspace": 0.02})
    for ax, img, title in zip(np.atleast_1d(axes), images, titles):
        ax.imshow(img[:h])
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    fig.savefig(HERE / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


scales = ("linear", "sqrt", "log")
strip(
    "fig_velocity_scales.png",
    [lambda s=s: plot_velocity_field(cartogram, velocity=VelocityPlotOptions(color_by="magnitude", norm=s), style="default").ax.figure for s in scales],
    scales,
)
strip(
    "fig_velocity_alpha_scales.png",
    [lambda s=s: plot_velocity_field(cartogram, velocity=VelocityPlotOptions(alpha_by_magnitude=True, norm=s), style="default").ax.figure for s in scales],
    scales,
)
strip(
    "fig_displacement_scales.png",
    [lambda s=s: vor.plot_displacement(voronoi, norm=s, style="default").ax.figure for s in scales],
    scales,
)
styles = ("classic", "default", "dark")
strip(
    "fig_density_palettes.png",
    [lambda s=s: plot_density_field(cartogram, style=s).ax.figure for s in styles],
    styles,
)
strip(
    "fig_density_ratio_palettes.png",
    [lambda s=s: plot_density_field(cartogram, density=DensityPlotOptions(normalize="ratio"), style=s).ax.figure for s in styles],
    styles,
)
strip(
    "fig_velocity_palettes.png",
    [lambda s=s: plot_velocity_field(cartogram, velocity=VelocityPlotOptions(color_by="magnitude"), style=s).ax.figure for s in styles],
    styles,
)
strip(
    "fig_convergence.png",
    [lambda s=s: plot_convergence(cartogram, style=s).ax.figure for s in styles],
    styles,
)

strip(
    "fig_velocity_direction.png",
    [lambda s=s: plot_velocity_field(cartogram, velocity=VelocityPlotOptions(color_by="direction"), style=s).ax.figure for s in styles],
    styles,
)
