"""Render mosaic tilings for the repair-objective check.

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

import carto_flow.data as cfdata
import carto_flow.symbol_cartogram as smb
from carto_flow.geo_utils import find_adjacent_pairs


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


if __name__ == "__main__":
    label, outdir = sys.argv[1], sys.argv[2]
    out = [case_states(label, outdir), case_districts_group(label, outdir)]
    with open(f"{outdir}/stats_{label}.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
