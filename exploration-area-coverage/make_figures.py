"""Figures and tables for the area-coverage exploration.

Reads data/*.pkl and data/raster_time.json (written by scripts/) and writes PNGs next to this file.
Run with `uv run python make_figures.py` from the carto-flow worktree (branch investigate/area-coverage).
The score is max(mean/mean_tol, max/max_tol) on the log2 errors; below 1 is converged.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
D = HERE / "data"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"

# One color per rasterization variant, the same in every figure.
STYLE = {
    "center": ("cell-center sampling (current)", "#2a78d6"),
    "s2": ("supersample 2x2", "#1baf7a"),
    "s4": ("supersample 4x4", "#eda100"),
    "s8": ("supersample 8x8", "#eb6834"),
    "exact": ("exact coverage", "#e87ba4"),
}


def load(case: str, grid: int) -> dict:
    p = D / f"out_{case}_{grid}.pkl"
    return pickle.load(open(p, "rb")) if p.exists() else {}


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def draw(ax, res: dict, ro: str = "0.01", x0: int = 0, variants=tuple(STYLE), rug: tuple[str, ...] = ()) -> None:
    for v in variants:
        run = res.get(f"{v}|ro{ro}|dtbase|re10")
        if run is None:
            continue
        label, color = STYLE[v]
        score = np.asarray(run["score"])
        x = np.arange(len(score))
        keep = x >= x0
        width = 3.0 if v == "center" else 1.5
        ax.plot(
            x[keep],
            score[keep],
            color=color,
            linewidth=width,
            alpha=0.6 if v == "center" else 1.0,
            label=f"{label}: {len(score)} it, {run['rec']} rec",
        )
        if v in rug:
            marks = [i for i in run["refresh_iters"] if i >= x0]
            ax.plot(marks, [0.62] * len(marks), "|", color=color, markersize=6, markeredgewidth=1.2, clip_on=False)
    ax.axhline(1.0, color=INK, linestyle="--", linewidth=0.8)
    ax.set_yscale("log")


def finish(fig, ax, title: str, path: Path, ncol: int = 3) -> None:
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=ncol, frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle(title, fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(path, dpi=140, facecolor=SURFACE)
    plt.close(fig)


def labels(ax, title, col=0, bottom=False):
    ax.set_title(title, fontsize=9, color=INK)
    if col == 0:
        ax.set_ylabel("score (below 1 is converged)", fontsize=8, color=MUTED)
    if bottom:
        ax.set_xlabel("iteration", fontsize=8, color=MUTED)


def states_aniso() -> None:
    cases = [("states", "states, default"), ("horiz", "horizontal"), ("tang", "tangential"), ("tilt", "tilted")]
    fig, axes = plt.subplots(3, 4, figsize=(16, 10.5), gridspec_kw={"hspace": 0.32, "wspace": 0.2})
    for row, grid in enumerate((128, 256, 512)):
        for col, (case, title) in enumerate(cases):
            ax = axes[row, col]
            style_axes(ax)
            draw(ax, load(case, grid))
            labels(ax, f"{title}, grid {grid}", col, row == 2)
    fig.subplots_adjust(bottom=0.12)
    finish(
        fig,
        axes[0, 1],
        "49 US states, refresh_on_rise = 0.01 (current stack), score per iteration. Legend: iterations, field recomputes",
        HERE / "convergence_states_aniso.png",
        ncol=3,
    )


def sawtooth() -> None:
    cases = [("horiz", "horizontal"), ("tang", "tangential"), ("tilt", "tilted")]
    fig, axes = plt.subplots(2, 3, figsize=(14, 7.6), gridspec_kw={"hspace": 0.3, "wspace": 0.2})
    for col, (case, title) in enumerate(cases):
        res = load(case, 256)
        for row, ro in enumerate(("None", "0.01")):
            ax = axes[row, col]
            style_axes(ax)
            ref = res.get(f"center|ro{ro}|dtbase|re10")
            start = next((i for i, s in enumerate(ref["score"]) if s < 20), 0) if ref else 0
            draw(ax, res, ro=ro, x0=start, variants=("center", "exact"), rug=("center", "exact"))
            ax.set_ylim(0.55, 20)
            labels(ax, f"{title}, grid 256, refresh_on_rise {'off' if ro == 'None' else 'on'}", col, row == 1)
    fig.subplots_adjust(bottom=0.14)
    finish(
        fig,
        axes[0, 0],
        "Sawtooth once the score is below 20, center sampling vs exact coverage. Ticks at the bottom: field refreshes",
        HERE / "sawtooth_anisotropy.png",
        ncol=2,
    )


def multires() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), gridspec_kw={"hspace": 0.3, "wspace": 0.2})
    for row, case in enumerate(("states", "districts")):
        p = D / f"mr_{case}_off.pkl"
        if not p.exists():
            continue
        res = pickle.load(open(p, "rb"))
        for col, ro in enumerate(("0.01", "None")):
            ax = axes[row, col]
            style_axes(ax)
            for v, (lab, color) in STYLE.items():
                r = res.get(f"{v}|ro{ro if ro == 'None' else float(ro)}")
                if r is None:
                    continue
                x0 = 0
                for lv in r["levels"]:
                    s = np.asarray(lv["score"])
                    ax.plot(
                        np.arange(x0, x0 + len(s)),
                        s,
                        color=color,
                        linewidth=3.0 if v == "center" else 1.5,
                        alpha=0.6 if v == "center" else 1.0,
                        label=lab + ": " + " + ".join(f"{q['grid']}:{q['it']}" for q in r["levels"]) if x0 == 0 else None,
                    )
                    ax.plot([x0 + len(s) - 1], [s[-1]], "o", color=color, markersize=3)
                    x0 += len(s)
            ax.axhline(1.0, color=INK, linestyle="--", linewidth=0.8)
            ax.set_yscale("log")
            labels(ax, f"{case} multiresolution (128, 256, 512), refresh_on_rise {'off' if ro == 'None' else 'on'}", col, row == 1)
    fig.subplots_adjust(bottom=0.14)
    handles, lbls = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="lower center", ncol=2, frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle(
        "Multiresolution (stall rule off, 300 iterations per level): score per iteration, levels concatenated. Legend: iterations per level",
        fontsize=10,
        color=INK,
    )
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "convergence_multires.png", dpi=140, facecolor=SURFACE)
    plt.close(fig)


def counties() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"wspace": 0.15})
    for col, grid in enumerate((256, 512)):
        ax = axes[col]
        style_axes(ax)
        draw(ax, load("counties", grid))
        labels(ax, f"3,108 counties, grid {grid}, 300 iterations", col, True)
    fig.subplots_adjust(bottom=0.25)
    finish(fig, axes[0], "Counties: the plateau (score near 10) does not move with the rasterization", HERE / "convergence_counties.png")


def districts() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"wspace": 0.15})
    for col, grid in enumerate((256, 512)):
        ax = axes[col]
        style_axes(ax)
        draw(ax, load("districts", grid))
        labels(ax, f"congressional districts, grid {grid}", col, True)
    fig.subplots_adjust(bottom=0.25)
    finish(fig, axes[0], "432 districts, refresh_on_rise = 0.01", HERE / "convergence_districts.png")


def raster_time() -> None:
    p = D / "raster_time.json"
    if not p.exists():
        return
    t = json.loads(p.read_text())
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), gridspec_kw={"wspace": 0.22})
    grids = (128, 256, 512, 1024)
    for ax, case in zip(axes, ("states", "districts", "counties")):
        style_axes(ax)
        for v, (lab, color) in STYLE.items():
            cov = {"center": "None", "s2": "2", "s4": "4", "s8": "8", "exact": "exact"}[v]
            ys = [t.get(f"{case}|{n}|{cov}") for n in grids]
            ax.plot(grids, [y * 1e3 if y else np.nan for y in ys], "o-", color=color, linewidth=2 if v in ("center", "exact") else 1.3, label=lab)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks(grids, [str(n) for n in grids])
        ax.set_title(case, fontsize=9, color=INK)
        ax.set_xlabel("grid size", fontsize=8, color=MUTED)
        if case == "states":
            ax.set_ylabel("rasterization time per call (ms)", fontsize=8, color=MUTED)
    fig.subplots_adjust(bottom=0.27)
    finish(fig, axes[0], "Rasterization time per field recompute (min of 3, NUMBA_NUM_THREADS=4)", HERE / "raster_time.png", ncol=3)


if __name__ == "__main__":
    states_aniso()
    sawtooth()
    multires()
    counties()
    districts()
    raster_time()
