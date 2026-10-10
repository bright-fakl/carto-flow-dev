"""Convergence plots for the adaptive-recompute experiment.

Reads the per-run score histories stored in data/out_<case>_<grid>.pkl (written by
scripts/run_case.py on investigate/adaptive-recompute @ 2650f6a) and writes
convergence_anisotropy.png, convergence_states_districts.png and
convergence_counties.png next to this file. Runs with `uv run python make_figures.py`.
The score is max(mean/mean_tol, max/max_tol) on the log2 errors; below 1 is converged.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"

# One color per policy, the same in every figure (categorical slots 1 to 5).
STYLE = {
    "fixed10": ("recompute every 10 (default)", "#2a78d6"),
    "fixed5": ("recompute every 5", "#1baf7a"),
    "fixed2": ("recompute every 2", "#eda100"),
    "adapt": ("refresh on rise, max interval 10", "#eb6834"),
    "adSC": ("refresh on rise + step control", "#e87ba4"),
}


def load(case: str, grid: int) -> dict:
    with open(HERE / "data" / f"out_{case}_{grid}.pkl", "rb") as f:
        return pickle.load(f)


def pick(res: dict, kind: str, key: str | None = None) -> dict | None:
    names = {
        "fixed10": "fixed10",
        "fixed5": "fixed5",
        "fixed2": "fixed2",
        "adapt": key or "adapt_t0.01_m1",
        "adSC": key or "adSC_t0.01_m1_best",
    }
    return res.get(names[kind])


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def draw(ax, res: dict, kinds: list[str], x0: int = 0, keys: dict | None = None, rug: tuple[str, ...] = ()) -> None:
    keys = keys or {}
    for kind in kinds:
        run = pick(res, kind, keys.get(kind))
        if run is None:
            continue
        label, color = STYLE[kind]
        score = np.asarray(run["score"])
        x = np.arange(len(score))
        keep = x >= x0
        width = 3.2 if kind == "fixed10" else 1.5
        ax.plot(x[keep], score[keep], color=color, linewidth=width, alpha=0.6 if kind == "fixed10" else 1.0, label=f"{label}: {len(score)} it, {run['rec']} rec")
        if kind in rug:
            marks = [i for i in run["refresh_iters"] if i >= x0]
            ax.plot(marks, [0.62] * len(marks), "|", color=color, markersize=6, markeredgewidth=1.2, clip_on=False)
    ax.axhline(1.0, color=INK, linestyle="--", linewidth=0.8)
    ax.set_yscale("log")


def finish(fig, handles_ax, title: str, path: Path) -> None:
    handles, labels = handles_ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle(title, fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(path, dpi=140, facecolor=SURFACE)
    plt.close(fig)


def anisotropy() -> None:
    cases = [("horiz", "horizontal"), ("tang", "tangential"), ("tilt", "tilted")]
    kinds = ["fixed10", "fixed5", "fixed2", "adapt"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.4), gridspec_kw={"hspace": 0.28, "wspace": 0.2})
    for col, (case, title) in enumerate(cases):
        res = load(case, 256)
        ax = axes[0, col]
        style_axes(ax)
        draw(ax, res, kinds)
        ax.set_title(f"{title}: full run", fontsize=9, color=INK)
        if col == 0:
            ax.set_ylabel("score (below 1 is converged)", fontsize=8, color=MUTED)
        zoom = axes[1, col]
        style_axes(zoom)
        start = next(i for i, s in enumerate(res["fixed10"]["score"]) if s < 20)
        draw(zoom, res, kinds, x0=start, rug=("fixed10", "adapt"))
        zoom.set_ylim(0.55, 20)
        zoom.set_title(f"{title}: zoom, score below 20", fontsize=9, color=INK)
        zoom.set_xlabel("iteration", fontsize=8, color=MUTED)
        if col == 0:
            zoom.set_ylabel("score", fontsize=8, color=MUTED)
    finish(fig, axes[1, 0], "Strong anisotropy, 49 US states, grid 256: score per iteration. Legend: iterations, recomputes. Bottom ticks: field refreshes of the default (blue) and refresh-on-rise (orange) runs", HERE / "convergence_anisotropy.png")


def states_districts() -> None:
    kinds = ["fixed10", "fixed5", "fixed2", "adapt"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.4), gridspec_kw={"hspace": 0.3, "wspace": 0.2})
    for row, (case, name) in enumerate([("states", "US states"), ("districts", "congressional districts")]):
        for col, grid in enumerate([256, 512]):
            ax = axes[row, col]
            style_axes(ax)
            draw(ax, load(case, grid), kinds)
            ax.set_title(f"{name}, grid {grid}", fontsize=9, color=INK)
            if col == 0:
                ax.set_ylabel("score (below 1 is converged)", fontsize=8, color=MUTED)
            if row == 1:
                ax.set_xlabel("iteration", fontsize=8, color=MUTED)
    finish(fig, axes[1, 0], "Default options: refresh on rise follows the default until the score first rises", HERE / "convergence_states_districts.png")


def counties() -> None:
    kinds = ["fixed10", "fixed2", "adapt", "adSC"]
    keys = {"adapt": "adapt_t0.0_m1", "adSC": "adSC_t0.01_m1_best"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"wspace": 0.15})
    for col, grid in enumerate([256, 512]):
        ax = axes[col]
        style_axes(ax)
        draw(ax, load("counties", grid), kinds, keys=keys)
        ax.set_title(f"3,108 counties, grid {grid}, 300 iterations", fontsize=9, color=INK)
        ax.set_xlabel("iteration", fontsize=8, color=MUTED)
        if col == 0:
            ax.set_ylabel("score (below 1 is converged)", fontsize=8, color=MUTED)
    fig.subplots_adjust(bottom=0.27)
    finish(fig, axes[0], "Counties do not converge in 300 iterations: the score ends near 10 whatever the schedule", HERE / "convergence_counties.png")


if __name__ == "__main__":
    anisotropy()
    states_districts()
    counties()
