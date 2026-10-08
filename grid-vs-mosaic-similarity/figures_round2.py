"""Silhouette and mosaic-knob-sweep figures.

    PYTHONPATH=<checkout of origin/main>/src uv run python \
        visual_checks/grid-vs-mosaic-similarity/figures_round2.py
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from shapely.affinity import scale as shp_scale  # noqa: E402
from shapely.affinity import translate as shp_translate  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PLACEMENTS = HERE / "placements"


def _plot_poly(ax, geom, **kw):
    geoms = geom.geoms if hasattr(geom, "geoms") else [geom]
    for g in geoms:
        ax.fill(*g.exterior.xy, **kw)
        for r in g.interiors:
            ax.fill(*r.xy, facecolor="white", edgecolor="none", zorder=kw.get("zorder", 1) + 0.1)


def _outline(ax, geom, **kw):
    geoms = geom.geoms if hasattr(geom, "geoms") else [geom]
    for g in geoms:
        ax.plot(*g.exterior.xy, **kw)


def align(footprint, reference):
    """Same similarity transform the metric uses: area-match, then centroid-match."""
    s = np.sqrt(reference.area / footprint.area)
    a = shp_scale(footprint, xfact=s, yfact=s, origin=footprint.centroid)
    return shp_translate(a, xoff=reference.centroid.x - a.centroid.x, yoff=reference.centroid.y - a.centroid.y)


def silhouette_figure(records, unions, outfile):
    rows = [
        ("states_uniform", "US states, 1 tile/region"),
        ("states", "US states, 154 tiles"),
        ("districts", "432 districts"),
    ]
    cols = [("__grid", "grid"), ("__mosaic_morph__rep0", "mosaic morph=True"), ("__mosaic_nomorph", "mosaic morph=False")]
    fig, axes = plt.subplots(len(rows), len(cols), figsize=(4.6 * len(cols), 3.4 * len(rows)))
    D = {r["name"]: r for r in records}
    for i, (case, rlabel) in enumerate(rows):
        ref = unions["districts" if case == "districts" else "states"]
        for j, (suf, clabel) in enumerate(cols):
            ax = axes[i, j]
            name = case + suf
            with (PLACEMENTS / f"{name}.pkl").open("rb") as f:
                pay = pickle.load(f)
            occ = unary_union(list(pay["polygons"].values()))
            a = align(occ, ref)
            _plot_poly(ax, ref, facecolor="#c9d6e3", edgecolor="none", zorder=1)
            _outline(ax, a, color="#b00020", lw=1.4, zorder=3)
            iou = D[name]["silhouette_vs_original"]["iou_aligned"]
            ax.set_title(f"{rlabel} - {clabel}\nIoU vs original map = {iou:.3f}", fontsize=9)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
    fig.suptitle(
        "Silhouette vs the ORIGINAL map (blue = input union; red = occupied tile footprint,\n"
        "area-matched and centroid-aligned to the input union - no rotation, no shear)",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", outfile)


def silhouette_bars(records, outfile):
    D = {r["name"]: r for r in records}
    groups = [
        ("states_uniform", "states, 1 tile/region\n(hexagon)"),
        ("states_uniform_sq", "states, 1 tile/region\n(square)"),
        ("states", "states, 154 tiles"),
        ("districts", "432 districts"),
    ]
    variants = [("__grid", "grid"), ("__mosaic_morph__rep0", "mosaic T"), ("__mosaic_nomorph", "mosaic F")]
    colours = ["#3a6ea5", "#b00020", "#e6972a"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
    for ax, key, title in [
        (axes[0], "silhouette_vs_original", "vs ORIGINAL input union\n(cross-layout comparable - the headline)"),
        (axes[1], "silhouette_vs_working", "vs the layout's OWN working footprint\n(internal fidelity - NOT comparable across layouts)"),
    ]:
        x = np.arange(len(groups))
        w = 0.26
        for k, (suf, vlabel) in enumerate(variants):
            ys = [D[g + suf][key]["iou_aligned"] for g, _ in groups]
            b = ax.bar(x + (k - 1) * w, ys, w, label=vlabel, color=colours[k])
            ax.bar_label(b, fmt="%.3f", fontsize=7, padding=1)
        ax.set_xticks(x)
        ax.set_xticklabels([lbl for _, lbl in groups], fontsize=8)
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("IoU (aligned)")
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(outfile, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", outfile)


MKNOBS = ["neighbor_weight", "distance_weight", "interior_bonus", "bfs_x_nw"]
MMETRICS = [
    ("displacement", "median_tiles", "displacement median (tiles)"),
    ("adjacency", "frac_edge_adjacent", "adjacency preserved (frac)"),
    ("direction", "median_abs_dev_deg", "direction median |dev| (deg)"),
    ("direction", "frac_reversed_gt90", "direction reversed >90 (frac)"),
    ("silhouette_vs_original", "iou_aligned", "silhouette IoU vs original"),
]
CASES = [("states_uniform", "1 tile/region", "#3a6ea5"), ("states", "154 tiles", "#b00020"), ("districts", "districts", "#2e8b57")]


def mosaic_sweep_figure(records, grid_ref, outfile):
    S = [r for r in records if r.get("msweep_label") and not r.get("msweep_morph") is False]
    fig, axes = plt.subplots(len(MKNOBS), len(MMETRICS), figsize=(3.2 * len(MMETRICS), 2.7 * len(MKNOBS)))
    for i, knob in enumerate(MKNOBS):
        for j, (sec, key, label) in enumerate(MMETRICS):
            ax = axes[i, j]
            for case, clabel, colour in CASES:
                rows = [r for r in S if r["msweep_case"] == case and r["msweep_label"].startswith(knob + "__")]
                rows = sorted(rows, key=lambda r: float(r["msweep_label"].split("__")[-1]))
                xs = [float(r["msweep_label"].split("__")[-1]) for r in rows]
                ys = [r[sec][key] for r in rows]
                ax.plot(xs, ys, marker="o", ms=3, color=colour, lw=1.4, label=clabel if (i == 0 and j == 0) else None)
                gv = grid_ref.get((case, sec, key))
                if gv is not None:
                    ax.axhline(gv, color=colour, ls=":", lw=1.0)
            ax.set_xscale("symlog", linthresh=0.1)
            ax.set_xlabel(knob if knob != "bfs_x_nw" else "neighbor_weight (neighbor_bfs=True)", fontsize=7.5)
            if i == 0:
                ax.set_title(label, fontsize=9)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.3)
    axes[0, 0].legend(fontsize=7, loc="best")
    fig.suptitle(
        "Mosaic HungarianOptions sweep, morph=True (solid = mosaic; dotted = grid's value on the same input)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", outfile)


def main():
    from carto_flow.data import load_us_census

    from metrics import build_study_union

    records = [json.loads(l) for l in (HERE / "results.jsonl").open()]
    D = {r["name"]: r for r in records}

    states = load_us_census(population=True).reset_index(drop=True)
    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    unions = {"states": build_study_union(states), "districts": build_study_union(districts)}

    silhouette_figure(records, unions, HERE / "silhouette_footprints.png")
    silhouette_bars(records, HERE / "silhouette_summary.png")

    grid_ref = {}
    for case in ["states_uniform", "states", "districts"]:
        g = D[case + "__grid"]
        for sec, key, _ in MMETRICS:
            grid_ref[(case, sec, key)] = g[sec][key]
    mosaic_sweep_figure(records, grid_ref, HERE / "mosaic_knob_sweep.png")


if __name__ == "__main__":
    main()
