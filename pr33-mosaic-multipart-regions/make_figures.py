"""Mosaic multi-part sub-regions: three-way figures and metrics (PR #33).

Variants, selected by the label argument:

  before  main @ 9c664f9 (run with PYTHONPATH pointing at the base source)
  mid     sub-regions only, MOSAIC_HOPS=8 -- the old relocation reach
  after   shipping: sub-regions + ring_swapback_max_hops=16

Configurations: 3x3 fixture, US states, congressional districts, districts +
group_by="State Name", and the world (bundled Natural Earth, Mollweide, tile
count from pop_est) -- each with morph=True and morph=False.

Sub-regions of one geometry belong to the same region and may sit adjacent; the
split exists to remove an impossible contiguity constraint, not to separate
anything visually.  The metrics here are therefore solution-quality metrics:
repair effort, damage to *neighbouring* regions, compactness, holes.

Usage: make_figures.py <label> <outdir>
"""

import json
import os
import sys
import time
import warnings
from collections import deque

warnings.filterwarnings("ignore")

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.colors import to_hex
from shapely.geometry import box

import carto_flow.data as cfdata
from carto_flow.symbol_cartogram.layouts import prepare_layout_data
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

COUNTS_3X3 = [4, 5, 3, 6, 4, 5, 3, 4, 6]
WORLD_CRS = "ESRI:54009"  # Mollweide -- equal-area, so tile areas mean something
WORLD_BUDGET = 600

# MOSAIC_HOPS pins ring_swapback_max_hops so the middle column of the three-way
# table -- sub-regions with the OLD reach of 8 -- comes from this same harness.
_HOPS = os.environ.get("MOSAIC_HOPS")

# Zoom windows are written by the first ("before") run and read by the others,
# so all three panels of a zoom share axis limits exactly.
WINDOWS_PATH = None


# --------------------------------------------------------------------- metrics


def _blocks(tiles, adj):
    todo, out = set(tiles), []
    while todo:
        start = todo.pop()
        comp, queue = {start}, deque([start])
        while queue:
            t = queue.popleft()
            for nb in np.flatnonzero(adj[t]):
                nb = int(nb)
                if nb in todo:
                    todo.discard(nb)
                    comp.add(nb)
                    queue.append(nb)
        out.append(comp)
    return out


def tiles_by_geom(lr):
    out = {}
    for t, g in zip(lr.assignments, lr.tiles_gdf["geometry_id"].tolist()):
        out.setdefault(int(g), []).append(int(t))
    return out


def geom_blocks(lr, g):
    return _blocks(tiles_by_geom(lr).get(g, []), lr.tiling_result.adjacency)


def split_counts(lr, key_of_geom=None):
    """(split units by geometry, split units by group), measured from the tiles."""
    adj = lr.tiling_result.adjacency
    by_geom = tiles_by_geom(lr)
    n_geom_split = sum(1 for tl in by_geom.values() if len(_blocks(tl, adj)) > 1)
    n_group_split = 0
    if key_of_geom is not None:
        by_group = {}
        for g, tl in by_geom.items():
            by_group.setdefault(key_of_geom[g], []).extend(tl)
        n_group_split = sum(1 for tl in by_group.values() if len(_blocks(tl, adj)) > 1)
    return n_geom_split, n_group_split


def single_part_splits(lr, multipart_geoms):
    """Split regions that are NOT multi-part -- i.e. collateral damage.

    This is the number that matters for solution quality: a multi-part region in
    two blocks is correct, a *single-part* neighbour in two blocks is the solver
    reaching across an impossible gap and shredding whatever was in the way.
    """
    adj = lr.tiling_result.adjacency
    return sum(
        1 for g, tl in tiles_by_geom(lr).items() if g not in multipart_geoms and len(_blocks(tl, adj)) > 1
    )


def hole_state(lr):
    tr = lr.tiling_result
    core = {int(x) for x in lr.core_tile_indices}
    assigned = {int(t) for t in lr.assignments}
    enclosed = []
    for t in range(len(tr.polygons)):
        if t in assigned:
            continue
        nbs = np.flatnonzero(tr.adjacency[t])
        if len(nbs) and all(int(x) in assigned for x in nbs):
            enclosed.append(t)
    return {"ring_used": sorted(assigned - core), "empty_core": sorted(core - assigned), "enclosed": enclosed}


def compactness(lr, key_of_geom):
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


def multipart_geom_indices(geoms, counts, frac=0.1):
    """Geometries with a second part of at least *frac* of their area and >1 tile.

    Input-side only -- independent of any layout run, so it labels the same
    geometries in all three variants.
    """
    out = set()
    for i, geom in enumerate(geoms):
        if int(counts[i]) < 2:
            continue
        parts = sorted((p.area for p in shapely.get_parts(geom)), reverse=True)
        if len(parts) > 1 and parts[1] >= frac * sum(parts):
            out.add(i)
    return out


def summarise(case, lr, names, wall, counts, multipart, group_key=None):
    st = hole_state(lr)
    m = lr.metrics.algorithm
    pp = compactness(lr, names)
    by_geom_split, by_group_split = split_counts(lr, group_key)
    tiles = tiles_by_geom(lr)
    tile_counts = np.array([len(tiles.get(g, [])) for g in range(len(names))])
    return {
        "case": case,
        "converged": bool(lr.metrics.converged),
        "n_subregions": getattr(m, "n_subregions", len(names)),
        "n_split_geometries": getattr(m, "n_split_geometries", 0),
        "split_by_geometry": by_geom_split,
        "split_by_subregion": m.n_noncontiguous_regions,
        "split_single_part": single_part_splits(lr, multipart),
        "split_groups_measured": by_group_split,
        "repair_passes": m.repair_passes,
        "ring_used": len(st["ring_used"]),
        "empty_core": len(st["empty_core"]),
        "enclosed": len(st["enclosed"]),
        "regions_correct": f"{m.regions_correct}/{m.regions_total}",
        "total_tiles": int(tile_counts.sum()),
        "target_tiles": int(np.sum(counts)),
        "counts_exact": bool(np.array_equal(tile_counts, np.asarray(counts))),
        "pp_min": round(min(pp.values()), 4) if pp else None,
        "pp_mean": round(float(np.mean(list(pp.values()))), 4) if pp else None,
        "wall_s": round(wall, 2),
    }


# ----------------------------------------------------------------------- draw


def unique_colors(n):
    cols = []
    for name in ("tab20", "tab20b", "tab20c"):
        cols.extend(to_hex(c) for c in plt.get_cmap(name).colors)
    return [cols[i % len(cols)] for i in range(n)]


def draw_map(ax, lr, key_of_geom, title, highlight=None):
    tiles = lr.tiles_gdf.copy()
    tiles["key"] = [key_of_geom[int(g)] for g in tiles["geometry_id"]]
    order = sorted(set(tiles["key"]))
    colors = dict(zip(order, unique_colors(len(order))))
    tiles.plot(ax=ax, color=[colors[k] for k in tiles["key"]], edgecolor="white", linewidth=0.3)
    if highlight is not None:
        sel = tiles[tiles["geometry_id"] == highlight]
        sel.plot(ax=ax, facecolor="#d81b60", edgecolor="black", linewidth=1.0, zorder=5)
    ax.set_title(title, fontsize=9)
    ax.set_axis_off()


def draw_defects(ax, lr):
    """Orange = ring tiles used, red = empty core tiles, blue hatch = enclosed cells."""
    tr = lr.tiling_result
    st = hole_state(lr)
    for key, fc, hatch in (
        ("ring_used", "#fb8c00", None),
        ("empty_core", "#e53935", None),
        ("enclosed", "#1e88e5", "//"),
    ):
        if st[key]:
            gpd.GeoSeries([tr.polygons[t] for t in st[key]]).plot(
                ax=ax, facecolor=fc, edgecolor="black", linewidth=1.2, alpha=0.9, hatch=hatch, zorder=7
            )
    return st


def zoom_window(lr, gidx, key, margin=1.8):
    """Axis limits around a region's tiles, shared across variants via JSON."""
    store = {}
    if WINDOWS_PATH and os.path.exists(WINDOWS_PATH):
        store = json.load(open(WINDOWS_PATH))
    if key in store:
        return tuple(store[key][0]), tuple(store[key][1])
    ts = tiles_by_geom(lr).get(gidx, [])
    if not ts:
        b = tuple(lr.tiles_gdf.total_bounds)
    else:
        arr = np.array([lr.tiling_result.polygons[t].bounds for t in ts])
        b = (arr[:, 0].min(), arr[:, 1].min(), arr[:, 2].max(), arr[:, 3].max())
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    half = max(b[2] - b[0], b[3] - b[1]) * margin / 2
    win = ((cx - half, cx + half), (cy - half, cy + half))
    store[key] = [list(win[0]), list(win[1])]
    if WINDOWS_PATH:
        json.dump(store, open(WINDOWS_PATH, "w"))
    return win


def draw_zoom(ax, lr, key_of_geom, gidx, name, label, key, geoms=None):
    xlim, ylim = zoom_window(lr, gidx, key)
    draw_map(ax, lr, key_of_geom, "", highlight=gidx)
    if geoms is not None:
        gpd.GeoSeries([geoms[gidx]]).boundary.plot(ax=ax, color="black", linewidth=1.0, zorder=6)
    st = draw_defects(ax, lr)

    def in_view(ts):
        return sum(
            1
            for t in ts
            if xlim[0] < lr.tiling_result.polygons[t].centroid.x < xlim[1]
            and ylim[0] < lr.tiling_result.polygons[t].centroid.y < ylim[1]
        )

    blocks = geom_blocks(lr, gidx)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_title(
        f"{name} -- {label}\npink = {name}'s tiles: {sum(len(b) for b in blocks)} tile(s) "
        f"in {len(blocks)} block(s)\n"
        f"in view: {in_view(st['ring_used'])} ring, {in_view(st['empty_core'])} empty core, "
        f"{in_view(st['enclosed'])} enclosed",
        fontsize=9,
    )
    ax.set_axis_off()


# ---------------------------------------------------------------------- cases


def _run(data, morph):
    kwargs = {}
    if _HOPS:
        from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions

        kwargs["hungarian_options"] = HungarianOptions(ring_swapback_max_hops=int(_HOPS))
    t0 = time.perf_counter()
    lr = MosaicLayout(morph=morph, **kwargs).compute(data, show_progress=False)
    return lr, time.perf_counter() - t0


def world_gdf():
    g = cfdata.load_world()
    g = g[(g["name"] != "Antarctica") & (g["pop_est"] > 0)].copy().to_crs(WORLD_CRS)
    pop = g["pop_est"].to_numpy(dtype=float)
    g["tiles"] = np.maximum(1, np.round(pop / pop.sum() * WORLD_BUDGET)).astype(int)
    return g.reset_index(drop=True)


def neighbour_distortion_figure(outdir):
    """Headline: what the impossible constraint costs the region's NEIGHBOURS.

    Same input, same code, only ``multipart_min_tiles`` differs.  Forced to make
    its two parts one block, the multi-part region reaches across the gap and
    breaks the single-part region beside it into several blocks.
    """
    from shapely.geometry import MultiPolygon

    geoms = [box(0.0, 0.0, 4.0, 4.0), MultiPolygon([box(4.0, 0.0, 8.0, 4.0), box(14.0, 0.0, 18.0, 4.0)])]
    gdf = gpd.GeoDataFrame({"tiles": [16, 16]}, geometry=geoms)
    data = prepare_layout_data(gdf, tile_count="tiles")
    names = ["A (single part)", "B (two parts)"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    out = {}
    for ax, (title, thr) in zip(axes, (("forced into one block (before)", 1e9), ("sub-regions (after)", 0.5))):
        lr = MosaicLayout(morph=False, multipart_min_tiles=thr).compute(data, show_progress=False)
        draw_map(ax, lr, names, "")
        gpd.GeoSeries(geoms).boundary.plot(ax=ax, color="black", linewidth=1.0, zorder=6)
        a_blocks, b_blocks = len(geom_blocks(lr, 0)), len(geom_blocks(lr, 1))
        ax.set_title(
            f"{title}\nA (the neighbour) in {a_blocks} block(s);  B in {b_blocks} block(s)\n"
            f"split regions reported: {lr.metrics.algorithm.n_noncontiguous_regions};  "
            f"converged: {lr.metrics.converged}",
            fontsize=10,
        )
        out[title] = {
            "neighbour_blocks": a_blocks,
            "multipart_blocks": b_blocks,
            "converged": bool(lr.metrics.converged),
        }
    fig.suptitle(
        "What the impossible constraint costs the NEIGHBOUR (same input, same code, threshold only)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(f"{outdir}/neighbour_distortion.png", dpi=150)
    plt.close(fig)
    return out


def main(label, outdir):
    global WINDOWS_PATH
    WINDOWS_PATH = f"{outdir}/zoom_windows.json"
    out = []

    # --- 3x3 fixture
    geoms, counts = [], []
    for r in range(3):
        for c in range(3):
            geoms.append(box(c, r, c + 1, r + 1))
            counts.append(COUNTS_3X3[r * 3 + c])
    fx = gpd.GeoDataFrame({"tiles": counts}, geometry=geoms)
    d_fx = prepare_layout_data(fx, tile_count="tiles")
    fx_names = [f"R{i}" for i in range(9)]
    for morph in (True, False):
        lr, wall = _run(d_fx, morph)
        out.append(summarise(f"fixture/morph={morph}", lr, fx_names, wall, counts, set()))
        if morph:
            fig, ax = plt.subplots(figsize=(5, 5))
            draw_map(ax, lr, fx_names, f"3x3 fixture, morph=True -- {label}")
            fig.tight_layout()
            fig.savefig(f"{outdir}/fixture_{label}.png", dpi=150)
            plt.close(fig)

    # --- US states
    g = cfdata.load_us_census(population=True)
    g["tiles"] = np.maximum(1, np.round(g["Population"] / g["Population"].sum() * 150)).astype(int)
    d_states = prepare_layout_data(g, tile_count="tiles")
    st_names = list(g["State Name"])
    st_counts = g["tiles"].to_numpy()
    st_geoms = list(g.geometry)
    st_multi = multipart_geom_indices(st_geoms, st_counts)
    mi, ri = st_names.index("Michigan"), st_names.index("Rhode Island")
    for morph in (True, False):
        lr, wall = _run(d_states, morph)
        suffix = "" if morph else "_nomorph"
        row = summarise(f"states/morph={morph}", lr, st_names, wall, st_counts, st_multi)
        row["michigan_blocks"] = len(geom_blocks(lr, mi))
        row["rhode_island_tiles"] = len(tiles_by_geom(lr).get(ri, []))
        out.append(row)

        fig, ax = plt.subplots(figsize=(9, 6))
        draw_map(ax, lr, st_names, "", highlight=mi)
        hs = draw_defects(ax, lr)
        ax.set_title(
            f"US states, morph={morph} -- {label}\npink = Michigan;  orange = ring tiles "
            f"({len(hs['ring_used'])}),  red = empty core ({len(hs['empty_core'])}),  "
            f"blue hatch = enclosed ({len(hs['enclosed'])})",
            fontsize=9,
        )
        fig.tight_layout()
        fig.savefig(f"{outdir}/states{suffix}_{label}.png", dpi=150)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6.5, 6))
        draw_zoom(ax, lr, st_names, mi, "Michigan", f"{label} (morph={morph})", f"michigan{suffix}", st_geoms)
        fig.tight_layout()
        fig.savefig(f"{outdir}/michigan{suffix}_{label}.png", dpi=150)
        plt.close(fig)

        if morph:
            fig, ax = plt.subplots(figsize=(6.5, 6))
            draw_zoom(ax, lr, st_names, ri, "Rhode Island", f"{label} (morph=True)", "rhodeisland", st_geoms)
            fig.tight_layout()
            fig.savefig(f"{outdir}/rhodeisland_{label}.png", dpi=150)
            plt.close(fig)

    # --- congressional districts, with and without group_by
    gd = cfdata.load_us_census(population=True, level="congressional_district")
    d_names = list(gd["State Name"])
    ones = np.ones(len(gd), dtype=int)
    for group_by in (False, True):
        data = prepare_layout_data(gd, **({"group_by": "State Name"} if group_by else {}))
        for morph in (True, False):
            lr, wall = _run(data, morph)
            case = f"districts{'_group_by' if group_by else ''}/morph={morph}"
            out.append(summarise(case, lr, d_names, wall, ones, set(), d_names if group_by else None))
            if group_by:
                name = "districts_group_by" if morph else "nomorph"
                fig, ax = plt.subplots(figsize=(9, 6))
                draw_map(ax, lr, d_names, f"Districts grouped by state, morph={morph} -- {label}")
                fig.tight_layout()
                fig.savefig(f"{outdir}/{name}_{label}.png", dpi=150)
                plt.close(fig)

    # --- world: the regime this feature actually targets
    gw = world_gdf()
    w_names = list(gw["name"])
    w_counts = gw["tiles"].to_numpy()
    w_geoms = list(gw.geometry)
    w_multi = multipart_geom_indices(w_geoms, w_counts)
    d_world = prepare_layout_data(gw, tile_count="tiles")
    zooms = [(n, w_names.index(n)) for n in ("Malaysia", "Indonesia", "New Zealand") if n in w_names]
    for morph in (True, False):
        lr, wall = _run(d_world, morph)
        suffix = "" if morph else "_nomorph"
        row = summarise(f"world/morph={morph}", lr, w_names, wall, w_counts, w_multi)
        for nm, idx in zooms:
            slug = nm.lower().replace(" ", "_")
            row[f"{slug}_blocks"] = len(geom_blocks(lr, idx))
            row[f"{slug}_tiles"] = len(tiles_by_geom(lr).get(idx, []))
        out.append(row)

        fig, ax = plt.subplots(figsize=(12, 6))
        draw_map(ax, lr, w_names, "", highlight=w_names.index("Indonesia"))
        hs = draw_defects(ax, lr)
        ax.set_title(
            f"World (Mollweide, {int(w_counts.sum())} tiles), morph={morph} -- {label}\n"
            f"pink = Indonesia;  orange = ring tiles ({len(hs['ring_used'])}),  "
            f"red = empty core ({len(hs['empty_core'])}),  blue hatch = enclosed ({len(hs['enclosed'])})",
            fontsize=9,
        )
        fig.tight_layout()
        fig.savefig(f"{outdir}/world{suffix}_{label}.png", dpi=150)
        plt.close(fig)

        for nm, idx in zooms:
            slug = nm.lower().replace(" ", "")
            fig, ax = plt.subplots(figsize=(6.5, 6))
            draw_zoom(ax, lr, w_names, idx, nm, f"{label} (morph={morph})", f"{slug}{suffix}", w_geoms)
            fig.tight_layout()
            fig.savefig(f"{outdir}/{slug}{suffix}_{label}.png", dpi=150)
            plt.close(fig)

    if label == "after":
        nd = neighbour_distortion_figure(outdir)
        with open(f"{outdir}/neighbour_distortion.json", "w") as fh:
            json.dump(nd, fh, indent=2)

    with open(f"{outdir}/stats_{label}.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
