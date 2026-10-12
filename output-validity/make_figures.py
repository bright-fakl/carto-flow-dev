"""Figures and tables for the output validity PR: invalid (self-intersecting) output regions of the flow cartogram, and their repair.

Run from a carto-flow checkout of the PR branch (bundled data only; the counties run when COUNTIES_PARQUET points at a
GeoDataFrame file with total_votes and geometry):
    NUMBA_NUM_THREADS=8 uv run python make_figures.py
"""

from __future__ import annotations

import os
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.geo_utils.validity import invalid_indices, repair_polygons

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
(HERE / "data").mkdir(exist_ok=True)
STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
MINORITIES = data.load_us_census(population=True, race=True, simplify=1000)
MINORITIES["Minorities"] = MINORITIES[["Black or African American", "Asian", "Hispanic or Latino"]].sum(axis=1)
TABLES: list[str] = []


def runs():
    out = [
        ("states, grid 256", STATES, "Population", dict(grid_size=256)),
        ("states, grid 512, 0.2 % / 0.4 %", STATES, "Population", dict(grid_size=512, mean_tol=0.002, max_tol=0.004)),
        ("districts, grid 256", DISTRICTS, "Population", dict(grid_size=256)),
        ("districts, grid 256, 0.5 % / 1 %", DISTRICTS, "Population", dict(grid_size=256, mean_tol=0.005, max_tol=0.01)),
        ("districts, grid 512, 0.5 % / 1 %", DISTRICTS, "Population", dict(grid_size=512, mean_tol=0.005, max_tol=0.01, n_iter=400)),
        ("issue 85: minority population, simplified states, grid 512", MINORITIES, "Minorities", dict(grid_size=512)),
    ]
    path = os.environ.get("COUNTIES_PARQUET")
    if path:
        import geopandas as gpd

        counties = gpd.read_parquet(path)
        out += [
            (f"counties, grid {n}", counties, "total_votes", dict(grid_size=n, area_scale=1e-6, n_iter=300)) for n in (256, 512)
        ]
    return out


def table_runs():
    rows = ["| run | status, iterations | invalid regions | regions with another part count after the repair | area change of the repaired regions: median / max | check + repair time (ms) |", "|---|---|---|---|---|---|"]
    for label, gdf, col, kw in runs():
        r = morph_gdf(gdf, col, options=MorphOptions(show_progress=False, repair_output=False, **kw))
        geoms = list(r.get_geometry())
        t = time.perf_counter()
        invalid = invalid_indices(geoms)
        fixed = repair_polygons(geoms, invalid)
        ms = (time.perf_counter() - t) * 1000
        if len(invalid):
            change = np.array([abs(fixed[i].area / geoms[i].area - 1) for i in invalid]) * 100
            parts = lambda g: len(g.geoms) if hasattr(g, "geoms") else 1  # noqa: E731
            n_parts = sum(parts(fixed[i]) != parts(geoms[i]) for i in invalid)
            rows.append(f"| {label} | {r.status.value}, {r.niterations} | {len(invalid)} of {len(geoms)} | {n_parts} | {np.median(change):.4f} % / {change.max():.3f} % | {ms:.1f} |")
        else:
            rows.append(f"| {label} | {r.status.value}, {r.niterations} | 0 of {len(geoms)} | | | {ms:.1f} |")
        print(rows[-1], flush=True)
    TABLES.append("\n".join(rows))


def maryland():
    """Where the first self-intersection of the issue's map appears, and what the repair does."""
    o = MorphOptions(grid_size=512, snapshot_every=1, show_progress=False, repair_output=False)
    r = morph_gdf(MINORITIES, "Minorities", options=o)
    grid = o.get_grid(o._calculate_bounds_from_geometries(MINORITIES.geometry.values))
    cell = grid.dx
    snaps = [np.asarray(s.geometry.geometry if hasattr(s.geometry, "geometry") else s.geometry) for s in r.snapshots]
    md = int(np.flatnonzero(MINORITIES["State Abbreviation"].values == "MD")[0])
    first = next(k for k, s in enumerate(snaps) if not shapely.is_valid(s[md]))
    bad, prev = snaps[first][md], snaps[first - 1][md]
    reason = shapely.is_valid_reason(bad)
    xy = [float(v) for v in reason.split("[")[1].rstrip("]").split()]
    pt = shapely.Point(*xy)

    def parts(g):
        return list(g.geoms) if hasattr(g, "geoms") else [g]

    pa = min(parts(prev), key=lambda p: p.distance(pt))
    c = np.asarray(pa.exterior.coords)[:-1]
    near = np.flatnonzero(np.hypot(c[:, 0] - pt.x, c[:, 1] - pt.y) < 3 * cell)
    best = min((np.hypot(*(c[i] - c[j])), i, j) for i in near for j in near if j > i + 2 and not (i == 0 and j == len(c) - 1))
    pb = min(parts(bad), key=lambda p: p.distance(pt))
    cb = np.asarray(pb.exterior.coords)[:-1]
    move = np.hypot(*(cb - c).T) / cell if len(cb) == len(c) else None
    fixed = repair_polygons([bad])[0]
    half = 0.12 * cell
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4))
    for ax, title, g in zip(axes, (f"iteration {first - 1} (valid)", f"iteration {first} (first invalid)", "after the repair"), (prev, bad, fixed)):
        for p in parts(g):
            ax.fill(*p.exterior.xy, color="#cfe3f1", ec="tab:blue", lw=1.2)
            for h in p.interiors:
                ax.fill(*h.xy, color="white", ec="tab:blue", lw=1.0)
        ax.plot(*pt.xy, "x", color="tab:red", ms=9)
        ax.set_xlim(pt.x - half, pt.x + half)
        ax.set_ylim(pt.y - half, pt.y + half)
        ax.set_aspect("equal")
        ax.set_title(f"Maryland, {title}", fontsize=9)
    fig.suptitle(f"Window of 0.24 x 0.24 grid cells around the first self-intersection (red cross), grid cell {cell:.0f} m", fontsize=9)
    fig.tight_layout()
    fig.savefig(HERE / "maryland.png", dpi=130)
    TABLES.append(
        f"Maryland (issue 85) is valid up to snapshot {first - 1} and invalid from snapshot {first} of {len(snaps) - 1}. "
        f"At the crossing the closest pair of non-adjacent vertices of the previous iteration is {best[0] / cell:.4f} grid cells apart; "
        + (f"the vertices there move {np.median(move[near]):.4f} cells per iteration (maximum {move[near].max():.4f}). " if move is not None else "")
        + f"The crossing is {pt.distance(pb.exterior) / cell:.3f} cells from the ring of the part it belongs to ({len(pb.exterior.coords)} vertices, {pb.area / cell**2:.0f} cells^2)."
    )


if __name__ == "__main__":
    if os.environ.get("ONLY") != "maryland":
        table_runs()
    maryland()
    if os.environ.get("ONLY") != "maryland":
        (HERE / "data" / "tables.md").write_text("\n\n".join(TABLES) + "\n")
    print("\n\n".join(TABLES))
