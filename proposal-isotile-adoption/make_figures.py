"""Figures of the page: holes and positions of the current triangle tiling, false edge contacts, layouts before and after.

Produces fig1_holes.png (current TriangleTiling against isotile's fill_region), fig2_adjacency.png (edge links of a
curved tiling: geometric method of carto-flow against the lattice table of isotile) and fig3_layouts.png (grid and
mosaic layouts of the 49 US states with the current tilings and with the wrapper prototype). Bundled data only.

Run from a carto-flow checkout, with isotile available:

    uv run --with <isotile checkout or git+https://github.com/bright-fakl/isotile@a66ed7a> python make_figures.py [holes] [adjacency] [layouts]

The layout runs use the wrapper prototype of ``wrapper_proto.py``, written into a temporary copy of the checkout's
sources (the checkout itself is not modified).
"""

from __future__ import annotations

import os
import pickle
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.collections import LineCollection, PolyCollection
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
CHECKOUT = Path(os.environ.get("CARTO_FLOW", Path.cwd())).resolve()
INK, MUTED = "#222222", "#888888"
BLUE, GREEN, RED, AMBER = "#0072B2", "#009E73", "#D55E00", "#E69F00"


def polys_to_collection(polys, **kw):
    return PolyCollection([np.array(p.exterior.coords) for p in polys], **kw)


def fig_holes() -> None:
    from carto_flow.symbol_cartogram.tiling import TriangleTiling
    from isotile import IsohedralTiling as IT

    size = 0.25
    # elongated triangle with the largest sampled hole of 300 random triangles (seed 0), found by random_shapes.py
    rng = np.random.default_rng(0)
    cands = []
    while len(cands) < 300:
        p = rng.uniform(-1, 1, (3, 2))
        if Polygon(p).area > 0.02:
            cands.append(p)

    def covered(polys, region, n=6000):
        pts = shapely.points(np.random.default_rng(5).uniform(region[:2], region[2:], (n, 2)))
        hit = shapely.STRtree(polys).query(pts, predicate="within")
        return len(np.unique(hit[0])) / n

    region0 = (-1.0, -1.0, 1.0, 1.0)
    worst, worst_cov = None, 1.0
    for p in cands[:80]:
        res = TriangleTiling(Polygon(p)).generate(bounds=region0, tile_size=size, margin=0.0, compute_adjacency=False)
        c = covered(res.polygons, region0)
        if c < worst_cov:
            worst, worst_cov = p, c
    rows = [
        ("equilateral triangle, region centered at (3, 3)", TriangleTiling.equilateral(), IT.triangle(), (2.0, 2.0, 4.0, 4.0), 0.2),
        (f"random elongated triangle, region at the origin", TriangleTiling(Polygon(worst)), None, region0, size),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    for r, (title, old, new, region, s) in enumerate(rows):
        res = old.generate(bounds=region, tile_size=s, margin=0.0, compute_adjacency=False)
        if new is None:
            unit = np.array(old.canonical_tile.exterior.coords[:-1])
            new = IT.triangle(unit)
        tiles = new.fill_region(region, tile_size=s)
        for c, (polys, label) in enumerate(((res.polygons, f"TriangleTiling.generate: {res.n_tiles} tiles"), (tiles.polygons(), f"isotile fill_region: {len(tiles)} tiles"))):
            ax = axes[r, c]
            ax.add_collection(polys_to_collection(polys, facecolors="#cfe3f2", edgecolors=BLUE, linewidths=0.5))
            x0, y0, x1, y1 = region
            ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=RED, lw=1.5)
            ax.set_xlim(x0 - 0.3, x1 + 0.3)
            ax.set_ylim(y0 - 0.3, y1 + 0.3)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(label, fontsize=10, color=INK)
        axes[r, 0].set_ylabel(title, fontsize=9, color=INK)
    fig.suptitle("Red: requested region (margin 0). Left: current class. Right: isotile.", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(HERE / "fig1_holes.png", dpi=130)
    plt.close(fig)


def fig_adjacency() -> None:
    from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old
    from isotile import IsohedralTiling as New

    p = Old._PRESETS["wavy_square"]
    old = Old.from_preset("wavy_square").generate(bounds=(-1, -1, 1, 1), n_tiles=36, margin=0.0)
    tiles = New.from_preset("wavy_square").fill_region((-1, -1, 1, 1), n_tiles=36)
    c_old = np.array([[q.centroid.x, q.centroid.y] for q in old.polygons])
    c_new = np.array([[q.centroid.x, q.centroid.y] for q in tiles.polygons()])
    from scipy.spatial import cKDTree

    d, j = cKDTree(c_new).query(c_old)
    keep = np.flatnonzero(d < 1e-6)
    e_old = np.asarray(old.adjacency)[np.ix_(keep, keep)]
    e_new = tiles.adjacency("edge")[j[keep]][:, j[keep]].toarray()
    pts = c_old[keep]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.8))
    polys = [old.polygons[i] for i in keep]
    for ax, title in zip(axes, ("current geometric method (tolerance 0.01 tile sizes)", "isotile lattice table"), strict=True):
        ax.add_collection(polys_to_collection(polys, facecolors="#f1f1f1", edgecolors=MUTED, linewidths=0.4))
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10, color=INK)
    segs = lambda m: [(pts[a], pts[b]) for a, b in zip(*np.nonzero(np.triu(m)), strict=True)]  # noqa: E731
    both = e_old & e_new
    axes[0].add_collection(LineCollection(segs(both), colors=GREEN, linewidths=1.4))
    axes[0].add_collection(LineCollection(segs(e_old & ~e_new), colors=RED, linewidths=1.4))
    axes[1].add_collection(LineCollection(segs(e_new), colors=GREEN, linewidths=1.4))
    n_false = int(np.triu(e_old & ~e_new).sum())
    fig.suptitle(f"wavy_square: {n_false} of {int(np.triu(e_old).sum())} links of the current method (red) are vertex-only contacts in the lattice table", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(HERE / "fig2_adjacency.png", dpi=130)
    plt.close(fig)


def fig_layouts() -> None:
    from carto_flow.data import load_us_census

    cases = ["states grid hexagon", "states grid triangle", "states mosaic hexagon"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        copy = tmp / "copy"
        copy.mkdir()
        subprocess.run(f"git -C {CHECKOUT} archive HEAD src | tar -x -C {copy}", shell=True, check=True)
        subprocess.run([sys.executable, str(HERE / "wrapper_proto.py"), str(CHECKOUT), str(copy)], check=True)
        runs = {}
        for label, src in (("old", CHECKOUT / "src"), ("new", copy / "src")):
            out = tmp / f"{label}.pkl"
            env = {**os.environ, "PYTHONPATH": str(src)}
            subprocess.run([sys.executable, str(HERE / "golden_layouts.py"), "run", label, str(out), ",".join(cases)], check=True, env=env)
            runs[label] = pickle.load(open(out, "rb"))
    states = load_us_census(population=True).reset_index(drop=True)
    cmap = plt.get_cmap("tab20")
    fig, axes = plt.subplots(len(cases), 2, figsize=(10, 3.9 * len(cases)))
    for r, name in enumerate(cases):
        for c, label in enumerate(("old", "new")):
            res = runs[label][name]
            ax = axes[r, c]
            polys = [shapely.from_wkb(w) for w in res["tile_polygon_wkb"]]
            region_of = {}
            for g, tiles in enumerate(res["tiles_of_region"]):
                for t in tiles:
                    region_of[t] = g
            colors = [cmap(region_of[t] % 20) for t in res["assigned"].tolist()]
            ax.add_collection(polys_to_collection(polys, facecolors=colors, edgecolors="white", linewidths=0.4))
            for g in states.geometry:
                for part in getattr(g, "geoms", [g]):
                    ax.plot(*part.exterior.xy, color=INK, lw=0.3, alpha=0.5)
            ax.autoscale_view()
            ax.set_aspect("equal")
            ax.axis("off")
            ax.set_title(f"{name}: {'current' if label == 'old' else 'isotile wrappers'} ({res['n_tiles']} lattice tiles)", fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(HERE / "fig3_layouts.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    wanted = sys.argv[1:] or ["holes", "adjacency", "layouts"]  # e.g. `python make_figures.py adjacency`
    for name, fn in (("holes", fig_holes), ("adjacency", fig_adjacency), ("layouts", fig_layouts)):
        if name in wanted:
            fn()
