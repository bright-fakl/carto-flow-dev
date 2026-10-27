"""Figures for the isotile phase 1 report: example tilings, adjacency, fill_region, safe ranges.

    uv run --project <carto-flow> --with <isotile checkout> --with matplotlib python fig.py <output dir>
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection, PolyCollection

import isotile as it

OUT = Path(sys.argv[1])
BLUE, AMBER, GREEN, GREY = "#2c6e9e", "#d98200", "#2e8b57", "#8a8f94"
PAL = ["#8fb9d9", "#f2c27a", "#a9d3b4", "#d6b3e0", "#e8a9a0", "#c9c9c9", "#f0e08a", "#9fd0d0", "#d9a77c", "#b7b7e0", "#c7e0a0", "#e0b0c8"]


def draw(ax, ts, colors=None, alpha=1.0, edge="#33383d", lw=0.6):
    polys = ts.vertices()
    fc = [PAL[c % len(PAL)] for c in ts.colors()] if colors is None else colors
    ax.add_collection(PolyCollection(polys, facecolors=fc, edgecolors=edge, linewidths=lw, alpha=alpha))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def region(ax, bounds):
    x0, y0, x1, y1 = bounds
    ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=AMBER, lw=1.5, ls="--")


# ---- fig 1: example tilings -------------------------------------------------------------
specs = [
    ("square()", it.IsohedralTiling.square()),
    ("hexagon(pointy_top=True)", it.IsohedralTiling.hexagon(pointy_top=True)),
    ("hexagon(pointy_top=False)", it.IsohedralTiling.hexagon(pointy_top=False)),
    ("triangle([(0,0),(1,0.15),(0.35,0.8)])", it.IsohedralTiling.triangle([(0, 0), (1, 0.15), (0.35, 0.8)])),
    ("quadrilateral([(0,0),(1,0),(0.8,0.7),(0.1,0.9)])", it.IsohedralTiling.quadrilateral([(0, 0), (1, 0), (0.8, 0.7), (0.1, 0.9)])),
    ("type 7 (defaults)", it.IsohedralTiling(7)),
    ("type 46 (defaults)", it.IsohedralTiling(46)),
]
most = max(it.tiling_types(), key=lambda t: it.get_type(t).n_aspects)
specs.append((f"type {most} ({it.get_type(most).n_aspects} aspects)", it.IsohedralTiling(most)))
fig, axes = plt.subplots(2, 4, figsize=(13, 6.8))
for ax, (title, t) in zip(axes.flat, specs):
    bounds = (0, 0, 3, 2)
    ts = t.fill_region(bounds, n_tiles=36)
    draw(ax, ts)
    ax.set_title(title, fontsize=8)
fig.suptitle("Tilings of one region with fill_region(n_tiles=36); color = tile coloring of the type", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "fig1_tilings.png", dpi=130)
plt.close(fig)

# ---- fig 2: adjacency -------------------------------------------------------------------
cases = [
    ("hexagon", it.IsohedralTiling.hexagon()),
    ("square", it.IsohedralTiling.square()),
    ("triangle", it.IsohedralTiling.triangle([(0, 0), (1, 0.15), (0.35, 0.8)])),
    ("type 7", it.IsohedralTiling(7)),
]
fig, axes = plt.subplots(3, 4, figsize=(13, 9.6))
for col, (name, t) in enumerate(cases):
    ts = t.fill_region((0, 0, 3, 3), n_tiles=60)
    n = len(ts.cell)
    cen = ts.centroids
    mid = int(np.argmin(np.linalg.norm(cen - cen.mean(axis=0), axis=1)))
    edge = ts.adjacency("edge")
    both = ts.adjacency("vertex")
    vonly = ts.adjacency("vertex-only")
    en, vn = set(ts.neighbors(mid, "edge")), set(ts.neighbors(mid, "vertex-only"))
    colors = ["#e0e3e6"] * n
    for i in en:
        colors[i] = "#7fb0d6"
    for i in vn:
        colors[i] = "#9ed0ae"
    colors[mid] = AMBER
    ax = axes[0, col]
    draw(ax, ts, colors=colors)
    ax.set_title(f"{name}: {len(en)} edge (blue), {len(vn)} vertex-only (green)", fontsize=8)
    ax = axes[1, col]
    draw(ax, ts, colors=["#f4f5f6"] * n, edge="#c5c9cd", lw=0.4)
    ei, ej = edge.nonzero()
    keep = ei < ej
    segs = np.stack([cen[ei[keep]], cen[ej[keep]]], axis=1)
    ax.add_collection(LineCollection(segs, colors=BLUE, linewidths=0.9))
    ax.plot(cen[:, 0], cen[:, 1], ".", color=BLUE, ms=3)
    ax.set_title(f"edge adjacency graph: {n} tiles, {int(keep.sum())} links", fontsize=8)
    ax = axes[2, col]
    order = np.lexsort((ts.aspect, ts.cell[:, 1], ts.cell[:, 0]))
    m = both[order][:, order].toarray()
    me = edge[order][:, order].toarray()
    img = np.zeros(m.shape + (3,))
    img[:] = 1.0
    img[m] = (0.62, 0.82, 0.68)
    img[me] = (0.17, 0.43, 0.62)
    ax.imshow(img, interpolation="nearest")
    ax.set_title("adjacency matrix, ordered by cell", fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])
fig.suptitle("Adjacency from the lattice table: one tile, the graph of edge neighbors, and the sparse matrix", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "fig2_adjacency.png", dpi=130)
plt.close(fig)

# ---- fig 3: fill_region -----------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(13, 4.4))
for ax, (title, t, kw) in zip(axes, [
    ("hexagon, n_tiles=40, margin=0", it.IsohedralTiling.hexagon(), dict(n_tiles=40)),
    ("hexagon, n_tiles=40, margin=0.15", it.IsohedralTiling.hexagon(), dict(n_tiles=40, margin=0.15)),
    ("type 46, tile_size=0.3", it.IsohedralTiling(46), dict(tile_size=0.3)),
]):
    bounds = (0, 0, 3, 2)
    ts = t.fill_region(bounds, **kw)
    draw(ax, ts)
    region(ax, bounds)
    ax.set_title(f"{title}: {len(ts.cell)} tiles", fontsize=8)
fig.suptitle("fill_region: the amber dashed rectangle is the requested bounds; tiles cover the region expanded by the margin", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "fig3_fill_region.png", dpi=130)
plt.close(fig)

# ---- fig 4: safe ranges -----------------------------------------------------------------
cand = []
for t in it.tiling_types():
    ty = it.get_type(t)
    for i in range(ty.n_params):
        lo, hi = ty.safe_ranges[i]
        d0 = float(ty.default_params[i])
        for end in (hi, lo):
            # ends at a distance of 5 are the cap of the first version, not validity limits
            if np.isfinite(end) and abs(abs(end - d0) - 5) > 1e-4:
                cand.append((t, i, end))
                break
sel = [c for c in cand if it.get_type(c[0]).n_params <= 2][:3]
fig, axes = plt.subplots(len(sel), 3, figsize=(9.5, 3.1 * len(sel)))
axes = np.atleast_2d(axes)
for r, (t, i, end) in enumerate(sel):
    ty = it.get_type(t)
    d = float(ty.default_params[i])
    sgn = 1 if end > d else -1
    for c, (label, val) in enumerate([("default", d), ("just inside the limit", end - sgn * 0.02 * max(1.0, abs(end - d))), ("just beyond the limit", end + sgn * 0.02 * max(1.0, abs(end - d)))]):
        p = np.array(ty.default_params, float)
        p[i] = val
        V = np.einsum("vkp,p->vk", ty.vertex_coeffs, np.append(p, 1.0))
        rep = it.check_prototile(t, p)
        ax = axes[r, c]
        ax.fill(*V.T, color="#8fb9d9" if rep.valid else "#e8a9a0", ec="#33383d", lw=1.0)
        for e in rep.bad_edges:
            a, b = V[e], V[(e + 1) % len(V)]
            ax.plot(*np.array([a, b]).T, color="#c0392b", lw=3)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"type {t}, parameter {i} = {val:.3f}\n{label}: {'valid' if rep.valid else 'invalid'}", fontsize=8)
fig.suptitle("safe_ranges: the prototile at the default, inside and beyond a finite limit (bad edges in red)", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "fig4_safe_ranges.png", dpi=130)
print("ok", sel)
