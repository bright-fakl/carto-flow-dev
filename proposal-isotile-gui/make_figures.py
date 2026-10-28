"""Figures of the page.

preview_old_new.png     the preview strip of six presets: the current render (carto-flow generate, color by rotation) above the
                        ported render (isotile fill_region, color by aspect), and the 'tree' strip where the current call leaves
                        part of the window uncovered.
validity_report.png     what the editor gets from check_prototile for four curves on IH41: a valid curve, a crossing curve, a
                        valid hairpin and a curve below the clearance. Offending edges (bad_edges) are red.

Run: GUI_SRC=<git archive of the GUI at eb7b79e>/src python make_figures.py   (writes the PNGs next to the script)
"""
from __future__ import annotations

import io
import os
import sys
import warnings
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
warnings.simplefilter("ignore")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.image as mimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import preview_render as pr  # noqa: E402
from isotile import IsohedralTiling as IT, check_prototile  # noqa: E402
from carto_flow.symbol_cartogram.tiling import IsohedralTiling as Old  # noqa: E402

names = ["regular_hexagon", "cairo", "wavy_triangle", "puzzle_piece", "flowers", "tree"]
fig, axes = plt.subplots(len(names), 2, figsize=(8.2, 1.35 * len(names)), dpi=140)
for r, name in enumerate(names):
    a = mimg.imread(io.BytesIO(pr.render_strip_png_old(Old.from_preset(name), "aspect")))
    b = mimg.imread(io.BytesIO(pr.render_strip_png_new(IT.from_preset(name), "aspect", outline="straight")))
    for c, img in enumerate((a, b)):
        ax = axes[r, c]
        ax.imshow(img)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color("#999999")
    axes[r, 0].set_ylabel(name.replace("_", " "), rotation=0, ha="right", va="center", fontsize=8)
axes[0, 0].set_title("current (carto-flow generate, color by rotation)", fontsize=8)
axes[0, 1].set_title("ported (isotile fill_region, color by aspect)", fontsize=8)
fig.tight_layout()
fig.savefig(HERE / "preview_old_new.png")
plt.close(fig)

cases = {
    "valid, 5 control points": [(0, 0), (0.25, 0.12), (0.5, 0.0), (0.75, -0.12), (1, 0)],
    "crossing (bow tie)": [(0, 0), (0.8, 0.5), (0.2, 0.5), (1, 0)],
    "hairpin, arms 0.001 apart: valid": [(0, 0), (0.3, 0.0), (0.499, 0.5), (0.501, 0.5), (0.7, 0), (1, 0)],
    "arms 1e-7 apart: invalid": [(0, 0), (0.3, 0.0), (0.4999999, 0.5), (0.5000001, 0.5), (0.7, 0), (1, 0)],
}
fig, axes = plt.subplots(1, 4, figsize=(9.6, 2.9), dpi=140)
for ax, (title, curve) in zip(axes, cases.items()):
    rep = check_prototile(41, edge_curves={0: curve}, edge_curve_modes={0: "linear" if "bow" in title else "spline"})
    mode = "linear" if "bow" in title else "spline"
    # draw the outline from the draft even when it is invalid: a tiling cannot be built, so place the canonical edge by hand
    from isotile import get_type
    from isotile.curves import native_edge_transforms, normalize_curves, outline

    t = get_type(41)
    p = t.default_params
    curves = normalize_curves(t, {0: curve}, {0: mode})
    maps = native_edge_transforms(t, p)
    pts, starts = outline(t, maps, curves)
    closed = np.vstack([pts, pts[:1]])
    ax.plot(closed[:, 0], closed[:, 1], color="#444444", lw=1.5)
    for e in rep.bad_edges:
        seg = closed[starts[e] : starts[e + 1] + 1]
        ax.plot(seg[:, 0], seg[:, 1], color="#d62728", lw=3)
    v = t.vertex_coeffs @ np.append(p, 1.0)
    ax.plot(*np.vstack([v, v[:1]]).T, color="#999999", lw=0.8, ls="--")
    ax.set_aspect("equal")
    ax.set_title(f"{title}\nvalid={rep.valid}, bad_edges={rep.bad_edges}", fontsize=7)
    ax.set_xticks([])
    ax.set_yticks([])
fig.tight_layout()
fig.savefig(HERE / "validity_report.png")
plt.close(fig)
print("wrote preview_old_new.png, validity_report.png")
