"""The thin district that stalls the coarse level of the districts multiresolution run (region_420*.png).

Districts, coarse level of morph_multiresolution (grid 128), dt 0.2, tolerances 0.5 % / 1 %. Three runs: constant dt,
adaptive_dt without the contested-regions condition (CONTESTED_FRACTION = 0, the rule that stalls) and adaptive_dt
as shipped. Run from a carto-flow checkout of the PR branch:
    NUMBA_NUM_THREADS=8 uv run python region_420.py
region_420_errors.png: signed area error of region 420 and the 90th percentile of |error| over all other regions,
with the step fraction actually used. field_region_420.png: density and velocity around region 420, zoomed on the
region (window of 12 grid cells around its bounding box), for constant dt (mid-swing) and the stalled run (last iteration).
"""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

import carto_flow.flow_cartogram.stepsize as stepsize
from carto_flow.flow_cartogram import CartogramWorkflow
from carto_flow.flow_cartogram.grid import build_multilevel_grids
from make_figures import options_for, source

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
REGION = 420
TOL = (0.005, 0.01)

USED: list[float] = []
_current = stepsize.StepController.current


def _recording(self, step):
    value = _current(self, step)
    if step == 0:
        USED.clear()
    USED.append(value)
    return value


stepsize.StepController.current = _recording


def run(adaptive, contested):
    stepsize.CONTESTED_FRACTION = contested
    gdf = source("districts")
    o = options_for("districts", adaptive, 256, 0.2, TOL, n_iter=300, snapshot_every=1, save_internals=True)
    wf = CartogramWorkflow(gdf, "Population", options=o)
    grid = build_multilevel_grids(wf._original_gdf.total_bounds, 128, 3, margin=o.grid_margin, square=True)[0]
    res = wf.morph(options=o.copy_with(grid=grid))
    snaps = res.snapshots.snapshots
    log_errors = np.array([s.errors.log_errors for s in snaps])
    return {"res": res, "snaps": snaps, "le": log_errors, "fraction": list(USED), "status": res.status.value, "it": res.niterations}


def region_errors(le):
    pct = (2.0**le - 1) * 100
    others = np.delete(np.abs(pct), REGION, axis=1)
    return pct[:, REGION], np.percentile(others, 90, axis=1), others.max(axis=1)


def figure_errors(runs):
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True, gridspec_kw={"hspace": 0.12})
    for ax, (label, r) in zip(axes, runs.items(), strict=True):
        e420, p90, mx = region_errors(r["le"])
        x = np.arange(1, len(e420) + 1)
        ax.plot(x, np.abs(e420), color="#d62728", label=f"region {REGION}: |error|")
        ax.plot(x, p90, color="#2a78d6", label="other regions: 90th percentile of |error|")
        ax.plot(x, mx, color="#2a78d6", alpha=0.35, label="other regions: maximum |error|")
        ax.axhline(TOL[1] * 100, color="black", linestyle="--", linewidth=0.8, label="max tolerance 1 %")
        ax.set_yscale("log")
        ax.set_ylabel("|area error| %")
        ax.set_title(f"{label}: {r['it']} iterations, {r['status']}", fontsize=9)
        ax2 = ax.twinx()
        ax2.plot(x, r["fraction"][: len(x)], color="#eb6834", linewidth=1.4, label="step fraction (right)")
        ax2.set_ylim(0, 1.05)
        ax2.set_ylabel("fraction of dt")
        ax.grid(True, color="#e6e5e1", linewidth=0.8)
        ax.set_xlim(90, None)
        if ax is axes[0]:
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7, loc="upper left")
    axes[-1].set_xlabel("iteration")
    fig.savefig(HERE / "region_420_errors.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def field_at(res, iteration):
    snaps = res.internals.snapshots
    use = [s for s in snaps if s.iteration <= iteration]
    return use[-1]


def figure_field(runs):
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for row, (label, key, iteration) in enumerate((("constant dt, iteration 120", "constant dt", 120), ("stalled run (no contested condition), last iteration", "no contested", None))):
        r = runs[key]
        res = r["res"]
        it = iteration or r["it"]
        grid = res.grid
        snap = r["snaps"][min(it, len(r["snaps"])) - 1]
        geom = list(snap.geometry)
        bounds = geom[REGION].bounds
        pad = 12 * max(grid.dx, grid.dy)
        x0, x1, y0, y1 = bounds[0] - pad, bounds[2] + pad, bounds[1] - pad, bounds[3] + pad
        f = field_at(res, it)
        ix = (grid.x_coords >= x0) & (grid.x_coords <= x1)
        iy = (grid.y_coords >= y0) & (grid.y_coords <= y1)
        ext = [grid.x_coords[ix][0], grid.x_coords[ix][-1], grid.y_coords[iy][0], grid.y_coords[iy][-1]]
        rho = f.rho[np.ix_(iy, ix)]
        mean = np.nanmean(f.rho)
        im = axes[row, 0].imshow(rho / mean, origin="lower", extent=ext, cmap="RdBu_r", vmin=0.5, vmax=1.5)
        fig.colorbar(im, ax=axes[row, 0], shrink=0.7)
        axes[row, 0].set_title(f"{label}\ndensity / mean (field of iteration {f.iteration})", fontsize=9)
        speed = np.hypot(f.vx, f.vy)[np.ix_(iy, ix)]
        im = axes[row, 1].imshow(speed, origin="lower", extent=ext, cmap="viridis")
        fig.colorbar(im, ax=axes[row, 1], shrink=0.7)
        step = max(1, int(ix.sum() // 18))
        X, Y = np.meshgrid(grid.x_coords[ix], grid.y_coords[iy])
        axes[row, 1].quiver(X[::step, ::step], Y[::step, ::step], f.vx[np.ix_(iy, ix)][::step, ::step], f.vy[np.ix_(iy, ix)][::step, ::step], color="white", scale=None)
        axes[row, 1].set_title("velocity magnitude and direction", fontsize=9)
        le = r["le"][it - 1]
        for k, g in enumerate(geom):
            if not shapely.intersects(g, shapely.box(x0, y0, x1, y1)):
                continue
            color = plt.cm.RdBu_r(0.5 + np.clip(le[k], -0.5, 0.5))
            for poly in getattr(g, "geoms", [g]):
                xs, ys = poly.exterior.xy
                axes[row, 2].fill(xs, ys, facecolor=color, edgecolor="black", linewidth=2.0 if k == REGION else 0.4)
        axes[row, 2].set_title(f"regions by signed error (red: too large); region {REGION} outlined, error {(2.0 ** le[REGION] - 1) * 100:+.1f} %", fontsize=9)
        for ax in axes[row]:
            ax.set_xlim(x0, x1)
            ax.set_ylim(y0, y1)
            ax.set_aspect("equal")
    fig.suptitle(f"Districts, coarse level (grid 128, cell {grid.dx:.3g}), window of 12 cells around region {REGION}", fontsize=10)
    fig.savefig(HERE / "field_region_420.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    runs = {
        "constant dt": run(False, stepsize.CONTESTED_FRACTION),
        "no contested": run(True, 0.0),
        "contested": run(True, 0.8),
    }
    stepsize.CONTESTED_FRACTION = 0.8
    for k, r in runs.items():
        e420, p90, mx = region_errors(r["le"])
        print(k, r["status"], r["it"], "region 420 |error| at last iteration", round(float(abs(e420[-1])), 2), "% ; max error of the others", round(float(mx[-1]), 2), "%", flush=True)
    figure_errors({"constant dt": runs["constant dt"], "adaptive_dt without the contested condition": runs["no contested"], "adaptive_dt (shipped)": runs["contested"]})
    figure_field(runs)
