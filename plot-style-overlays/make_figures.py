"""Figures for the overlay colors of a style: classic against default and dark.

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
from carto_flow.flow_cartogram.visualization import plot_velocity_field
import carto_flow.symbol_cartogram as sym
import carto_flow.voronoi_cartogram as vor
from carto_flow.voronoi_cartogram.animation import animate_voronoi_history

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DPI = 80
STYLES = ("classic", "default", "dark")

states = data.load_us_census(population=True, race=True, simplify=1000).reset_index(drop=True)
result = vor.create_voronoi_cartogram(
    states,
    weights="Population",
    backend=vor.RasterBackend(resolution=256, boundary=vor.ElasticBoundary(strength=0.02), adjacency_spring=0.2),
    options=vor.VoronoiOptions(n_iter=100, show_progress=False, record_history=True),
)
analysis = result.analyze_topology(group_by="Region")
circles = sym.create_symbol_cartogram(
    states, "Population", layout=sym.CirclePackingLayout(max_iterations=200), show_progress=False
)
grid = sym.create_symbol_cartogram(states, "Population", layout=sym.GridBasedLayout(), show_progress=False)


def row(name, draw, size=(5.0, 4.0)):
    images = []
    for style in STYLES:
        fig = draw(style)
        fig.set_size_inches(*size)
        fig.canvas.draw()
        images.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
        plt.close(fig)
    h = min(i.shape[0] for i in images)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.0), gridspec_kw={"wspace": 0.02})
    for ax, img, style in zip(axes, images, STYLES):
        ax.imshow(img[:h])
        ax.set_title(style, fontsize=11)
        ax.axis("off")
    fig.savefig(HERE / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


row("fig_convergence.png", lambda s: vor.plot_convergence(result, style=s).ax.figure)
row(
    "fig_voronoi_displacement.png",
    lambda s: vor.plot_displacement(result, show_positions=True, show_adjacency=True, style=s).ax.figure,
)
row("fig_topology.png", lambda s: vor.plot_topology(analysis, result, style=s).ax.figure)
row("fig_symbol_displacement.png", lambda s: sym.plot_displacement(circles, style=s).ax.figure)
row("fig_adjacency_nodes.png", lambda s: sym.plot_adjacency(circles, show_symbols=False, style=s).ax.figure)

flow_result = flow.create_flow_cartogram(
    states, "Population", options=flow.MorphOptions(grid=64, n_iter=30, save_internals=True, show_progress=False)
)
row("fig_velocity.png", lambda s: plot_velocity_field(flow_result, style=s).ax.figure)
row("fig_linewidth_legend.png", lambda s: circles.plot(edgecolor="Region", linewidth="Population", legend=False, style=s).ax.figure)
