"""Mosaic ring swap-back reach (8 -> 14 hops) before/after figures.

8 standard configurations: US states, congressional districts, districts with
group_by="State Name", and world (bundled Natural Earth, Mollweide,
tile count ~ pop_est) -- each with morph=True and morph=False.

Usage: make_figures.py <label: before|after> <outdir>
"""

import json
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

import carto_flow.data as cfdata
from carto_flow.symbol_cartogram.layouts import prepare_layout_data
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

WORLD_CRS = "ESRI:54009"  # Mollweide -- equal-area, so tile areas mean something
WORLD_BUDGET = 600


# --------------------------------------------------------------------------- state


def hole_state(lr):
    """Ring tiles used, empty core tiles, and enclosed unassigned cells (any kind)."""
    tr = lr.tiling_result
    core = {int(x) for x in lr.core_tile_indices}
    assigned = {int(t) for t in lr.assignments}
    ring_used = sorted(assigned - core)
    empty_core = sorted(core - assigned)
    enclosed = []
    for t in range(len(tr.polygons)):
        if t in assigned:
            continue
        nbs = np.flatnonzero(tr.adjacency[t])
        if len(nbs) and all(int(x) in assigned for x in nbs):
            enclosed.append(t)
    return {"ring_used": ring_used, "empty_core": empty_core, "enclosed": enclosed}


def draw_holes(ax, lr, st, title):
    """Grey footprint; orange = ring tiles, red = empty core, blue hatch = enclosed."""
    tr = lr.tiling_result
    lr.tiles_gdf.plot(ax=ax, color="#cfd8dc", edgecolor="white", linewidth=0.3)
    if st["empty_core"]:
        gpd.GeoSeries([tr.polygons[t] for t in st["empty_core"]]).plot(
            ax=ax, facecolor="#e53935", edgecolor="black", linewidth=1.0, alpha=0.85, zorder=5
        )
    if st["enclosed"]:
        gpd.GeoSeries([tr.polygons[t] for t in st["enclosed"]]).plot(
            ax=ax, facecolor="#1e88e5", edgecolor="black", linewidth=1.4, hatch="//", zorder=6
        )
    if st["ring_used"]:
        gpd.GeoSeries([tr.polygons[t] for t in st["ring_used"]]).plot(
            ax=ax, facecolor="#fb8c00", edgecolor="black", linewidth=1.0, alpha=0.95, zorder=7
        )
    ax.set_title(
        f"{title}\norange = ring tiles used ({len(st['ring_used'])}),  "
        f"red = empty core ({len(st['empty_core'])}),  "
        f"blue hatch = enclosed ({len(st['enclosed'])})",
        fontsize=9,
    )
    ax.set_axis_off()


def compactness(lr, key_of_geom):
    """Discrete Polsby-Popper on the tile adjacency graph -- combinatorial, reproducible.

    area = tile count, perimeter = boundary-edge count on the tile-adjacency graph.
    NOT geometric Polsby-Popper on unioned tile polygons, which is non-reproducible
    (hairline internal edges leave a non-deterministic perimeter that is then squared).
    """
    tr = lr.tiling_result
    n_sides = max(1, len(tr.polygons[0].exterior.coords) - 1)
    e_len = tr.polygons[0].length / n_sides
    a_tile = tr.polygons[0].area
    by_key = {}
    for t, g in zip(lr.assignments, lr.tiles_gdf["geometry_id"].tolist()):
        by_key.setdefault(key_of_geom[int(g)], set()).add(int(t))
    out = {}
    for k, tiles in by_key.items():
        perim = sum(n_sides - sum(1 for nb in np.flatnonzero(tr.adjacency[t]) if int(nb) in tiles) for t in tiles)
        if perim:
            out[k] = 4 * np.pi * (len(tiles) * a_tile) / ((perim * e_len) ** 2)
    return out


def split_groups(lr, key_of_geom):
    from collections import deque

    adj = lr.tiling_result.adjacency
    by_geom = {}
    for t, g in zip(lr.assignments, lr.tiles_gdf["geometry_id"].tolist()):
        by_geom.setdefault(int(g), []).append(int(t))
    by_group = {}
    for g, tl in by_geom.items():
        by_group.setdefault(key_of_geom[g], []).extend(tl)

    def n_blocks(tiles):
        todo, blocks = set(tiles), 0
        while todo:
            start = todo.pop()
            blocks += 1
            queue = deque([start])
            while queue:
                t = queue.popleft()
                for nb in np.flatnonzero(adj[t]):
                    nb = int(nb)
                    if nb in todo:
                        todo.discard(nb)
                        queue.append(nb)
        return blocks

    return sum(1 for tl in by_group.values() if n_blocks(tl) > 1)


def summarise(case, lr, names, wall):
    st = hole_state(lr)
    m = lr.metrics.algorithm
    pp = compactness(lr, names)
    return {
        "case": case,
        "converged": bool(lr.metrics.converged),
        "ring_used": len(st["ring_used"]),
        "empty_core": len(st["empty_core"]),
        "enclosed": len(st["enclosed"]),
        "split_regions": m.n_noncontiguous_regions,
        "split_groups": m.n_split_groups,
        "regions_correct": f"{m.regions_correct}/{m.regions_total}",
        "pp_min": round(min(pp.values()), 4) if pp else None,
        "pp_mean": round(float(np.mean(list(pp.values()))), 4) if pp else None,
        "wall_s": round(wall, 2),
    }


# --------------------------------------------------------------------------- cases


def world_gdf():
    g = cfdata.load_world()
    g = g[(g["name"] != "Antarctica") & (g["pop_est"] > 0)].copy().to_crs(WORLD_CRS)
    pop = g["pop_est"].to_numpy(dtype=float)
    g["tiles"] = np.maximum(1, np.round(pop / pop.sum() * WORLD_BUDGET)).astype(int)
    return g.reset_index(drop=True)


def run_case(name, data, names, morph, label, outdir, fig_slug):
    t0 = time.perf_counter()
    lr = MosaicLayout(morph=morph).compute(data, show_progress=False)
    wall = time.perf_counter() - t0
    row = summarise(f"{name}/morph={morph}", lr, names, wall)
    st = hole_state(lr)
    fig, ax = plt.subplots(figsize=(10, 6))
    draw_holes(ax, lr, st, f"{name}, morph={morph} -- {label}")
    fig.tight_layout()
    fig.savefig(f"{outdir}/{fig_slug}_{label}.png", dpi=150)
    plt.close(fig)
    return row


def main(label, outdir):
    out = []

    # --- US states
    g = cfdata.load_us_census(population=True)
    g["tiles"] = np.maximum(1, np.round(g["Population"] / g["Population"].sum() * 150)).astype(int)
    d_states = prepare_layout_data(g, tile_count="tiles")
    st_names = list(g["State Name"])
    for morph in (True, False):
        suffix = "states" if morph else "states_nomorph"
        out.append(run_case("states", d_states, st_names, morph, label, outdir, suffix))

    # --- congressional districts, with and without group_by
    gd = cfdata.load_us_census(population=True, level="congressional_district")
    d_names = list(gd["State Name"])
    for group_by in (False, True):
        data = prepare_layout_data(gd, **({"group_by": "State Name"} if group_by else {}))
        for morph in (True, False):
            case = f"districts{'_group_by' if group_by else ''}"
            suffix = f"{case}{'' if morph else '_nomorph'}"
            row = run_case(case, data, d_names, morph, label, outdir, suffix)
            if group_by:
                row["split_groups_measured"] = split_groups(
                    MosaicLayout(morph=morph).compute(data, show_progress=False), d_names
                )
            out.append(row)

    # --- world
    gw = world_gdf()
    w_names = list(gw["name"])
    d_world = prepare_layout_data(gw, tile_count="tiles")
    for morph in (True, False):
        suffix = "world" if morph else "world_nomorph"
        out.append(run_case("world", d_world, w_names, morph, label, outdir, suffix))

    with open(f"{outdir}/stats_{label}.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
