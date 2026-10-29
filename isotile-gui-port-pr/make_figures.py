# Composes the figures of this page from the images that render_old.py and render_new.py wrote, and prints the pixel
# statistics of the tables. Run:
#   python make_figures.py <old directory> <new directory>
# (needs numpy and matplotlib). Writes fig_strips.png, fig_tree.png, fig_modes.png, fig_linear.png, fig_svg.png here.
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.path import Path as MplPath

old, new = Path(sys.argv[1]), Path(sys.argv[2])
here = Path(__file__).parent
PRESETS = sorted({p.name.split("_uniform_strip")[0] for p in old.glob("*_uniform_strip.png")})
ORDER = [
    "regular_hexagon", "square", "equilateral_triangle", "rhombus", "cairo", "wide_parallelogram", "scalloped_hexagon",
    "wavy_square", "puzzle_piece", "arrow_quad", "wavy_triangle", "interlocking_hexagon", "flowers", "scalloped_quad", "tree",
]
assert sorted(ORDER) == PRESETS


def img(path):
    return mpimg.imread(path)[:, :, :3]


def differing(a, b, tol=0.05):
    """Share of pixels whose intensity differs by more than tol (images of equal size)."""
    if a.shape != b.shape:
        return float("nan")
    return float((np.abs(a.mean(axis=2) - b.mean(axis=2)) > tol).mean())


# --- statistics of the strips: old against new, per color mode ------------------------------------------------
pairs = {"uniform": "uniform", "aspect": "aspect", "index/coloring": ("index", "coloring")}
for label, modes in pairs.items():
    om, nm = (modes, modes) if isinstance(modes, str) else modes
    d = [differing(img(old / f"{p}_{om}_strip.png"), img(new / f"{p}_{nm}_strip.png")) for p in ORDER]
    sizes = sum(img(old / f"{p}_{om}_strip.png").shape == img(new / f"{p}_{nm}_strip.png").shape for p in ORDER)
    print(f"strip {label}: median {100 * np.nanmedian(d):.2f} percent of pixels differ, max {100 * np.nanmax(d):.1f} ({ORDER[int(np.nanargmax(d))]}); equal sizes {sizes} of 15")
    if label == "uniform":
        print("   uniform, per preset:", {p: round(100 * x, 2) for p, x in zip(ORDER, d)})

# --- figure 1: strips ---------------------------------------------------------------------------------------------
fig, axes = plt.subplots(len(ORDER), 4, figsize=(12, 0.82 * len(ORDER)))
for r, name in enumerate(ORDER):
    for c, (src, mode, title) in enumerate([(old, "uniform", "old, uniform"), (new, "uniform", "new, uniform"), (old, "aspect", "old, aspect"), (new, "aspect", "new, aspect")]):
        ax = axes[r, c]
        ax.imshow(img(src / f"{name}_{mode}_strip.png"))
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        if r == 0:
            ax.set_title(title, fontsize=9)
        if c == 0:
            ax.set_ylabel(name.replace("_", " "), rotation=0, ha="right", va="center", fontsize=8)
fig.tight_layout(pad=0.3, h_pad=0.2, w_pad=0.3)
fig.savefig(here / "fig_strips.png", dpi=110)
plt.close(fig)


# --- figure 2: the window of the tree preview, uncovered area in red --------------------------------------------
def window(ax, polygons, title):
    ax.set_facecolor("#e03131")
    ax.add_collection(PolyCollection(polygons, facecolors="#a5d8ff", edgecolors="#333", linewidths=0.4))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.3, 0.3)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=9)
    ax.set_xticks([])
    ax.set_yticks([])


fig, axes = plt.subplots(2, 1, figsize=(8, 5.2))
for ax, src, title in zip(axes, (old, new), ("old: carto-flow generate", "new: isotile fill_region, outline=\"straight\""), strict=True):
    polygons = json.loads((src / "tree_window_tiles.json").read_text())
    window(ax, polygons, f"tree preset, {title}: {len(polygons)} tiles in the expanded region")
fig.tight_layout()
fig.savefig(here / "fig_tree.png", dpi=110)
plt.close(fig)

# --- figure 3: color modes of wavy_triangle (2 aspects) ------------------------------------------------------
name = "wavy_triangle"
fig, axes = plt.subplots(2, 3, figsize=(10, 6.6))
for r, (src, modes) in enumerate([(old, ["uniform", "aspect", "index"]), (new, ["uniform", "aspect", "coloring"])]):
    for c, mode in enumerate(modes):
        ax = axes[r, c]
        ax.imshow(img(src / f"{name}_{mode}_export.png"))
        ax.set_title(f"{'old' if r == 0 else 'new'}: {mode}", fontsize=9)
        ax.axis("off")
fig.tight_layout()
fig.savefig(here / "fig_modes.png", dpi=100)
plt.close(fig)

# --- figure 4: a linear preset (arrow_quad) -------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(10, 5.2))
for ax, src, title in zip(axes, (old, new), ("old: the linear curves are drawn as splines", "new: lines through the control points"), strict=True):
    ax.imshow(img(src / "arrow_quad_aspect_export.png"))
    ax.set_title(f"arrow_quad, {title}", fontsize=9)
    ax.axis("off")
fig.tight_layout()
fig.savefig(here / "fig_linear.png", dpi=100)
plt.close(fig)


# --- figure 5: the SVG exports of one preset ---------------------------------------------------------------------
def svg_polygons(path):
    text = path.read_text()
    out, colors = [], []
    for fill, pts in re.findall(r'<polygon fill="([^"]*)" opacity="[^"]*" points="([^"]*)"', text):
        out.append([[float(v) for v in p.split(",")] for p in pts.split()])
        colors.append(fill)
    return out, colors


fig, axes = plt.subplots(1, 2, figsize=(10, 5.2))
for ax, src, title in zip(axes, (old, new), ("old", "new"), strict=True):
    polygons, colors = svg_polygons(src / "puzzle_piece_export.svg")
    ax.add_collection(PolyCollection(polygons, facecolors=colors, edgecolors="#333", linewidths=0.4, alpha=0.85))
    ax.set_xlim(0, 800)
    ax.set_ylim(800, 0)
    ax.set_aspect("equal")
    ax.set_title(f"puzzle_piece, Medium grid, SVG export, {title}: {len(polygons)} polygons", fontsize=9)
    ax.axis("off")
fig.tight_layout()
fig.savefig(here / "fig_svg.png", dpi=100)
plt.close(fig)

# --- statistics of the SVG exports ------------------------------------------------------------------------------
for name in ("puzzle_piece", "tree", "square"):
    po, _ = svg_polygons(old / f"{name}_export.svg")
    pn, _ = svg_polygons(new / f"{name}_export.svg")
    print(f"svg {name}: old {len(po)} polygons, new {len(pn)} polygons")
