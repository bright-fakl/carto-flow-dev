"""Figures and tables for the exact density coverage PR: center sampling against exact coverage.

Run from a carto-flow checkout of the PR branch (bundled data only):
    NUMBA_NUM_THREADS=8 uv run python make_figures.py
Writes the PNGs next to this file and data/tables.md.
"""

from __future__ import annotations

import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import shapely

from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf, multiresolution_morph
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries
from carto_flow.flow_cartogram.grid import Grid

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
(HERE / "data").mkdir(exist_ok=True)
STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
TABLES: list[str] = []
MODES = ("center", "exact")
COLORS = {"center": "#d62728", "exact": "#1f77b4"}


def score(result):
    o = result.options
    conv = result.convergence
    return np.maximum(conv.mean_log_errors / np.log2(1 + o.mean_tol), conv.max_log_errors / np.log2(1 + o.max_tol))


def true_errors(result, gdf, col):
    a = shapely.area(np.asarray(result.get_geometry(), dtype=object))
    w = gdf[col].to_numpy(float)
    return (a / (w / w.sum() * a.sum()) - 1.0) * 100.0


def run(gdf, col, grid, mode, n_iter=400, **kw):
    options = MorphOptions(show_progress=False, grid_size=grid, n_iter=n_iter, density_rasterization=mode, **kw)
    t = time.perf_counter()
    result = morph_gdf(gdf, col, options=options)
    return result, time.perf_counter() - t


def fig_density():
    """Density near DC and Delaware at grids 128 and 256: center against exact."""
    geoms = list(STATES.geometry)
    values = STATES["Population"].to_numpy(float)
    ab = list(STATES["State Abbreviation"])
    xmin, ymin, xmax, ymax = STATES.total_bounds
    box_ = shapely.box(*STATES.geometry[ab.index("DC")].buffer(2.2e5).bounds)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2))
    for row, n in enumerate((128, 256)):
        grid = Grid(tuple(STATES.total_bounds), size=n, margin=0.5)
        fields = {
            m: compute_density_field_from_geometries(geoms, values, grid, None, rasterization=m) for m in MODES
        }
        sel = (grid.X >= box_.bounds[0]) & (grid.X <= box_.bounds[2]) & (grid.Y >= box_.bounds[1]) & (grid.Y <= box_.bounds[3])
        rows, cols = np.where(sel.any(axis=1))[0], np.where(sel.any(axis=0))[0]
        sl = np.s_[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]
        ext = [grid.x_edges[cols.min()], grid.x_edges[cols.max() + 1], grid.y_edges[rows.min()], grid.y_edges[rows.max() + 1]]
        vmax = np.percentile(np.log10(fields["exact"][sl] + 1e-9), 99.5)
        for col, m in enumerate(MODES):
            ax = axes[row, col]
            ax.imshow(np.log10(fields[m][sl] + 1e-9), origin="lower", extent=ext, vmin=vmax - 2.5, vmax=vmax, cmap="viridis")
            gpd.GeoSeries(geoms).boundary.plot(ax=ax, color="white", linewidth=0.5)
            ax.set_xlim(ext[0], ext[1])
            ax.set_ylim(ext[2], ext[3])
            ax.set_title(f"grid {n}, {m}: log10 density", fontsize=9)
            ax.set_axis_off()
        diff = fields["exact"][sl] - fields["center"][sl]
        ax = axes[row, 2]
        lim = np.abs(diff).max()
        ax.imshow(diff, origin="lower", extent=ext, cmap="RdBu_r", vmin=-lim, vmax=lim)
        gpd.GeoSeries(geoms).boundary.plot(ax=ax, color="black", linewidth=0.4)
        ax.set_xlim(ext[0], ext[1])
        ax.set_ylim(ext[2], ext[3])
        ax.set_title("exact minus center", fontsize=9)
        ax.set_axis_off()
        TABLES.append(f"- grid {n}: DC covers {STATES.geometry[ab.index('DC')].area / (grid.dx * grid.dy):.2f} cells; "
                      f"cells whose density changes by more than 10 %: {(np.abs(diff) > 0.1 * fields['center'][sl].max() * 0.01).sum()} in the crop")
    fig.suptitle("Density field around Washington DC (initial geometry): center sampling against exact coverage", fontsize=11)
    fig.tight_layout()
    fig.savefig(HERE / "coverage_density.png", dpi=110)
    plt.close(fig)


def fig_traces():
    cases = [("states", STATES, "Population", 128), ("states", STATES, "Population", 256), ("districts", DISTRICTS, "Population", 256)]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    TABLES.append("")
    TABLES.append("| input | grid | rasterization | status | iterations | reported max error % | true max error % | true mean error % | seconds |")
    TABLES.append("|---|---|---|---|---|---|---|---|---|")
    for ax, (name, gdf, col, grid) in zip(axes, cases, strict=True):
        for m in MODES:
            result, secs = run(gdf, col, grid, m)
            ax.semilogy(np.arange(1, len(score(result)) + 1), score(result), color=COLORS[m], label=m)
            err = true_errors(result, gdf, col)
            TABLES.append(
                f"| {name} | {grid} | {m} | {result.status.value} | {result.niterations} | {result.get_errors().max_error_pct:.2f} | "
                f"{np.abs(err).max():.2f} | {np.abs(err).mean():.3f} | {secs:.1f} |"
            )
        ax.axhline(1.0, color="gray", linewidth=0.8)
        ax.set_title(f"{name}, grid {grid}", fontsize=10)
        ax.set_xlabel("iteration")
    axes[0].set_ylabel("score (below 1 is converged)")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(HERE / "coverage_traces.png", dpi=110)
    plt.close(fig)


def fig_maps():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    results = {m: run(STATES, "Population", 256, m)[0] for m in MODES}
    for ax, m in zip(axes[:2], MODES, strict=True):
        err = true_errors(results[m], STATES, "Population")
        gdf = gpd.GeoDataFrame({"e": err}, geometry=list(results[m].get_geometry()))
        gdf.plot(column="e", cmap="RdBu_r", vmin=-4.5, vmax=4.5, ax=ax, edgecolor="white", linewidth=0.3, legend=True)
        ax.set_title(f"{m}: area error % (max {np.abs(err).max():.2f})", fontsize=9)
        ax.set_axis_off()
    ax = axes[2]
    a = gpd.GeoSeries(list(results["center"].get_geometry()))
    b = gpd.GeoSeries(list(results["exact"].get_geometry()))
    a.boundary.plot(ax=ax, color=COLORS["center"], linewidth=0.7)
    b.boundary.plot(ax=ax, color=COLORS["exact"], linewidth=0.7)
    ax.set_title("outlines: center (red) and exact (blue)", fontsize=9)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(HERE / "coverage_maps.png", dpi=110)
    plt.close(fig)


def fig_multires():
    from carto_flow.flow_cartogram import CartogramWorkflow

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    TABLES.append("")
    TABLES.append("| input | rasterization | level | grid | status | iterations |")
    TABLES.append("|---|---|---|---|---|---|")
    for ax, (name, gdf) in zip(axes, [("states", STATES), ("districts", DISTRICTS)], strict=True):
        for m in MODES:
            options = MorphOptions(show_progress=False, n_iter=300, density_rasterization=m)
            wf = CartogramWorkflow(gdf, "Population", options=options)
            wf.morph_multiresolution(min_resolution=128, levels=3, options=options)
            offset = 0
            for level, c in enumerate(list(wf)[1:], start=1):
                sc = score(c)
                ax.semilogy(offset + np.arange(1, len(sc) + 1), sc, color=COLORS[m], label=m if level == 1 else None)
                offset += len(sc)
                TABLES.append(f"| {name} | {m} | {level} | {c.grid.sx} | {c.status.value} | {c.niterations} |")
            err = true_errors(wf.last, gdf, "Population")
            TABLES.append(f"| {name} | {m} | total | - | {wf.last.status.value} | {offset} (true max error {np.abs(err).max():.2f} %) |")
        ax.axhline(1.0, color="gray", linewidth=0.8)
        ax.set_title(f"{name}: multiresolution from grid 128, levels concatenated", fontsize=10)
        ax.set_xlabel("iteration (all levels)")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("score (below 1 is converged)")
    fig.tight_layout()
    fig.savefig(HERE / "coverage_multires.png", dpi=110)
    plt.close(fig)


def fig_accuracy():
    """True area error against iteration with the tolerances unreachable, so both runs go the same number of steps."""
    cases = [("states", STATES, 256), ("states", STATES, 512), ("districts", DISTRICTS, 256)]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    TABLES.append("")
    TABLES.append("True area error with unreachable tolerances (300 iterations, stall rule off):")
    TABLES.append("")
    TABLES.append("| input | grid | rasterization | lowest true max error % | at iteration | true max error % at iteration 291 | true mean error % at iteration 291 |")
    TABLES.append("|---|---|---|---|---|---|---|")
    for ax, (name, gdf, grid) in zip(axes, cases, strict=True):
        for m in MODES:
            result, _ = run(gdf, "Population", grid, m, n_iter=300, mean_tol=1e-6, max_tol=1e-6, stall_patience=None, snapshot_every=10)
            its = [i for i in result.snapshots.get_iterations() if (i - 1) % 10 == 0]  # periodic snapshots only
            mx = [np.abs(true_errors_at(result, gdf, "Population", i)).max() for i in its]
            mean300 = np.abs(true_errors_at(result, gdf, "Population", its[-1])).mean()
            ax.semilogy(its, mx, color=COLORS[m], label=m)
            k = int(np.argmin(mx))
            TABLES.append(f"| {name} | {grid} | {m} | {mx[k]:.2f} | {its[k]} | {mx[-1]:.2f} | {mean300:.3f} |")
        ax.set_title(f"{name}, grid {grid}", fontsize=10)
        ax.set_xlabel("iteration")
    axes[0].set_ylabel("true max area error %")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(HERE / "coverage_accuracy.png", dpi=110)
    plt.close(fig)


def tolerance_sweep():
    TABLES.append("")
    TABLES.append("Stopping at tolerances (mean tolerance / max tolerance as fractions; true errors in %):")
    TABLES.append("")
    TABLES.append("| input | grid | tolerances | center: status, iterations, true max, true mean | exact: status, iterations, true max, true mean |")
    TABLES.append("|---|---|---|---|---|")
    for name, gdf, grid in (("states", STATES, 256), ("states", STATES, 512), ("districts", DISTRICTS, 256)):
        for tol in ((0.02, 0.04), (0.01, 0.02), (0.005, 0.01), (0.002, 0.004)):
            cells = []
            for m in MODES:
                result, _ = run(gdf, "Population", grid, m, n_iter=600, mean_tol=tol[0], max_tol=tol[1])
                err = np.abs(true_errors(result, gdf, "Population"))
                cells.append(f"{result.status.value}, {result.niterations}, {err.max():.2f}, {err.mean():.3f}")
            TABLES.append(f"| {name} | {grid} | {tol[0]:g} / {tol[1]:g} | {cells[0]} | {cells[1]} |")


def true_errors_at(result, gdf, col, iteration):
    a = shapely.area(np.asarray(result.get_geometry(iteration=iteration), dtype=object))
    w = gdf[col].to_numpy(float)
    return (a / (w / w.sum() * a.sum()) - 1.0) * 100.0


def rasterization_times():
    TABLES.append("")
    TABLES.append("| input | grid | center ms | exact ms |")
    TABLES.append("|---|---|---|---|")
    for name, gdf in (("states", STATES), ("districts", DISTRICTS)):
        geoms = list(gdf.geometry)
        values = gdf["Population"].to_numpy(float)
        for n in (128, 256, 512, 1024):
            grid = Grid(tuple(gdf.total_bounds), size=n, margin=0.5)
            ms = {}
            for m in MODES:
                compute_density_field_from_geometries(geoms, values, grid, None, rasterization=m)  # compile
                best = min(
                    (lambda t0: (compute_density_field_from_geometries(geoms, values, grid, None, rasterization=m), time.perf_counter() - t0)[1])(time.perf_counter())
                    for _ in range(3)
                )
                ms[m] = best * 1e3
            TABLES.append(f"| {name} | {n} | {ms['center']:.1f} | {ms['exact']:.1f} |")


if __name__ == "__main__":
    fig_density()
    fig_traces()
    fig_maps()
    fig_multires()
    fig_accuracy()
    tolerance_sweep()
    rasterization_times()
    (HERE / "data" / "tables.md").write_text("\n".join(TABLES) + "\n")
