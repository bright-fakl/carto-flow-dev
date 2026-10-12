"""Why the 3,108 counties do not converge: targets below the grid resolution.

Run from a carto-flow checkout of main (needs the prepared counties set, not bundled):
    COUNTIES_PARQUET=counties_prepared.parquet NUMBA_NUM_THREADS=8 uv run python counties_check.py
The set is a GeoDataFrame in ESRI:102008 with GEOID, total_votes and geometry; MorphOptions use area_scale 1e-6.
"""

import os
import time
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely

from carto_flow.flow_cartogram import CartogramWorkflow, MorphOptions, morph_gdf

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
(HERE / "data").mkdir(exist_ok=True)
gdf = gpd.read_parquet(os.environ["COUNTIES_PARQUET"])
vals = gdf["total_votes"].values.astype(float)
OUT: list[str] = []


def log(line):
    print(line, flush=True)
    OUT.append(line)


def errors(geoms):
    a = np.array([g.area for g in geoms])
    return np.abs(a / (vals / vals.sum() * a.sum()) - 1) * 100, a


base = MorphOptions(grid_size=256, n_iter=300, area_scale=1e-6, show_progress=False)
grid = base.get_grid(base._calculate_bounds_from_geometries(gdf.geometry.values))
target = vals / vals.sum() * gdf.geometry.area.sum()

log("## Targets below one grid cell\n")
log(f"Votes range from {vals.min():.0f} to {vals.max():.0f} (median {np.median(vals):.0f}); the target area of a county is its share of the total area.\n")
log("| grid | counties with a target area below one cell | below 0.1 cell |\n|---|---|---|")
for n in (256, 512, 1024, 2048):
    cell = (grid.dx * 256 / n) ** 2
    log(f"| {n} | {(target < cell).sum()} ({(target < cell).mean() * 100:.0f} %) | {(target < 0.1 * cell).sum()} |")

log("\n## Single-level runs (stall rule on, 300 iterations)\n")
log("| grid | status, iterations | true mean / max error % | regions with target < 1 cell: count, median error % | other regions: median error %, max error % | regions off by > 10 % (of which target < 1 cell) | invalid output regions |\n|---|---|---|---|---|---|---|")
for n in (256, 512, 1024):
    r = morph_gdf(gdf, "total_votes", options=base.copy_with(grid_size=n))
    geoms = list(r.get_geometry())
    e, a = errors(geoms)
    cell = (grid.dx * 256 / n) ** 2
    tg = vals / vals.sum() * a.sum()
    small = tg < cell
    inv = int((~shapely.is_valid(np.array(geoms, dtype=object))).sum())
    log(f"| {n} | {r.status.value}, {r.niterations} | {e.mean():.1f} / {e.max():.0f} | {small.sum()}, {np.median(e[small]):.0f} | {np.median(e[~small]):.1f}, {e[~small].max():.0f} | {(e > 10).sum()} ({((e > 10) & small).sum()}) | {inv} |")

log("\n## Multiresolution (128 to 1024, 4 levels)\n")
t = time.perf_counter()
wf = CartogramWorkflow(gdf, "total_votes", options=base.copy_with(n_iter=400))
wf.morph_multiresolution(min_resolution=128, levels=4)
e, _ = errors(list(wf.last.get_geometry()))
levels = ", ".join(f"{r.status.value} {r.niterations}" for r in wf.results[1:])
log(f"Levels: {levels}; true mean {e.mean():.1f} %, max {e.max():.0f} %, {(e > 10).sum()} regions off by more than 10 % ({time.perf_counter() - t:.0f} s).")

log("\n## Stall rule off, grid 512 (reported mean / max error % at iteration)\n")
r = morph_gdf(gdf, "total_votes", options=base.copy_with(grid_size=512, n_iter=1500, stall_patience=None))
c = r.convergence
idx = [i for i in (0, 49, 99, 199, 299, 499, 799, 1199, len(c.mean_errors_pct) - 1) if i < len(c.mean_errors_pct)]
log("| " + " | ".join(str(i + 1) for i in idx) + " |\n|" + "---|" * len(idx))
log("| " + " | ".join(f"{c.mean_errors_pct[i]:.1f} / {c.max_errors_pct[i]:.0f}" for i in idx) + " |")

log("\n## Worst regions, grid 512 (stall rule on)\n")
r = morph_gdf(gdf, "total_votes", options=base.copy_with(grid_size=512))
geoms = list(r.get_geometry())
e, a = errors(geoms)
cell = (grid.dx * 256 / 512) ** 2
tg = vals / vals.sum() * a.sum()
small = tg < cell
log("| county | error % | target (cells) | area (cells) |\n|---|---|---|---|")
for k in np.argsort(-e)[:8]:
    log(f"| {gdf['GEOID'].iloc[k]} | {e[k]:.0f} | {tg[k] / cell:.3f} | {a[k] / cell:.2f} |")
log(f"\nSub-cell regions: target {tg[small].sum() / cell:.0f} cells in total, actual {a[small].sum() / cell:.0f} cells; all other regions: target {tg[~small].sum() / cell:.0f}, actual {a[~small].sum() / cell:.0f}. Regions with a target of at least one cell and an error above 10 %: {((e > 10) & ~small).sum()} of {(~small).sum()} (median error of that group {np.median(e[~small]):.1f} %).")
(HERE / "data" / "tables.md").write_text("\n".join(OUT) + "\n")
