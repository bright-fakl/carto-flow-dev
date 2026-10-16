"""Figures for the non-contiguous cartogram: the reference densities, the growth limit and the multipolygon modes.

    uv run python make_figures.py   # in a checkout of the PR branch
"""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import carto_flow.data as data
from carto_flow.noncontiguous_cartogram import create_noncontiguous_cartogram

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DPI = 80

states = data.load_us_census(population=True, simplify=1000).reset_index(drop=True)


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


densest = create_noncontiguous_cartogram(states, "Population")
largest_capped = create_noncontiguous_cartogram(states, "Population", reference="largest")
largest_free = create_noncontiguous_cartogram(states, "Population", reference="largest", max_scale=None)

strip(
    "fig_references.png",
    [
        lambda: densest.plot(facecolor="Population").ax.figure,
        lambda: largest_capped.plot(facecolor="Population").ax.figure,
        lambda: largest_free.plot(facecolor="Population").ax.figure,
    ],
    (
        "densest (default): nothing grows",
        f"largest, capped at 1 ({largest_capped.capped.sum()} states smaller than proportional)",
        "largest, no cap (11 states grow)",
    ),
)
strip(
    "fig_styles.png",
    [lambda s=s: densest.plot(facecolor="Region", style=s).ax.figure for s in ("classic", "default", "dark")],
    ("classic", "default", "dark"),
)

# multipolygons: Michigan (two peninsulas and islands) at a scale of 0.5, about the group centroid and about each part
michigan = states[states["State Name"] == "Michigan"].copy()
reference = float(michigan["Population"].iloc[0] / michigan.geometry.area.iloc[0]) / 0.5**2
group = create_noncontiguous_cartogram(michigan, "Population", reference=reference, multipart="group")
partsmode = create_noncontiguous_cartogram(michigan, "Population", reference=reference, multipart="parts")
print(group.scale, len(michigan.geometry.iloc[0].geoms))


def zoomed(cartogram):
    fig = cartogram.plot(legend=False).ax.figure
    return fig


strip(
    "fig_multipart.png",
    [lambda: zoomed(group), lambda: zoomed(partsmode)],
    ("multipart='group' (default)", "multipart='parts'"),
    size=(6.0, 5.0),
)
