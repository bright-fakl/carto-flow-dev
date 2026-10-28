"""Proof of concept of the ported preview strip render, and its comparison with the current one.

`render_strip_png_old` is `PreviewStrip._render_strip_png` (preview_strip.py 294 to 353) with its input taken from a
carto-flow tiling. `render_strip_png_new` takes an isotile tiling, calls `fill_region` and draws `TileSet.outlines()` (numpy,
no shapely) with matplotlib's object-oriented API (`Figure` and the Agg canvas, no pyplot, so no global state and no lock
between the render thread and the other sessions).

Compared for the 15 presets in three color modes: pixel difference of the two PNGs, and render time.

Run: python preview_render.py > preview_render.txt     (GUI_SRC set)
"""
from __future__ import annotations

import io
import os
import sys
import time
import warnings

import numpy as np

sys.path.insert(0, os.environ["GUI_SRC"])
warnings.simplefilter("ignore")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.image as mimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT  # noqa: E402
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old  # noqa: E402

STRIP_W, STRIP_H, DPI = 300, 90, 100
BOUNDS = (-1, -0.3, 1, 0.3)
CMAP = plt.get_cmap("tab10")


def render_strip_png_old(tiling: Old, mode: str, face="#1f77b4", edge="#333333") -> bytes:
    result = tiling.generate(bounds=BOUNDS, n_tiles=100, margin=0.25, compute_adjacency=False)
    fig, ax = plt.subplots(figsize=(STRIP_W / DPI, STRIP_H / DPI), dpi=DPI)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.3, 0.3)
    ax.axis("off")
    n = len(result.polygons)
    coords, colors = [], []
    for i, (poly, tr) in enumerate(zip(result.polygons, result.transforms, strict=False)):
        px, py = poly.exterior.xy
        coords.append(list(zip(px, py, strict=False)))
        if mode == "uniform":
            colors.append(face)
        elif mode == "aspect":
            colors.append(mcolors.to_hex(CMAP((tr.rotation % 360) / 360.0)))
        else:
            colors.append(mcolors.to_hex(CMAP(i / max(n - 1, 1))))
    ax.add_collection(PolyCollection(coords, facecolors=colors, edgecolors=edge, linewidths=0.3, alpha=0.85))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return buf.getvalue()


def tile_colors(tiles: isotile.TileSet, mode: str, face: str) -> list:
    n = len(tiles)
    if mode == "uniform":
        return [face] * n
    if mode == "aspect":  # one color per aspect of the type
        k = tiles.tiling.type.n_aspects
        return [CMAP(a % 10) for a in tiles.aspect]
    return [CMAP(c % 10) for c in tiles.colors()]  # "coloring": tiles of one color are never adjacent


def render_strip_png_new(tiling: IT, mode: str, face="#1f77b4", edge="#333333", outline=None) -> bytes:
    tiles = tiling.fill_region(BOUNDS, n_tiles=100, margin=0.25, outline=outline)
    fig = Figure(figsize=(STRIP_W / DPI, STRIP_H / DPI), dpi=DPI)
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.3, 0.3)
    ax.axis("off")
    ax.add_collection(PolyCollection(list(tiles.outlines()), facecolors=tile_colors(tiles, mode, face), edgecolors=edge, linewidths=0.3, alpha=0.85))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0)
    return buf.getvalue()


def decode(b: bytes) -> np.ndarray:
    return mimg.imread(io.BytesIO(b))[:, :, :3]


if __name__ == "__main__":
    print(f"{'preset':22s} {'mode':8s} {'shape old/new':>16s} {'differing px':>13s} {'max diff':>9s} {'t_old ms':>9s} {'t_new ms':>9s}")
    ratios = {"uniform": [], "aspect": [], "index/coloring": []}
    t_old_all, t_new_all, t_straight_all, same_straight = [], [], [], []
    for name in isotile.list_presets():
        o, n = Old.from_preset(name), IT.from_preset(name)
        for mode_old, mode_new, key in (("uniform", "uniform", "uniform"), ("aspect", "aspect", "aspect"), ("index", "coloring", "index/coloring")):
            t0 = time.perf_counter()
            a = render_strip_png_old(o, mode_old)
            t1 = time.perf_counter()
            b = render_strip_png_new(n, mode_new)
            t2 = time.perf_counter()
            ia, ib = decode(a), decode(b)
            if ia.shape == ib.shape:
                d = np.abs(ia - ib).max(axis=2)
                frac = float((d > 0.05).mean())
                mx = float(d.max())
            else:
                frac, mx = float("nan"), float("nan")
            ratios[key].append(frac)
            if mode_old == "uniform":
                t_old_all.append((t1 - t0) * 1000)
                t_new_all.append((t2 - t1) * 1000)
                t3 = time.perf_counter()
                c = render_strip_png_new(n, mode_new, outline="straight")
                t_straight_all.append((time.perf_counter() - t3) * 1000)
                same_straight.append(bool(np.array_equal(decode(c), ib)))
            print(f"{name:22s} {key:14s} {str(ia.shape[:2]) + '/' + str(ib.shape[:2]):>20s} {100 * frac:12.2f}% {mx:9.3f} {(t1 - t0) * 1000:9.1f} {(t2 - t1) * 1000:9.1f}")
    print()
    for k, v in ratios.items():
        v = np.array(v)
        print(f"{k:16s}: pixels differing by more than 0.05 in intensity: median {100 * np.nanmedian(v):.2f} %, max {100 * np.nanmax(v):.2f} %, images of different size: {int(np.isnan(v).sum())}")
    print(f"render time (uniform mode, generate/fill_region included): old median {np.median(t_old_all):.1f} ms, new median {np.median(t_new_all):.1f} ms, "
          f"new with outline='straight' median {np.median(t_straight_all):.1f} ms (max {max(t_straight_all):.1f}); image identical to the curved selection in {sum(same_straight)} of {len(same_straight)} presets")
