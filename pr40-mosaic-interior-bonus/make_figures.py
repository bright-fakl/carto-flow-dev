"""Before/after figures for the mosaic interior_bonus default change (0.5 -> 2.0).

Both sides are produced from the same source tree by passing `interior_bonus`
explicitly, so the only difference between the panels is the value itself.

    PYTHONPATH=<PR worktree>/src uv run python \
        visual_checks/pr40-mosaic-interior-bonus/make_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

HERE = Path(__file__).resolve().parent
BEFORE, AFTER = 0.5, 2.0


def blocks(tiles, nbrs):
    ts, seen, n = set(tiles), set(), 0
    for start in tiles:
        if start in seen:
            continue
        n += 1
        stack = [start]
        seen.add(start)
        while stack:
            t = stack.pop()
            for u in nbrs[t]:
                if u in ts and u not in seen:
                    seen.add(u)
                    stack.append(u)
    return n


def analyse(result, n_regions, group_labels):
    """Region -> tiles, plus the non-contiguous regions and split groups."""
    tiles = np.asarray(result.assignments, dtype=int)
    regions = np.asarray(result.source_indices, dtype=int)
    adj = np.asarray(result.tiling_result.adjacency, dtype=bool)
    assigned = set(int(t) for t in tiles)
    nbrs = {int(t): [int(u) for u in np.flatnonzero(adj[t]) if int(u) in assigned] for t in assigned}

    tile_of_region = [[] for _ in range(n_regions)]
    for t, g in zip(tiles.tolist(), regions.tolist()):
        tile_of_region[g].append(int(t))

    noncontig = [g for g, ts in enumerate(tile_of_region) if ts and blocks(ts, nbrs) > 1]
    split = []
    if group_labels is not None:
        for gid in np.unique(group_labels):
            members = np.flatnonzero(group_labels == gid).tolist()
            ts = [t for g in members for t in tile_of_region[g]]
            if ts and blocks(ts, nbrs) > 1:
                split.append(int(gid))
    return tile_of_region, noncontig, split


def colour(i):
    return plt.get_cmap("tab20")((i * 7 % 20) / 20.0 + 1e-6)


def panel(ax, result, tile_of_region, marked, colour_index, title):
    polys = result.tiling_result.polygons
    marked = set(marked)
    for g, tiles in enumerate(tile_of_region):
        c = colour(colour_index[g])
        for t in tiles:
            ax.add_patch(
                MplPolygon(
                    np.array(polys[t].exterior.coords),
                    facecolor=c,
                    edgecolor="#b00020" if g in marked else "white",
                    linewidth=1.8 if g in marked else 0.4,
                    zorder=3 if g in marked else 1,
                )
            )
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=10)


def run(gdf, *, interior_bonus, morph, tiling, tile_count=None, group_by=None):
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

    return create_layout(
        gdf,
        tile_count=tile_count,
        group_by=group_by,
        layout=MosaicLayout(
            tiling=tiling, morph=morph, hungarian_options=HungarianOptions(interior_bonus=interior_bonus)
        ),
        show_progress=False,
    )


def figure(name, caption, gdf, *, morph, tiling, tile_count=None, group_by=None, group_labels=None, colour_index=None):
    n = len(gdf)
    if colour_index is None:
        colour_index = np.arange(n)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
    stats = {}
    for ax, ib, side in [(axes[0], BEFORE, "before"), (axes[1], AFTER, "after")]:
        res = run(gdf, interior_bonus=ib, morph=morph, tiling=tiling, tile_count=tile_count, group_by=group_by)
        tor, noncontig, split = analyse(res, n, group_labels)
        if group_labels is None:
            marked, note = noncontig, f"{len(noncontig)} non-contiguous"
        else:
            marked = [g for g in range(n) if group_labels[g] in set(split)]
            note = f"{len(split)} split groups"
        panel(ax, res, tor, marked, colour_index, f"{side}: interior_bonus={ib}\n{note}")
        stats[side] = {"interior_bonus": ib, "n_noncontiguous": len(noncontig), "n_split_groups": len(split)}
    fig.suptitle(caption, fontsize=12)
    fig.tight_layout()
    out = HERE / f"{name}.png"
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out, stats, flush=True)
    return {name: stats}


def main():
    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * 150)).astype(int)
    districts = load_us_census(population=True, level="congressional_district").reset_index(drop=True)
    _, groups = np.unique(districts["State Name"].to_numpy(), return_inverse=True)

    out = {}
    out |= figure(
        "01_uniform_hex_morphTrue",
        "US states, one tile per region, hexagon, morph=True — IMPROVED",
        states, morph=True, tiling="hexagon",
    )
    out |= figure(
        "02_uniform_hex_morphFalse_REGRESSION",
        "US states, one tile per region, hexagon, morph=False — REGRESSION\n"
        "adjacency preserved 0.596 -> 0.523, reversed >90 deg 0.064 -> 0.119, direction 29.0 -> 34.2 deg",
        states, morph=False, tiling="hexagon",
    )
    out |= figure(
        "03_uniform_square_morphFalse_REGRESSION",
        "US states, one tile per region, square, morph=False — REGRESSION\n"
        "adjacency preserved 0.486 -> 0.468, reversed >90 deg 0.092 -> 0.119, direction 22.6 -> 30.2 deg",
        states, morph=False, tiling="square",
    )
    out |= figure(
        "04_states154_morphTrue",
        "US states, 154 tiles via tile_count, hexagon, morph=True — IMPROVED\n"
        "adjacency preserved 0.706 -> 0.798, displacement median 2.58 -> 2.10 tiles",
        states, morph=True, tiling="hexagon", tile_count="tiles",
    )
    out |= figure(
        "05_districts_groupby_morphTrue",
        "US congressional districts grouped by state, hexagon, morph=True — IMPROVED\n"
        "adjacency preserved 0.477 -> 0.527, direction 29.2 -> 25.9 deg; coloured by state",
        districts, morph=True, tiling="hexagon", group_by="State Name",
        group_labels=groups, colour_index=groups,
    )
    (HERE / "integrity.json").write_text(json.dumps(out, indent=2))
    print("all done")


if __name__ == "__main__":
    main()
