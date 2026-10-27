"""Figures for the isotile phase 2 report.

    uv run --project /home/fakl/isotile-phase2 --group docs python fig.py <output dir>
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

import isotile as it

OUT = Path(sys.argv[1])
PAL = ["#8fb9d9", "#f2c27a", "#a9d3b4", "#d6b3e0", "#e8a9a0", "#c9c9c9"]

# fig1: curved tilings from presets
names = ["scalloped_hexagon", "puzzle_piece", "wavy_triangle", "flowers", "tree", "interlocking_hexagon"]
fig, axes = plt.subplots(1, 6, figsize=(15, 2.8))
for ax, name in zip(axes, names, strict=True):
    t = it.IsohedralTiling.from_preset(name)
    t = t.scaled(1 / np.sqrt(t.area))
    c = t.centroid
    tiles = t.cover((c[0] - 2.2, c[1] - 2.2, c[0] + 2.2, c[1] + 2.2))
    ax.add_collection(PolyCollection(tiles.outlines(), facecolors=[PAL[k % 6] for k in tiles.colors()], edgecolors="#33383d", linewidths=0.6))
    ax.set_xlim(c[0] - 1.8, c[0] + 1.8); ax.set_ylim(c[1] - 1.8, c[1] + 1.8)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(f"{name} (IH{t.type.number})", fontsize=8)
fig.savefig(OUT / "fig1_presets.png", dpi=130, bbox_inches="tight")

# fig2: validity versus amplitude (numbers from evidence_fit.py, seed 0)
amp = ["0.1", "0.3", "0.6", "1.0", "2.0"]
valid = [224, 174, 131, 84, 50]
invalid = [19, 69, 112, 159, 193]
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(amp, valid, color="#2e8b57", label="valid: every draw tiles (0 failures)")
ax.bar(amp, invalid, bottom=valid, color="#d6453d", label="invalid: rejected")
ax.set_xlabel("amplitude (times the edge length)"); ax.set_ylabel("draws (81 types x 3)")
ax.legend(fontsize=8)
fig.savefig(OUT / "fig2_validity.png", dpi=130, bbox_inches="tight")

# fig3: sleeve example (valid despite long excursion) and a crossing one
t41 = it.get_type(41)
from isotile.curves import native_edge_transforms, normalize_curves, outline
fig, axes = plt.subplots(1, 3, figsize=(10, 3.4))
cases = [
    ("long spike: valid, tiles", {0: [[0, 0], [0.45, 0], [0.5, 5], [0.55, 0], [1, 0]]}, {0: "linear"}),
    ("wide sleeve: touching sides, invalid", {0: [[0, 0], [0.2, 0], [0.2, 3], [0.3, 3], [0.3, 0], [1, 0]]}, {0: "linear"}),
    ("bow: crossing, invalid", {0: [[0, 0], [0.8, 0.5], [0.2, 0.5], [1, 0]]}, {0: "linear"}),
]
for ax, (title, curves, modes) in zip(axes, cases, strict=True):
    rep = it.check_prototile(41, edge_curves=curves, edge_curve_modes=modes)
    pts, starts = outline(t41, native_edge_transforms(t41, t41.default_params), normalize_curves(t41, curves, modes))
    closed = np.vstack([pts, pts[:1]])
    for i in range(4):
        seg = closed[starts[i]:starts[i + 1] + 1]
        ax.plot(seg[:, 0], seg[:, 1], color="#d6453d" if i in rep.bad_edges else "#33383d", lw=1.6)
    ax.set_aspect("equal"); ax.set_title(f"{title}\nvalid={rep.valid}, bad_edges={rep.bad_edges}", fontsize=8)
fig.savefig(OUT / "fig3_cases.png", dpi=130, bbox_inches="tight")
