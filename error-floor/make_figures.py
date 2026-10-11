"""Figures and tables for the error floor PR: a floor relative to the mean target area against one grid cell.

The one-grid-cell floor of main is reproduced with error_floor = cell area / mean target area, which gives
exactly the same eps on a given grid.

Run from a carto-flow checkout of the PR branch (bundled data only):
    NUMBA_NUM_THREADS=8 uv run python make_figures.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

from carto_flow import data
from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions, morph_gdf

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
(HERE / "data").mkdir(exist_ok=True)
STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
TABLES: list[str] = []


def cell_floor(gdf, grid_size):
    """error_floor that reproduces the one-grid-cell floor of main on this grid."""
    opts = MorphOptions(grid_size=grid_size)
    grid = opts.get_grid(opts._calculate_bounds_from_geometries(gdf.geometry.values))
    return grid.dx * grid.dy / (gdf.geometry.area.sum() / len(gdf))


def true_errors(result, gdf, col="Population"):
    a = shapely.area(np.asarray(result.get_geometry(), dtype=object))
    w = gdf[col].to_numpy(float)
    return np.abs(a / (w / w.sum() * a.sum()) - 1.0) * 100.0


def initial_errors():
    """The issue's table: initial mean error of the original districts on each grid."""
    grids = (128, 256, 512, 1024)
    rows = {}
    TABLES.append("| grid | regions below the one-cell floor (current or target) | one-cell floor (main) | error_floor 1e-3 (new) | no floor |")
    TABLES.append("|---|---|---|---|---|")
    for n in grids:
        cf = cell_floor(DISTRICTS, n)
        errs = {}
        for name, floor in (("cell", cf), ("new", 1e-3), ("none", 0.0)):
            options = MorphOptions(grid_size=n, error_floor=floor, show_progress=False)
            errs[name] = CartogramWorkflow(DISTRICTS, "Population", options=options).original.get_errors().mean_error_pct
        mean_area = DISTRICTS.geometry.area.sum() / len(DISTRICTS)
        w = DISTRICTS["Population"].to_numpy(float)
        target = DISTRICTS.geometry.area.sum() * w / w.sum()
        below = int(((DISTRICTS.geometry.area.to_numpy() < cf * mean_area) | (target < cf * mean_area)).sum())
        rows[n] = errs
        TABLES.append(f"| {n} | {below} of {len(DISTRICTS)} | {errs['cell']:.0f} % | {errs['new']:.0f} % | {errs['none']:.0f} % |")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(grids, [rows[n]["cell"] for n in grids], "o-", color="#d62728", label="one grid cell (main)")
    ax.plot(grids, [rows[n]["new"] for n in grids], "s-", color="#1f77b4", label="error_floor 1e-3 (new)")
    ax.plot(grids, [rows[n]["none"] for n in grids], "--", color="gray", label="no floor")
    ax.set_xscale("log", base=2)
    ax.set_xticks(grids)
    ax.set_xticklabels(grids)
    ax.set_xlabel("grid size")
    ax.set_ylabel("initial mean error % (districts, unmorphed)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "floor_initial.png", dpi=110)
    plt.close(fig)


def histories():
    """Mean error history of single-grid runs on the districts: curves start at the same value only with the new floor."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, (label, floor_of) in zip(axes, [("one grid cell (main)", cell_floor), ("error_floor 1e-3 (new)", lambda g, n: 1e-3)], strict=True):
        for n, color in zip((128, 256, 512), ("#2ca02c", "#ff7f0e", "#9467bd"), strict=True):
            options = MorphOptions(grid_size=n, error_floor=floor_of(DISTRICTS, n), n_iter=400, show_progress=False)
            conv = morph_gdf(DISTRICTS, "Population", options=options).convergence
            ax.semilogy(np.arange(1, len(conv.mean_errors_pct) + 1), conv.mean_errors_pct, color=color, label=f"grid {n}")
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("iteration")
    axes[0].set_ylabel("reported mean error %")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(HERE / "floor_histories.png", dpi=110)
    plt.close(fig)


def convergence_table():
    TABLES.append("")
    TABLES.append("| input | grid | floor | status | iterations | reported mean % | reported max % | true max % | seconds |")
    TABLES.append("|---|---|---|---|---|---|---|---|---|")
    import time

    for name, gdf, grid in (("states", STATES, 128), ("states", STATES, 256), ("states", STATES, 512), ("districts", DISTRICTS, 256), ("districts", DISTRICTS, 512)):
        for label, floor in (("one cell (main)", cell_floor(gdf, grid)), ("1e-3 (new)", 1e-3)):
            options = MorphOptions(grid_size=grid, error_floor=floor, n_iter=600, show_progress=False)
            t = time.perf_counter()
            result = morph_gdf(gdf, "Population", options=options)
            secs = time.perf_counter() - t
            errs = result.get_errors()
            TABLES.append(
                f"| {name} | {grid} | {label} | {result.status.value} | {result.niterations} | {errs.mean_error_pct:.2f} | {errs.max_error_pct:.2f} | "
                f"{true_errors(result, gdf).max():.2f} | {secs:.1f} |"
            )


def counties_table():
    """Counties are not bundled: set COUNTIES_PARQUET to a GeoDataFrame file with GEOID, total_votes and geometry."""
    import os

    path = os.environ.get("COUNTIES_PARQUET")
    if not path:
        return
    import geopandas as gpd

    gdf = gpd.read_parquet(path)
    TABLES.append("")
    TABLES.append(f"Counties ({len(gdf)}, total votes, area_scale 1e-6, 300 iterations):")
    TABLES.append("")
    TABLES.append("| grid | floor | initial mean error % | status | iterations | reported mean % | reported max % | true mean % | true max % |")
    TABLES.append("|---|---|---|---|---|---|---|---|---|")
    for grid in (256, 512):
        for label, floor in (("one cell (main)", cell_floor(gdf, grid)), ("1e-3 (new)", 1e-3), ("1e-4", 1e-4), ("0", 0.0)):
            options = MorphOptions(grid_size=grid, error_floor=floor, n_iter=300, area_scale=1e-6, show_progress=False)
            initial = CartogramWorkflow(gdf, "total_votes", options=options).original.get_errors().mean_error_pct
            result = morph_gdf(gdf, "total_votes", options=options)
            errs = result.get_errors()
            true = true_errors(result, gdf, "total_votes")
            TABLES.append(
                f"| {grid} | {label} | {initial:.1f} | {result.status.value} | {result.niterations} | {errs.mean_error_pct:.2f} | "
                f"{errs.max_error_pct:.1f} | {true.mean():.1f} | {true.max():.1f} |"
            )


if __name__ == "__main__":
    initial_errors()
    histories()
    convergence_table()
    counties_table()
    (HERE / "data" / "tables.md").write_text("\n".join(TABLES) + "\n")
