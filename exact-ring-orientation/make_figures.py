"""Figures and tables for the ring-orientation fix of the exact density rasterizer.

The exact rasterizer used to orient rings with shapely.orient_polygons (GEOS); the fix orients them by the sign of
their shoelace area. The "before" runs patch the previous function back in, so one checkout of the fix branch
produces both columns.

Run from a carto-flow checkout of the PR branch (bundled data only):
    NUMBA_NUM_THREADS=8 uv run python make_figures.py
"""

from __future__ import annotations

import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

import carto_flow.flow_cartogram.density as density
from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.density import compute_density_field_from_geometries

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
(HERE / "data").mkdir(exist_ok=True)
STATES = data.load_us_census(population=True).reset_index(drop=True)
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
TABLES: list[str] = []

FIXED = density._exact_coverage_fields


def _legacy(geometries, dens, grid, rho, cover, best, geom_mask):
    """The function before the fix: rings oriented by shapely.orient_polygons."""
    arr = np.empty(len(geometries), dtype=object)
    arr[:] = list(geometries)
    parts, part_g = shapely.get_parts(shapely.orient_polygons(arr), return_index=True)
    rings, ring_p = shapely.get_rings(parts, return_index=True)
    pts, pt_r = shapely.get_coordinates(rings, return_index=True)
    ring_starts = np.searchsorted(pt_r, np.arange(len(rings) + 1))
    geom_rings = np.searchsorted(part_g[ring_p], np.arange(len(arr) + 1))
    u = (pts[:, 0] - (grid.x_coords[0] - 0.5 * grid.dx)) / grid.dx
    v = (pts[:, 1] - (grid.y_coords[0] - 0.5 * grid.dy)) / grid.dy
    ny, nx = rho.shape
    # Pass the sign each ring has after GEOS orientation, so that the kernel applies no further reversal.
    same = pt_r[:-1] == pt_r[1:]
    area2 = np.bincount(pt_r[:-1], weights=np.where(same, u[:-1] * v[1:] - u[1:] * v[:-1], 0.0), minlength=len(rings))
    density._exact_fields(u, v, ring_starts, area2 >= 0.0, geom_rings, dens, nx, ny, rho, cover, best, geom_mask)


def use(version):
    density._exact_coverage_fields = _legacy if version == "before" else FIXED


def true_errors(geoms, values):
    a = np.array([g.area for g in geoms])
    return np.abs(a / (np.asarray(values, float) / np.sum(values) * a.sum()) - 1.0)


def run(gdf, **kw):
    options = MorphOptions(show_progress=False, **kw)
    r = morph_gdf(gdf, "Population", options=options)
    return r, true_errors(r.get_geometry(), gdf["Population"].values).max() * 100


def wrong_orientation(geoms):
    """Regions whose exterior ring reaches the rasterizer with a sign opposite to its shoelace area."""
    out = []
    for i, g in enumerate(geoms):
        for p in g.geoms if hasattr(g, "geoms") else [g]:
            ring = np.asarray(shapely.orient_polygons(np.array([p], dtype=object))[0].exterior.coords)
            if 0.5 * np.sum(ring[:-1, 0] * ring[1:, 1] - ring[1:, 0] * ring[:-1, 1]) < 0:
                out.append(i)
                break
    return out


def table(rows):
    lines = ["| case | before: status, iterations, true max error | after: status, iterations, true max error |", "|---|---|---|"]
    for label, a, b in rows:
        lines.append(f"| {label} | {a} | {b} |")
    TABLES.append("\n".join(lines))


def scenarios():
    cases = [
        ("districts, grid 128, dt 0.4, 1 % / 2 %", DISTRICTS, dict(grid_size=128, dt=0.4, mean_tol=0.01, max_tol=0.02, n_iter=400)),
        ("districts, grid 128, dt 0.2, 1 % / 2 %", DISTRICTS, dict(grid_size=128, dt=0.2, mean_tol=0.01, max_tol=0.02, n_iter=400)),
        ("districts, grid 256, tolerances 0.5 % / 1 %", DISTRICTS, dict(grid_size=256, mean_tol=0.005, max_tol=0.01, n_iter=400)),
        ("districts, grid 256, default tolerances", DISTRICTS, dict(grid_size=256, n_iter=400)),
        ("states, grid 256, default tolerances", STATES, dict(grid_size=256, n_iter=400)),
    ]
    rows, runs = [], {}
    for label, gdf, kw in cases:
        out = []
        for version in ("before", "after"):
            use(version)
            r, e = run(gdf, **kw)
            out.append(f"{r.status.value}, {r.niterations}, {e:.2f} %")
            runs[(label, version)] = r
        rows.append((label, *out))
        print(label, out, flush=True)
    use("after")
    table(rows)
    return runs, cases


def figure_histories(runs, label):
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for version, color in (("before", "tab:red"), ("after", "tab:blue")):
        c = runs[(label, version)].convergence
        ax.semilogy(np.arange(1, len(c.max_errors_pct) + 1), c.max_errors_pct, color=color, label=f"{version}: {runs[(label, version)].status.value}, {runs[(label, version)].niterations} iterations")
    ax.set_xlabel("iteration")
    ax.set_ylabel("max error (%)")
    ax.set_title(label, fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "histories.png", dpi=130)


def figure_field(runs, label, kw):
    r = runs[(label, "before")]
    geoms = list(r.get_geometry())
    errs = true_errors(geoms, DISTRICTS["Population"].values)
    worst = int(np.argmax(errs))
    wrong = wrong_orientation(geoms)
    w = max(wrong, key=lambda i: errs[i])
    opts = MorphOptions(**kw)
    grid = opts.get_grid(opts._calculate_bounds_from_geometries(DISTRICTS.geometry.values))
    values = DISTRICTS["Population"].values.astype(float)
    mean = values.sum() / sum(g.area for g in geoms)
    fields = {}
    for version in ("before", "after"):
        use(version)
        fields[version] = compute_density_field_from_geometries(geoms, values, grid, mean, rasterization="exact") / mean - 1
    use("after")
    cell = grid.dx
    bx = geoms[w].bounds
    cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    half = max(bx[2] - bx[0], bx[3] - bx[1]) / 2 + 3 * cell
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    vmax = max(abs(fields["before"]).max(), abs(fields["after"]).max())
    vmax = min(vmax, 0.5)
    for ax, title, f in zip(axes, ("before", "after", "after minus before"), (fields["before"], fields["after"], fields["after"] - fields["before"])):
        lim = vmax if title != "after minus before" else abs(f).max()
        im = ax.pcolormesh(grid.X, grid.Y, f, cmap="RdBu_r", vmin=-lim, vmax=lim, shading="auto")
        for g in geoms:
            if g.distance(geoms[w]) < half:
                for p in g.geoms if hasattr(g, "geoms") else [g]:
                    ax.plot(*np.asarray(p.exterior.coords).T, color="k", lw=0.5)
        for p in geoms[w].geoms if hasattr(geoms[w], "geoms") else [geoms[w]]:
            ax.plot(*np.asarray(p.exterior.coords).T, color="tab:green", lw=1.6)
        ax.set_xlim(cx - half, cx + half)
        ax.set_ylim(cy - half, cy + half)
        ax.set_aspect("equal")
        ax.set_title(f"density / mean - 1, {title}" if title != "after minus before" else title, fontsize=9)
        fig.colorbar(im, ax=ax, shrink=0.7)
    fig.suptitle(f"Region {w} of the stalled run (green): its ring reaches the rasterizer with the wrong sign; true error {errs[w]*100:.1f} %, valid: {bool(shapely.is_valid(geoms[w]))}; grid cell {cell:.3g}", fontsize=9)
    fig.tight_layout()
    fig.savefig(HERE / "field.png", dpi=130)
    n_invalid = int((~shapely.is_valid(np.array(geoms, dtype=object))).sum())
    changed = np.abs(fields["after"] - fields["before"]) > 1e-9
    near = [int(i) for i in np.argsort([g.distance(geoms[worst]) for g in geoms])[:6] if i != worst]
    TABLES.append(
        f"Stalled run (before): {n_invalid} of {len(geoms)} regions are invalid; the rings of regions {wrong} reach the rasterizer with a sign opposite to their shoelace area "
        f"(true errors {', '.join(f'{errs[i]*100:.1f} %' for i in wrong)}). The worst region is {worst} (error {errs[worst]*100:.1f} %); the wrong-sign regions are {'neighbors of it' if set(wrong) & set(near) else 'not among its six nearest neighbors'}. "
        f"The two fields differ in {int(changed.sum())} cells; the summed density deviation (cells) there is {float(fields['before'][changed].sum()):+.3f} before and {float(fields['after'][changed].sum()):+.3f} after."
    )


if __name__ == "__main__":
    runs, cases = scenarios()
    label, _, kw = cases[0]
    figure_histories(runs, label)
    figure_field(runs, label, kw)
    (HERE / "data" / "tables.md").write_text("\n\n".join(TABLES) + "\n")
    print("\n\n".join(TABLES))
