"""Figures and tables of the report from the outputs of experiments.py.

    python make_figures.py <old.pkl> <new.pkl> <output directory>

Needs carto-flow (for the census data) and matplotlib; reads the stored tile polygons, so it does not depend on the
version of the tiling code.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon

from experiments import SCAN, SHIFT, load_inputs, moved

PALETTE = plt.get_cmap("tab20")


def draw(ax, gdf, run, title: str, *, highlight: np.ndarray | None = None, dx: float = 0.0, crop: bool = True) -> None:
    """Lattice (light), assigned tiles (colored by region), region outlines (black)."""
    polys = shapely.from_wkb(run["polygons"])
    patches = [MplPolygon(np.asarray(p.exterior.coords), closed=True) for p in polys]
    ax.add_collection(PatchCollection(patches, facecolor="none", edgecolor="#c9c9c9", linewidth=0.3))
    assigned = run["assignments"]
    regions = run["regions"]
    colors = [PALETTE(int(g) % 20) for g in regions]
    ax.add_collection(
        PatchCollection([patches[t] for t in assigned], facecolor=colors, edgecolor="white", linewidth=0.4, alpha=0.9)
    )
    if highlight is not None and len(highlight):
        ax.add_collection(
            PatchCollection(
                [patches[t] for t in highlight], facecolor="white", edgecolor="#e03131", hatch="////", linewidth=0.8
            )
        )
    gdf.boundary.plot(ax=ax, color="black", linewidth=0.5)
    if crop:
        minx, miny, maxx, maxy = gdf.total_bounds
        pad = 0.04 * max(maxx - minx, maxy - miny)
        ax.set_xlim(minx - pad, maxx + pad)
        ax.set_ylim(miny - pad, maxy + pad)
    else:
        ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(title, fontsize=8.5)


def metric_line(run) -> str:
    s = f"mean dist {run['disp_mean']:.2f}, max {run['disp_max']:.1f}"
    if "unassigned_core" in run:
        s += f"\nunassigned core {run['unassigned_core']}, noncontig. {run['noncontiguous']}"
    return s


def rotation_figures(old, new, states, out: Path) -> None:
    for tiling in ("hexagon", "square"):
        cols = [("centered", 0.0), ("centered", 30.0), ("moved", 30.0)]
        fig, axes = plt.subplots(2, 3, figsize=(13, 7.2))
        for r, (label, runs) in enumerate((("main (rotate about the origin)", old), ("this PR (about the region center)", new))):
            for c, (pos, rot) in enumerate(cols):
                run = runs[("rotation", tiling, pos, rot)]
                dx = SHIFT if pos == "moved" else 0.0
                gdf = states if dx == 0 else moved(states, dx)
                title = f"{label}\n{pos}, rotation {rot:g}\n{metric_line(run)}"
                draw(axes[r, c], gdf, run, title, crop=(pos == "centered"))
        fig.suptitle(f"Grid layout, {tiling}, 49 states. Moved: data 8e6 m east (the old rotation turns the tiles about (0, 0)).", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / f"fig_rotation_{tiling}.png", dpi=130)
        plt.close(fig)


def offsets_figure(new, states, out: Path) -> None:
    rows = [(kind, tiling) for tiling in ("hexagon", "square") for kind in ("grid", "mosaic")]
    offs = [(0.0, 0.0), (0.25, 0.25), (0.5, 0.5)]
    fig, axes = plt.subplots(len(rows), 3, figsize=(13, 4.0 * len(rows)))
    for r, (kind, tiling) in enumerate(rows):
        for c, off in enumerate(offs):
            run = new[("offsets", kind, tiling, off)]
            highlight = unassigned_core(states, run) if kind == "mosaic" else None
            draw(axes[r, c], states, run, f"{kind} {tiling}, offset {off}\n{metric_line(run)}", highlight=highlight)
    fig.suptitle("Offset of the lattice, 49 states (red hatch: core tiles without a region)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "fig_offsets_states.png", dpi=120)
    plt.close(fig)


def unassigned_core(gdf, run, min_overlap: float = 0.1) -> np.ndarray:
    polys = shapely.from_wkb(run["polygons"])
    union = shapely.union_all(list(gdf.geometry))
    area = shapely.area(polys)
    inter = shapely.area(shapely.intersection(polys, union))
    core = np.flatnonzero(inter >= min_overlap * area)
    return np.setdiff1d(core, run["assignments"])


def symmetric_figures(new, grid10, out: Path) -> list[str]:
    lines = []
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.6))
    scans = {}
    for r, tiling in enumerate(("square", "hexagon")):
        table = np.array([[new[("symmetric", tiling, "offset", (u, v))]["unassigned_core"] for v in SCAN] for u in SCAN])
        scans[tiling] = table
        best = min(((u, v) for u in SCAN for v in SCAN), key=lambda p: (table[SCAN.index(p[0]), SCAN.index(p[1])], p))
        worst = max(((u, v) for u in SCAN for v in SCAN), key=lambda p: (table[SCAN.index(p[0]), SCAN.index(p[1])], p))
        for c, off in enumerate(((0.0, 0.0), best, worst)):
            run = new[("symmetric", tiling, "offset", off)]
            tag = ["default", "fewest unassigned", "most unassigned"][c]
            draw(axes[r, c], grid10, run, f"{tiling}, offset {off} ({tag})\n{metric_line(run)}",
                 highlight=unassigned_core(grid10, run))
        lines.append(f"{tiling}: unassigned core tiles over the 5 x 5 scan: min {table.min()}, max {table.max()}, "
                     f"default {table[0, 0]}, offset of the minimum {best}")
    fig.suptitle("Mosaic layout of the 10 x 10 grid of cells (red hatch: core tiles without a region)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "fig_symmetric_tiles.png", dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
    for ax, tiling in zip(axes, ("square", "hexagon")):
        table = scans[tiling]
        im = ax.imshow(table.T, origin="lower", cmap="viridis_r", extent=(-0.1, 0.9, -0.1, 0.9))
        for i, u in enumerate(SCAN):
            for j, v in enumerate(SCAN):
                ax.text(u, v, str(table[i, j]), ha="center", va="center", fontsize=9, color="white" if table[i, j] > table.max() / 2 else "black")
        ax.set_xticks(SCAN)
        ax.set_yticks(SCAN)
        ax.set_xlabel("offset u")
        ax.set_ylabel("offset v")
        ax.set_title(f"{tiling}: unassigned core tiles")
        fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(out / "fig_symmetric_scan.png", dpi=130)
    plt.close(fig)
    return lines


def tables(old, new) -> str:
    out = []
    out.append("| tiling | position | rotation | version | mean distance | largest distance | lattice tiles | seconds |")
    out.append("|---|---|---|---|---|---|---|---|")
    for tiling in ("hexagon", "square"):
        for pos in ("centered", "moved"):
            for rot in (0.0, 30.0):
                for label, runs in (("main", old), ("this PR", new)):
                    r = runs[("rotation", tiling, pos, rot)]
                    out.append(f"| {tiling} | {pos} | {rot:g} | {label} | {r['disp_mean']:.3f} | {r['disp_max']:.2f} | {r['lattice_tiles']} | {r['seconds']:.2f} |")
    out.append("")
    out.append("| layout | tiling | offset | mean distance | largest distance | unassigned core | noncontiguous | seconds |")
    out.append("|---|---|---|---|---|---|---|---|")
    for tiling in ("hexagon", "square"):
        for kind in ("grid", "mosaic"):
            for off in ((0.0, 0.0), (0.25, 0.25), (0.5, 0.5)):
                r = new[("offsets", kind, tiling, off)]
                out.append(f"| {kind} | {tiling} | {off} | {r['disp_mean']:.3f} | {r['disp_max']:.2f} | {r.get('unassigned_core', '')} | {r.get('noncontiguous', '')} | {r['seconds']:.2f} |")
    out.append("")
    out.append("| position | mean distance | largest distance | unassigned core | noncontiguous | seconds |")
    out.append("|---|---|---|---|---|---|")
    for pos in ("centered", "moved"):
        r = new[("mosaic rotation", "hexagon", pos, 30.0)]
        out.append(f"| {pos} | {r['disp_mean']:.3f} | {r['disp_max']:.2f} | {r['unassigned_core']} | {r['noncontiguous']} | {r['seconds']:.2f} |")
    out.append("")
    out.append("| tiling | rotation | mean distance | unassigned core | noncontiguous | seconds |")
    out.append("|---|---|---|---|---|---|")
    for tiling in ("square", "hexagon"):
        for rot in (0.0, 15.0, 30.0, 45.0):
            r = new[("symmetric", tiling, "rotation", rot)]
            out.append(f"| {tiling} | {rot:g} | {r['disp_mean']:.3f} | {r['unassigned_core']} | {r['noncontiguous']} | {r['seconds']:.2f} |")
    return "\n".join(out)


def main() -> None:
    old = pickle.load(open(sys.argv[1], "rb"))
    new = pickle.load(open(sys.argv[2], "rb"))
    out = Path(sys.argv[3])
    data = load_inputs()
    rotation_figures(old, new, data["states"], out)
    offsets_figure(new, data["states"], out)
    lines = symmetric_figures(new, data["grid10"], out)
    text = tables(old, new) + "\n\n" + "\n".join(lines) + "\n"
    (out / "tables.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
