"""Figures for the grid-vs-mosaic comparison.

Reads ``placements/*.pkl`` (written by ``run.py``) and ``results.jsonl``.

    PYTHONPATH=<checkout of origin/main>/src uv run python \
        visual_checks/grid-vs-mosaic-similarity/figures.py
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
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PLACEMENTS = HERE / "placements"


def load(name):
    with (PLACEMENTS / f"{name}.pkl").open("rb") as f:
        return pickle.load(f)


def _blocks(tiles, nbrs) -> int:
    """Connected components of ``tiles`` under the lattice edge-adjacency."""
    ts = set(tiles)
    seen: set[int] = set()
    n = 0
    for start in tiles:
        if start in seen:
            continue
        n += 1
        stack = [start]
        seen.add(start)
        while stack:
            t = stack.pop()
            for u in nbrs.get(t, ()):
                if u in ts and u not in seen:
                    seen.add(u)
                    stack.append(u)
    return n


def noncontiguous(tile_of_region, nbrs) -> list[int]:
    """Regions whose tiles do not form one edge-connected block."""
    return [g for g, tiles in enumerate(tile_of_region) if tiles and _blocks(tiles, nbrs) > 1]


def split_groups(tile_of_region, nbrs, group_labels) -> list[int]:
    bad = []
    for gid in np.unique(group_labels):
        members = np.flatnonzero(group_labels == gid).tolist()
        tiles = [t for g in members for t in tile_of_region[g]]
        if tiles and _blocks(tiles, nbrs) > 1:
            bad.append(int(gid))
    return bad


def colour_for(i, n):
    cmap = plt.get_cmap("tab20")
    return cmap((i * 7 % 20) / 20.0 + 1e-6)


def panel(ax, pay, colour_index, n_colour, title, mark_regions, mark_label):
    polys = pay["polygons"]
    marked = set(mark_regions)
    for g, tiles in enumerate(pay["tile_of_region"]):
        c = colour_for(colour_index[g], n_colour)
        for t in tiles:
            xy = np.array(polys[t].exterior.coords)
            ax.add_patch(
                MplPolygon(
                    xy,
                    facecolor=c,
                    edgecolor="#b00020" if g in marked else "white",
                    linewidth=1.6 if g in marked else 0.4,
                    zorder=2 if g in marked else 1,
                )
            )
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    extra = f"\n{len(marked)} {mark_label}" if mark_label else ""
    ax.set_title(title + extra, fontsize=10)


def comparison_figure(input_name, names, titles, colour_index, n_colour, group_labels, outfile):
    fig, axes = plt.subplots(1, len(names), figsize=(6 * len(names), 6))
    for ax, name, title in zip(axes, names, titles):
        pay = load(name)
        nbrs = pay["neighbours"]
        if group_labels is None:
            marks = noncontiguous(pay["tile_of_region"], nbrs)
            label = "non-contiguous regions"
        else:
            marks_g = set(split_groups(pay["tile_of_region"], nbrs, group_labels))
            marks = [g for g in range(len(pay["tile_of_region"])) if group_labels[g] in marks_g]
            label = f"regions in {len(marks_g)} split groups"
        panel(ax, pay, colour_index, n_colour, title, marks, label)
    fig.suptitle(input_name, fontsize=13)
    fig.tight_layout()
    fig.savefig(outfile, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", outfile)


METRIC_KEYS = [
    ("displacement", "median_tiles", "displacement median (tiles)", "origin_weight"),
    ("displacement", "p90_tiles", "displacement p90 (tiles)", "origin_weight"),
    ("adjacency", "frac_edge_adjacent", "adjacency preserved (frac)", "neighbor_weight"),
    ("direction", "median_abs_dev_deg", "direction median |dev| (deg)", "topology_weight"),
    ("direction", "frac_reversed_gt90", "direction reversed >90 (frac)", "topology_weight"),
    ("compactness", "polsby_popper_mean", "Polsby-Popper mean", "compactness"),
    ("spread", "aspect_ratio_vs_input", "occupied aspect / input aspect", "compactness"),
    ("spread", "bbox_fill_frac", "occupied bbox fill fraction", "compactness"),
]
KNOBS = ["origin_weight", "neighbor_weight", "topology_weight", "compactness"]


def sweep_figure(records, outfile, case, case_label):
    fig, axes = plt.subplots(4, len(METRIC_KEYS), figsize=(3.1 * len(METRIC_KEYS), 11), sharex="row")
    for r, knob in enumerate(KNOBS):
        rows = sorted(
            [
                x
                for x in records
                if x.get("sweep_knob") == knob
                and x.get("sweep_case", "states") == case
                and "error" not in x
            ],
            key=lambda x: x["sweep_value"],
        )
        xs = [x["sweep_value"] for x in rows]
        for c, (sec, key, label, owner) in enumerate(METRIC_KEYS):
            ax = axes[r, c]
            ys = [x[sec][key] for x in rows]
            own = owner == knob
            ax.set_xscale("symlog", linthresh=0.1)
            ax.plot(xs, ys, marker="o", color="#b00020" if own else "#888888", lw=2 if own else 1.2)
            ax.set_xlabel(knob, fontsize=8)
            if r == 0:
                ax.set_title(label, fontsize=9)
            if own:
                ax.set_facecolor("#fff4f4")
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.3)
    fig.suptitle(
        f"Grid weight sweep - {case_label} (red = the knob's own achieved metric; others held at defaults)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", outfile)


def main():
    from carto_flow.data import load_us_census

    records = [json.loads(l) for l in (HERE / "results.jsonl").open()]

    states = load_us_census(population=True).reset_index(drop=True)
    idx = np.arange(len(states))

    # --- primary case: one tile per region (the gallery / preset case) ------
    comparison_figure(
        "US states, one tile per region (gallery case: no size, no tile_count) - hexagon tiling",
        ["states_uniform__grid", "states_uniform__mosaic_morph__rep0", "states_uniform__mosaic_nomorph"],
        ["grid (defaults)", "mosaic (morph=True)", "mosaic (morph=False)"],
        colour_index=idx,
        n_colour=len(states),
        group_labels=None,
        outfile=HERE / "states_uniform_grid_vs_mosaic.png",
    )
    comparison_figure(
        "US states, one tile per region - square tiling (the demers_cartogram shape)",
        [
            "states_uniform_sq__grid",
            "states_uniform_sq__mosaic_morph__rep0",
            "states_uniform_sq__mosaic_nomorph",
        ],
        ["grid (defaults)", "mosaic (morph=True)", "mosaic (morph=False)"],
        colour_index=idx,
        n_colour=len(states),
        group_labels=None,
        outfile=HERE / "states_uniform_square_grid_vs_mosaic.png",
    )

    # --- multi-tile variant --------------------------------------------------
    comparison_figure(
        "US states, 154 tiles via tile_count - hexagon tiling",
        ["states__grid", "states__mosaic_morph__rep0", "states__mosaic_nomorph"],
        ["grid (defaults)", "mosaic (morph=True)", "mosaic (morph=False)"],
        colour_index=idx,
        n_colour=len(states),
        group_labels=None,
        outfile=HERE / "states_grid_vs_mosaic.png",
    )

    # --- grouped variant -----------------------------------------------------
    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    _, groups = np.unique(districts["State Name"].to_numpy(), return_inverse=True)
    if (PLACEMENTS / "districts__grid.pkl").exists():
        comparison_figure(
            "US congressional districts (432 regions, group_by='State Name') - coloured by state",
            ["districts__grid", "districts__mosaic_morph__rep0", "districts__mosaic_nomorph"],
            ["grid (defaults, ignores group_by)", "mosaic (morph=True)", "mosaic (morph=False)"],
            colour_index=groups,
            n_colour=int(groups.max()) + 1,
            group_labels=groups,
            outfile=HERE / "districts_grid_vs_mosaic.png",
        )

    # --- sweeps --------------------------------------------------------------
    for case, label, out in [
        ("states_uniform", "US states, one tile per region", "grid_weight_sweep_uniform.png"),
        ("states", "US states, 154 tiles via tile_count", "grid_weight_sweep_states154.png"),
    ]:
        if any(x.get("sweep_knob") and x.get("sweep_case", "states") == case for x in records):
            sweep_figure(records, HERE / out, case, label)


if __name__ == "__main__":
    main()
