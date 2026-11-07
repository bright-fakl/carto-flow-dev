"""Compare the grid, mosaic and tiles layouts on four use cases.

Reproduce (from a carto-flow checkout that has the tiles layout, with its environment)::

    uv run python compare.py            # runs everything, writes results.csv, results.json and fig_*.png
    uv run python compare.py states     # one use case

Use cases: states (49 contiguous US states, one tile each), districts (432 congressional
districts grouped by state), europe (38 regions without Russia), africa (51 regions).
All with the hexagon lattice. Each layout builds its own lattice: the mosaic layout calibrates its
tile size so that the tiles overlapping the input match the tile budget, grid and tiles use a tile
with the area of one needed tile; tile sizes (and so displacements in tile steps, pockets and
tile counts of the window) differ slightly between layouts. In the districts case the grid layout
runs on the 49 states with ``tile_count`` (its only grouped path), while mosaic and tiles run on
the 432 districts with ``group_by``; all three are scored per state. Adjacency of the input regions is by shared border length
(``find_bordering_pairs``); for districts the units compared are the states.
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
from matplotlib.patches import Polygon as MplPolygon
from scipy.spatial import cKDTree

from carto_flow.data import load_us_census, load_world
from carto_flow.geo_utils.adjacency import find_bordering_pairs
from carto_flow.symbol_cartogram import GridBasedLayout, MosaicLayout, TileLayout, create_symbol_cartogram

warnings.filterwarnings("ignore")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


# ---------------------------------------------------------------- data
def short_labels(names):
    """Three-letter labels, made unique by taking later letters on a clash."""
    out, used = [], set()
    for name in names:
        letters = [c for c in str(name).upper() if c.isalpha()]
        cand = "".join(letters[:3])
        i = 3
        while cand in used and i < len(letters):
            cand = letters[0] + letters[1] + letters[i]
            i += 1
        used.add(cand)
        out.append(cand)
    return out


def load_case(case):
    """Return dict: gdf (as the layouts get it), labels, unit_of_geom, plain (one tile per region)."""
    if case == "states":
        g = load_us_census(population=True, contiguous_only=True).reset_index(drop=True)
        return dict(gdf=g, unit_of_geom=np.arange(len(g)), labels=list(g["State Abbreviation"]), plain=True)
    if case == "districts":
        d = load_us_census(level="congressional_district", population=True, contiguous_only=True, simplify=1000)
        d = d.reset_index(drop=True)
        st = load_us_census(population=True, contiguous_only=True).reset_index(drop=True)
        st["nd"] = st["State Name"].map(d.groupby("State Name").size()).fillna(1).astype(int)
        code = {n: i for i, n in enumerate(st["State Name"])}
        return dict(
            gdf=d,
            states=st,
            unit_of_geom=d["State Name"].map(code).to_numpy(),
            labels=list(st["State Abbreviation"]),
            plain=False,
        )
    w = load_world()
    if case == "europe":
        g = w[w.continent == "Europe"].to_crs("EPSG:3035")
        g = g[g["name"] != "Russia"].reset_index(drop=True)
        from europe_iso import ISO

        labels = [ISO.get(n, short_labels([n])[0]) for n in g["name"]]
    else:
        g = w[w.continent == "Africa"].to_crs("ESRI:102022").reset_index(drop=True)
        labels = short_labels(g["name"])
    return dict(gdf=g, unit_of_geom=np.arange(len(g)), labels=labels, plain=True)


VARIANTS = {
    "plain": [
        ("grid", "grid", {}),
        ("mosaic", "mosaic", {}),
        ("tiles c=.25", "tiles", dict(compactness=0.25)),
        ("tiles c=1", "tiles", dict(compactness=1.0)),
        ("tiles c=.25 pre-morph", "tiles", dict(compactness=0.25, pre_morph=True)),
        ("tiles c=1 pre-morph", "tiles", dict(compactness=1.0, pre_morph=True)),
        ("tiles c=.25 protect", "tiles", dict(compactness=0.25, protect_contacts=True)),
        ("tiles c=1 protect", "tiles", dict(compactness=1.0, protect_contacts=True)),
    ],
    "districts": [
        ("grid (tile_count)", "grid", {}),
        ("mosaic (group_by)", "mosaic", {}),
        ("tiles c=.25", "tiles", dict(compactness=0.25)),
        ("tiles c=1", "tiles", dict(compactness=1.0)),
        ("tiles c=.25 pre-morph", "tiles", dict(compactness=0.25, pre_morph=True)),
        ("tiles c=1 pre-morph", "tiles", dict(compactness=1.0, pre_morph=True)),
    ],
}


def run_variant(case, data, kind, kw):
    """Run one layout; return unit of each lattice tile (-1 unused), tiling result and runtime."""
    t0 = time.perf_counter()
    if kind == "grid":
        lay = GridBasedLayout(tiling="hexagon")
        if case == "districts":
            r = create_symbol_cartogram(data["states"], tile_count="nd", layout=lay, show_progress=False)
        else:
            r = create_symbol_cartogram(data["gdf"], layout=lay, show_progress=False)
    else:
        lay = MosaicLayout(tiling="hexagon") if kind == "mosaic" else TileLayout(tiling="hexagon", **kw)
        if case == "districts":
            r = create_symbol_cartogram(data["gdf"], group_by="State Name", layout=lay, show_progress=False)
        else:
            r = create_symbol_cartogram(data["gdf"], layout=lay, show_progress=False)
    dt = time.perf_counter() - t0
    lr = r.layout_result
    tr = lr.tiling_result
    centers = np.asarray(tr.centers)
    pos = np.array([t.position for t in lr.transforms])
    tile = cKDTree(centers).query(pos)[1]
    src = lr.source_indices
    geom = np.arange(len(tile)) if src is None else np.asarray(src)
    geom_unit = geom if kind == "grid" else data["unit_of_geom"][geom]  # grid ran on the units (states) directly
    unit_of_tile = np.full(len(centers), -1, dtype=int)
    unit_of_tile[tile] = geom_unit
    return unit_of_tile, tr, dt


# ---------------------------------------------------------------- metrics
def unit_geometries(data):
    gdf = data["gdf"] if data["plain"] else data["states"]
    return list(shapely.make_valid(np.asarray(list(gdf.geometry), dtype=object)))


def metrics(unit_of_tile, tr, geoms, pairs):
    """Displacement in tile steps, touching of true neighbors, false contacts, splits, pockets."""
    centers = np.asarray(tr.centers)
    adj = tr.adjacency.tocsr()
    nbrs = [adj.indices[adj.indptr[t] : adj.indptr[t + 1]].tolist() for t in range(len(centers))]
    d, _ = cKDTree(centers).query(centers, k=2)
    step = float(np.median(d[:, 1]))
    n = len(geoms)
    cents = np.array([g.centroid.coords[0] for g in geoms])
    used = unit_of_tile >= 0
    disp = np.full(n, np.nan)
    split = stray = 0
    for u in range(n):
        tiles = np.flatnonzero(unit_of_tile == u)
        if len(tiles) == 0:
            continue
        disp[u] = np.hypot(*(centers[tiles].mean(0) - cents[u])) / step
        members, seen, sizes = set(tiles.tolist()), set(), []
        for t in tiles:
            if t in seen:
                continue
            seen.add(t)
            stack, size = [t], 1
            while stack:
                x = stack.pop()
                for y in nbrs[x]:
                    if y in members and y not in seen:
                        seen.add(y)
                        stack.append(y)
                        size += 1
            sizes.append(size)
        if len(sizes) > 1:
            split += 1
            stray += len(tiles) - max(sizes)
    touch = set()
    for t in np.flatnonzero(used):
        for u in nbrs[t]:
            if used[u] and unit_of_tile[u] != unit_of_tile[t]:
                touch.add((int(min(unit_of_tile[t], unit_of_tile[u])), int(max(unit_of_tile[t], unit_of_tile[u]))))
    true = {(i, j): w for i, j, w in pairs}
    got = [p for p in true if p in touch]
    plain = len(got) / max(len(true), 1)
    weighted = sum(true[p] for p in got) / max(sum(true.values()), 1e-12)
    has_neighbor = {i for p in true for i in p}
    touched = {i for p in got for i in p}
    k_min = max(len(x) for x in nbrs) // 2 + 1
    pockets = sum(1 for t in np.flatnonzero(~used) if sum(1 for u in nbrs[t] if used[u]) >= k_min)
    return dict(
        disp_mean=float(np.nanmean(disp)),
        disp_max=float(np.nanmax(disp)),
        touch=plain,
        touch_w=weighted,
        false=len(touch - set(true)),
        split=split,
        stray=stray,
        pockets=pockets,
        no_touch=len(has_neighbor - touched),
        missing=int(np.isnan(disp).sum()),
        step=step,
    )


# ---------------------------------------------------------------- figures
def colors(cents):
    lo, hi = cents.min(0), cents.max(0)
    x, y = ((cents - lo) / (hi - lo)).T
    return np.clip(np.c_[0.35 + 0.55 * x, 0.35 + 0.55 * y, 0.35 + 0.55 * (1 - 0.5 * (x + y))], 0, 1)


def draw(ax, unit_of_tile, tr, geoms, labels, title, fontsize):
    """Tiles colored by unit (one fixed color per unit in every panel), unit outlines and labels."""
    cents = np.array([g.centroid.coords[0] for g in geoms])
    col = colors(cents)
    polys = tr.polygons
    used = np.flatnonzero(unit_of_tile >= 0)
    for g in geoms:
        for p in getattr(g, "geoms", [g]):
            ax.plot(*p.exterior.xy, color="0.75", lw=0.4, zorder=0)
    for t in used:
        ax.add_patch(
            MplPolygon(np.asarray(polys[t].exterior.coords), fc=col[unit_of_tile[t]], ec="white", lw=0.3, zorder=1)
        )
    eps = 1e-3 * np.sqrt(polys[0].area)
    for u in np.unique(unit_of_tile[used]):
        tiles = np.flatnonzero(unit_of_tile == u)
        merged = shapely.union_all([polys[t].buffer(eps) for t in tiles]).buffer(-eps)
        for p in getattr(merged, "geoms", [merged]):
            ax.plot(*p.exterior.xy, color="k", lw=0.8, zorder=3)
        c = shapely.union_all([polys[t] for t in tiles]).centroid
        ax.text(c.x, c.y, labels[u], ha="center", va="center", fontsize=fontsize, zorder=4)
    ax.set_title(title, fontsize=8)


def run_case(case):
    data = load_case(case)
    geoms = unit_geometries(data)
    pairs = find_bordering_pairs(geoms)
    variants = VARIANTS["districts" if case == "districts" else "plain"]
    rows, panels = [], []
    for name, kind, kw in variants:
        unit_of_tile, tr, dt = run_variant(case, data, kind, kw)
        m = metrics(unit_of_tile, tr, geoms, pairs)
        m.update(case=case, variant=name, seconds=dt, n_pairs=len(pairs))
        rows.append(m)
        panels.append((name, unit_of_tile, tr, m))
        print(
            f"{case:10s} {name:24s} disp {m['disp_mean']:.2f}/{m['disp_max']:.1f} touch {m['touch']:.2f}/{m['touch_w']:.2f} "
            f"false {m['false']} split {m['split']}/{m['stray']} pockets {m['pockets']} no_touch {m['no_touch']} {dt:.1f}s",
            flush=True,
        )
    cols = 4 if len(panels) > 6 else 3
    nrows = -(-len(panels) // cols)
    fig, axes = plt.subplots(nrows, cols, figsize=(5.6 * cols, 5.2 * nrows))
    axes = np.atleast_1d(axes).ravel()
    boxes = []
    for _, unit_of_tile, tr, _ in panels:
        used = np.flatnonzero(unit_of_tile >= 0)
        boxes.append(shapely.union_all([tr.polygons[t] for t in used]).bounds)
    boxes = np.array(boxes)
    bounds = (boxes[:, 0].min(), boxes[:, 1].min(), boxes[:, 2].max(), boxes[:, 3].max())
    fs = 5.5 if case == "districts" else 6
    for ax, (name, unit_of_tile, tr, m) in zip(axes, panels, strict=False):
        title = (
            f"{name}\ndisp {m['disp_mean']:.2f}/{m['disp_max']:.1f}  touch {m['touch']:.2f}  "
            f"false {m['false']}  split {m['split']}  pockets {m['pockets']}"
        )
        draw(ax, unit_of_tile, tr, geoms, data["labels"], title, fs)
        pad = 0.05 * max(bounds[2] - bounds[0], bounds[3] - bounds[1])
        ax.set_xlim(bounds[0] - pad, bounds[2] + pad)
        ax.set_ylim(bounds[1] - pad, bounds[3] + pad)
        ax.set_aspect("equal")
        ax.axis("off")
    for ax in axes[len(panels) :]:
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(HERE / f"fig_{case}.png", dpi=130)
    plt.close()
    return rows


if __name__ == "__main__":
    cases = sys.argv[1:] or ["states", "districts", "europe", "africa"]
    rows = []
    for case in cases:
        rows += run_case(case)
    suffix = "" if len(cases) == 4 else "_" + "_".join(cases)
    pd.DataFrame(rows).to_csv(HERE / f"results{suffix}.csv", index=False)
    json.dump(rows, open(HERE / f"results{suffix}.json", "w"), indent=1)
