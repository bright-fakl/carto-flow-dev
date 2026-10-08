"""Render mosaic tilings for the chain-swap repair check.

Usage: make_figures.py <label: before|after> <outdir>

Writes <outdir>/<case>_<label>.png and <outdir>/stats_<label>.json.
combine.py merges the two labels into side-by-side figures.
"""

import json
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_hex

import geopandas as gpd
from shapely.geometry import box

import carto_flow.data as cfdata
import carto_flow.symbol_cartogram as smb
from carto_flow.geo_utils import find_adjacent_pairs
from carto_flow.symbol_cartogram.layouts import prepare_layout_data
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

COUNTS_3X3 = [4, 5, 3, 6, 4, 5, 3, 4, 6]


def unique_colors(n):
    cols = []
    for name in ("tab20", "tab20b", "tab20c"):
        cols.extend(to_hex(c) for c in plt.get_cmap(name).colors)
    return [cols[i % len(cols)] for i in range(n)]


def blocks_per_key(tiles_gdf, key_of_geom):
    polys = list(tiles_gdf.geometry)
    adj = {i: set() for i in range(len(polys))}
    for i, j, _ in find_adjacent_pairs(polys):
        adj[i].add(j)
        adj[j].add(i)
    grouped = {}
    for row, gid in enumerate(tiles_gdf["geometry_id"].tolist()):
        grouped.setdefault(key_of_geom[int(gid)], []).append(row)
    blocks = {}
    for k, rows in grouped.items():
        rset = set(rows)
        seen, n = set(), 0
        for s in rows:
            if s in seen:
                continue
            n += 1
            stack = [s]
            while stack:
                u = stack.pop()
                if u in seen:
                    continue
                seen.add(u)
                stack.extend(v for v in adj[u] if v in rset)
        blocks[k] = n
    return grouped, blocks


def draw(ax, tiles_gdf, key_of_geom, key_order, title):
    grouped, blocks = blocks_per_key(tiles_gdf, key_of_geom)
    colors = dict(zip(key_order, unique_colors(len(key_order))))
    tiles = tiles_gdf.copy()
    tiles["key"] = [key_of_geom[int(g)] for g in tiles["geometry_id"]]
    tiles.plot(ax=ax, color=[colors[k] for k in tiles["key"]], edgecolor="white", linewidth=0.3)

    split = sorted(k for k, n in blocks.items() if n > 1)
    for k in split:
        merged = tiles.iloc[grouped[k]].dissolve()
        merged.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.8, hatch="///", zorder=5)
        c = merged.geometry.iloc[0].centroid
        ax.annotate(
            str(k),
            xy=(c.x, c.y),
            ha="center",
            va="center",
            fontsize=7,
            fontweight="bold",
            zorder=6,
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "black", "lw": 0.6, "alpha": 0.85},
        )
    ax.set_title(f"{title}\nsplit: {len(split)} of {len(blocks)}", fontsize=10)
    ax.set_axis_off()
    return split, blocks


def case_states(label, outdir):
    g = cfdata.load_us_census(population=True)
    g["tiles"] = np.maximum(1, np.round(g["Population"] / g["Population"].sum() * 150)).astype(int)
    t0 = time.perf_counter()
    r = smb.create_symbol_cartogram(g, tile_count="tiles", layout="mosaic", show_progress=False)
    wall = time.perf_counter() - t0
    names = list(g["State Name"])
    fig, ax = plt.subplots(figsize=(9, 6))
    split, blocks = draw(ax, r.layout_result.tiles_gdf, names, names, f"US states — {label}")
    fig.tight_layout()
    fig.savefig(f"{outdir}/states_{label}.png", dpi=150)
    plt.close(fig)
    return {"case": "states", "split": split, "n_split": len(split), "wall_s": round(wall, 2)}


def case_districts_group(label, outdir):
    g = cfdata.load_us_census(population=True, level="congressional_district")
    t0 = time.perf_counter()
    r = smb.create_symbol_cartogram(g, group_by="State Name", layout="mosaic", show_progress=False)
    wall = time.perf_counter() - t0
    states = list(g["State Name"])
    order = sorted(set(states))
    fig, ax = plt.subplots(figsize=(9, 6))
    split, blocks = draw(
        ax, r.layout_result.tiles_gdf, states, order, f"Districts, group_by=State Name — {label}"
    )
    fig.tight_layout()
    fig.savefig(f"{outdir}/districts_group_by_{label}.png", dpi=150)
    plt.close(fig)
    return {"case": "districts_group_by", "split": split, "n_split": len(split), "wall_s": round(wall, 2)}




def case_fixture(label, outdir):
    geoms = [box(c, r, c + 1, r + 1) for r in range(3) for c in range(3)]
    gdf = gpd.GeoDataFrame({"tiles": COUNTS_3X3}, geometry=geoms)
    data = prepare_layout_data(gdf, tile_count="tiles")
    t0 = time.perf_counter()
    res = MosaicLayout(morph=False).compute(data, show_progress=False)
    wall = time.perf_counter() - t0
    names = [f"R{i}" for i in range(9)]
    fig, ax = plt.subplots(figsize=(5, 5))
    split, blocks = draw(ax, res.tiles_gdf, names, names, f"3x3 synthetic fixture - {label}")
    fig.tight_layout()
    fig.savefig(f"{outdir}/fixture_{label}.png", dpi=150)
    plt.close(fig)
    return {"case": "fixture", "split": split, "n_split": len(split), "wall_s": round(wall, 2)}


def case_michigan(label, outdir):
    """Zoom on Michigan: legitimately two-part, so closing its split may be an over-correction."""
    g = cfdata.load_us_census(population=True)
    g["tiles"] = np.maximum(1, np.round(g["Population"] / g["Population"].sum() * 150)).astype(int)
    r = smb.create_symbol_cartogram(g, tile_count="tiles", layout="mosaic", show_progress=False)
    names = list(g["State Name"])
    tiles = r.layout_result.tiles_gdf.copy()
    tiles["key"] = [names[int(gid)] for gid in tiles["geometry_id"]]
    mi = tiles[tiles["key"] == "Michigan"]
    nb = tiles[tiles["key"].isin(["Michigan", "Wisconsin", "Indiana", "Ohio", "Illinois", "Minnesota"])]
    fig, ax = plt.subplots(figsize=(6, 6))
    nb.plot(ax=ax, color="#dddddd", edgecolor="white", linewidth=0.4)
    mi.plot(ax=ax, color="#1f77b4", edgecolor="white", linewidth=0.4)
    _, blocks = blocks_per_key(tiles, names)
    ax.set_title(f"Michigan ({blocks['Michigan']} block(s)) - {label}\nreal geography: 2 parts, 70.9% / 28.3%", fontsize=9)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(f"{outdir}/michigan_{label}.png", dpi=150)
    plt.close(fig)
    return {"case": "michigan", "blocks": blocks["Michigan"]}


def case_holes(label, outdir):
    """Centre-hole check: unassigned core tiles enclosed by assigned tiles."""
    g = cfdata.load_us_census(population=True)
    g["tiles"] = np.maximum(1, np.round(g["Population"] / g["Population"].sum() * 150)).astype(int)
    r = smb.create_symbol_cartogram(g, tile_count="tiles", layout="mosaic", show_progress=False)
    lr = r.layout_result
    tr = lr.tiling_result
    assigned = {int(t) for t in lr.assignments}
    adjacency = tr.adjacency
    holes = []
    for t in (int(x) for x in lr.core_tile_indices):
        if t in assigned:
            continue
        nbs = np.flatnonzero(adjacency[t])
        if len(nbs) and all(int(x) in assigned for x in nbs):
            holes.append(t)
    fig, ax = plt.subplots(figsize=(9, 6))
    lr.tiles_gdf.plot(ax=ax, color="#cfd8dc", edgecolor="white", linewidth=0.3)
    unassigned = [int(x) for x in lr.core_tile_indices if int(x) not in assigned]
    if unassigned:
        gpd.GeoSeries([tr.polygons[t] for t in unassigned]).plot(
            ax=ax, facecolor="none", edgecolor="#90a4ae", linewidth=0.5
        )
    if holes:
        gpd.GeoSeries([tr.polygons[t] for t in holes]).plot(
            ax=ax, color="crimson", edgecolor="black", linewidth=0.8, zorder=5
        )
    ax.set_title(
        f"Centre-hole check, US states - {label}\nenclosed unassigned core tiles: {len(holes)}"
        f"  (grey outline = unassigned core tiles, {len(unassigned)})",
        fontsize=9,
    )
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(f"{outdir}/holes_{label}.png", dpi=150)
    plt.close(fig)
    return {"case": "holes", "n_holes": len(holes), "n_unassigned_core": len(unassigned)}


if __name__ == "__main__":
    label, outdir = sys.argv[1], sys.argv[2]
    out = [
        case_fixture(label, outdir),
        case_states(label, outdir),
        case_districts_group(label, outdir),
        case_michigan(label, outdir),
        case_holes(label, outdir),
    ]
    with open(f"{outdir}/stats_{label}.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
