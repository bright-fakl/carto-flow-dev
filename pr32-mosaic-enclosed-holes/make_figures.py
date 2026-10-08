"""Render mosaic tilings for the enclosed-hole check (PR #32).

Extends the PR #31 harness with a third marker: enclosed unassigned cells that
are NOT core tiles -- the blind spot both earlier metrics had -- and with a
morph=False case and a donut fixture that has a genuine inner sea.

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
from matplotlib.colors import to_hex
from shapely.geometry import box
from shapely.ops import unary_union

import carto_flow.data as cfdata
from carto_flow.symbol_cartogram.layouts import prepare_layout_data
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

COUNTS_3X3 = [4, 5, 3, 6, 4, 5, 3, 4, 6]

# Same view as the pr31 figure, so the two checks can be read against each other.
NORTHEAST_XLIM = (1.35e6, 2.15e6)
NORTHEAST_YLIM = (8.0e5, 1.60e6)


# --------------------------------------------------------------------------- state


def hole_state(lr):
    """Ring tiles used, empty core tiles, and enclosed unassigned cells by kind.

    The third bucket is the point of this PR: an enclosed cell that is not a core
    tile is invisible to both `n_unassigned_core_tiles` and PR #30's hole check.
    """
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
    return {
        "ring_used": ring_used,
        "empty_core": empty_core,
        "enclosed_core": [t for t in enclosed if t in core],
        "enclosed_noncore": [t for t in enclosed if t not in core],
    }


def unique_colors(n):
    cols = []
    for name in ("tab20", "tab20b", "tab20c"):
        cols.extend(to_hex(c) for c in plt.get_cmap(name).colors)
    return [cols[i % len(cols)] for i in range(n)]


def draw_holes(ax, lr, names, st, annotate=True):
    """Grey footprint; orange = ring tiles, red = empty core, blue = enclosed non-core."""
    tr = lr.tiling_result
    lr.tiles_gdf.plot(ax=ax, color="#cfd8dc", edgecolor="white", linewidth=0.3)

    owner = {int(t): names[int(g)] for t, g in zip(lr.assignments, lr.tiles_gdf["geometry_id"].tolist())}

    if st["empty_core"]:
        gpd.GeoSeries([tr.polygons[t] for t in st["empty_core"]]).plot(
            ax=ax, facecolor="#e53935", edgecolor="black", linewidth=1.0, alpha=0.85, zorder=5
        )
    if st["enclosed_core"]:
        gpd.GeoSeries([tr.polygons[t] for t in st["enclosed_core"]]).plot(
            ax=ax, facecolor="none", edgecolor="black", linewidth=2.0, hatch="xx", zorder=6
        )
    # The new marker.  Drawn last and largest so it cannot be mistaken for the others.
    if st["enclosed_noncore"]:
        gpd.GeoSeries([tr.polygons[t] for t in st["enclosed_noncore"]]).plot(
            ax=ax, facecolor="#1e88e5", edgecolor="black", linewidth=2.2, hatch="//", zorder=8
        )
    if st["ring_used"]:
        gpd.GeoSeries([tr.polygons[t] for t in st["ring_used"]]).plot(
            ax=ax, facecolor="#fb8c00", edgecolor="black", linewidth=1.0, alpha=0.95, zorder=5
        )
    if annotate:
        for t in st["ring_used"]:
            c = tr.polygons[t].centroid
            ax.annotate(
                owner.get(t, "?"),
                xy=(c.x, c.y),
                xytext=(0, -16),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                fontweight="bold",
                zorder=9,
                bbox={"boxstyle": "round,pad=0.15", "fc": "#fb8c00", "ec": "black", "lw": 0.5, "alpha": 0.9},
            )
    for t in st["enclosed_noncore"]:
        c = tr.polygons[t].centroid
        ax.annotate(
            "enclosed\nnon-core",
            xy=(c.x, c.y),
            xytext=(0, 26),
            textcoords="offset points",
            ha="center",
            fontsize=7,
            fontweight="bold",
            color="white",
            zorder=10,
            bbox={"boxstyle": "round,pad=0.2", "fc": "#1e88e5", "ec": "black", "lw": 0.6},
            arrowprops={"arrowstyle": "->", "color": "#1e88e5", "lw": 1.4},
        )
    ax.set_axis_off()


def title_for(prefix, st):
    return (
        f"{prefix}\norange = ring tiles used ({len(st['ring_used'])}),  "
        f"red = empty core ({len(st['empty_core'])}),  "
        f"x-hatch = enclosed core ({len(st['enclosed_core'])}),  "
        f"blue = ENCLOSED NON-CORE ({len(st['enclosed_noncore'])})"
    )


# --------------------------------------------------------------------------- groups


def draw_groups(ax, lr, key_of_geom, title):
    tiles = lr.tiles_gdf.copy()
    tiles["key"] = [key_of_geom[int(g)] for g in tiles["geometry_id"]]
    order = sorted(set(tiles["key"]))
    colors = dict(zip(order, unique_colors(len(order))))
    tiles.plot(ax=ax, color=[colors[k] for k in tiles["key"]], edgecolor="white", linewidth=0.3)
    ax.set_title(title, fontsize=10)
    ax.set_axis_off()


def compactness(lr, key_of_geom):
    """Discrete Polsby-Popper on the tile adjacency graph (see summary.md)."""
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


def summarise(name, lr, names, wall):
    st = hole_state(lr)
    m = lr.metrics.algorithm
    pp = compactness(lr, names)
    return {
        "case": name,
        "ring_used": len(st["ring_used"]),
        "empty_core": len(st["empty_core"]),
        "enclosed_core": len(st["enclosed_core"]),
        "enclosed_noncore": len(st["enclosed_noncore"]),
        "metric_n_enclosed_unassigned_tiles": getattr(m, "n_enclosed_unassigned_tiles", None),
        "metric_n_unassigned_core_tiles": m.n_unassigned_core_tiles,
        "split_regions": m.n_noncontiguous_regions,
        "split_groups": m.n_split_groups,
        "regions_correct": f"{m.regions_correct}/{m.regions_total}",
        "pp_min": round(min(pp.values()), 4) if pp else None,
        "pp_mean": round(float(np.mean(list(pp.values()))), 4) if pp else None,
        "wall_s": round(wall, 2),
    }


# --------------------------------------------------------------------------- cases


def _districts(group_by, morph):
    g = cfdata.load_us_census(population=True, level="congressional_district")
    data = prepare_layout_data(g, **({"group_by": "State Name"} if group_by else {}))
    t0 = time.perf_counter()
    lr = MosaicLayout(morph=morph).compute(data, show_progress=False)
    return lr, time.perf_counter() - t0, list(g["State Name"])


def case_northeast(label, outdir):
    """The hole the user spotted: districts + group_by, north-east corner."""
    lr, wall, names = _districts(True, True)
    st = hole_state(lr)

    fig, ax = plt.subplots(figsize=(9, 6))
    draw_holes(ax, lr, names, st)
    ax.set_title(title_for(f"Districts + group_by, morph=True -- {label}", st), fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{outdir}/districts_group_by_{label}.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 6))
    draw_holes(ax, lr, names, st)
    ax.set_xlim(*NORTHEAST_XLIM)
    ax.set_ylim(*NORTHEAST_YLIM)
    n_local = sum(1 for t in st["enclosed_noncore"] if NORTHEAST_XLIM[0] < lr.tiling_result.polygons[t].centroid.x < NORTHEAST_XLIM[1])
    ax.set_title(f"North-east zoom -- {label}\nenclosed non-core cells in view: {n_local}", fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{outdir}/northeast_{label}.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 6))
    draw_groups(ax, lr, names, f"Districts grouped by state -- {label}")
    fig.tight_layout()
    fig.savefig(f"{outdir}/groups_{label}.png", dpi=150)
    plt.close(fig)
    return summarise("districts_group_by/morph=True", lr, names, wall)


def case_nomorph(label, outdir):
    """morph=False: the harder case for the assignment, never measured before."""
    lr, wall, names = _districts(True, False)
    st = hole_state(lr)
    fig, ax = plt.subplots(figsize=(9, 6))
    draw_holes(ax, lr, names, st)
    ax.set_title(title_for(f"Districts + group_by, morph=FALSE -- {label}", st), fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{outdir}/nomorph_{label}.png", dpi=150)
    plt.close(fig)
    return summarise("districts_group_by/morph=False", lr, names, wall)


def case_states(label, outdir):
    g = cfdata.load_us_census(population=True)
    g["tiles"] = np.maximum(1, np.round(g["Population"] / g["Population"].sum() * 150)).astype(int)
    data = prepare_layout_data(g, tile_count="tiles")
    t0 = time.perf_counter()
    lr = MosaicLayout(morph=True).compute(data, show_progress=False)
    wall = time.perf_counter() - t0
    names = list(g["State Name"])
    st = hole_state(lr)
    fig, ax = plt.subplots(figsize=(9, 6))
    draw_holes(ax, lr, names, st)
    ax.set_title(title_for(f"US states -- {label}", st), fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{outdir}/states_{label}.png", dpi=150)
    plt.close(fig)
    return summarise("states/morph=True", lr, names, wall)


def case_donut(label, outdir):
    """Characterisation, not a fix: mosaic paves over a genuine inner sea.

    Nothing in this PR changes that.  The cause is upstream -- calibration admits
    cells sitting in the hole to the core tile budget, because `min_overlap_frac`
    (0.1) is a pool-admission knob, not a land/water classifier.  The panel is here
    so the queued calibration-level issue has a picture to point at.
    """
    geoms, counts = [], []
    for r in range(4):
        for c in range(4):
            if r in (1, 2) and c in (1, 2):
                continue
            geoms.append(box(c, r, c + 1, r + 1))
            counts.append(4)
    gdf = gpd.GeoDataFrame({"tiles": counts}, geometry=geoms)
    data = prepare_layout_data(gdf, tile_count="tiles")
    t0 = time.perf_counter()
    lr = MosaicLayout(morph=False).compute(data, show_progress=False)
    wall = time.perf_counter() - t0
    names = [f"R{i}" for i in range(len(geoms))]
    st = hole_state(lr)

    from shapely.geometry import Polygon

    union = unary_union(list(gdf.geometry))
    polys = [union] if union.geom_type == "Polygon" else list(union.geoms)
    rings = [Polygon(r) for p in polys if p.geom_type == "Polygon" for r in p.interiors]
    water = unary_union(rings).difference(union) if rings else None

    tr = lr.tiling_result
    core = {int(x) for x in lr.core_tile_indices}
    assigned = {int(t) for t in lr.assignments}
    wet = {
        t for t, poly in enumerate(tr.polygons) if water is not None and poly.intersection(water).area > 0.5 * poly.area
    }

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    draw_holes(ax, lr, names, st, annotate=False)
    if water is not None:
        gpd.GeoSeries([water]).plot(ax=ax, facecolor="#4fc3f7", edgecolor="#0277bd", linewidth=1.4, alpha=0.6, zorder=3)
    if wet & assigned:
        gpd.GeoSeries([tr.polygons[t] for t in sorted(wet & assigned)]).plot(
            ax=ax, facecolor="#8e24aa", edgecolor="black", linewidth=1.2, alpha=0.8, zorder=8
        )
    ax.set_title(
        f"Donut fixture -- genuine inner sea -- {label}\n"
        f"pale blue = the sea;  purple = mostly-water cells the solver occupied "
        f"({len(wet & assigned)} of {len(wet)});  of those cells {len(wet & core)} are CORE tiles\n"
        f"Characterisation of current behaviour -- unchanged by this PR",
        fontsize=8,
    )
    fig.tight_layout()
    fig.savefig(f"{outdir}/donut_{label}.png", dpi=150)
    plt.close(fig)
    out = summarise("donut/morph=False", lr, names, wall)
    out["wet_cells"] = len(wet)
    out["wet_cells_core"] = len(wet & core)
    out["wet_cells_occupied"] = len(wet & assigned)
    return out


if __name__ == "__main__":
    label, outdir = sys.argv[1], sys.argv[2]
    out = [
        case_northeast(label, outdir),
        case_nomorph(label, outdir),
        case_states(label, outdir),
        case_donut(label, outdir),
    ]
    with open(f"{outdir}/stats_{label}.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
