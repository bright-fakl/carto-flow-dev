"""Figures for the adaptive-step exploration.

Reads data/traces.json (score histories, scripts/traces.py) and data/grid_cheap.jsonl,
data/grid_counties.jsonl (robustness grid, scripts/sweep_grid.py) and writes
traces_*.png and robustness.png next to this file. Run with `uv run python make_figures.py`.
The score is max(mean/mean_tol, max/max_tol) on the log2 errors; below 1 is converged.
Data were produced on investigate/adaptive-step (see summary.md for the commit).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"

# One color per variant, the same in every figure.
STYLE = {
    "base": ("constant dt (current)", "#2a78d6"),
    "A_r3_m0.05": ("A: error-driven dt, ref 3", "#1baf7a"),
    "A_r10_m0.05": ("A: error-driven dt, ref 10", "#eda100"),
    "B_0.1": ("B: area change <= 10 % per step", "#e87ba4"),
    "C_r10": ("C: error-driven dt in the first window only", "#8a63d2"),
    "AB_r10_f0.05": ("A (ref 10) + B (5 %)", "#eb6834"),
}


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def traces() -> None:
    runs = json.load(open(HERE / "data" / "traces.json"))
    idx = {(r["case"], r["dt"], r["rr"], r["variant"]): r for r in runs}
    panels = [
        ("states_t", 0.2, "states, tight tolerances, dt 0.2"),
        ("horiz", 0.6, "horizontal anisotropy, dt 0.6"),
        ("tang", 0.6, "tangential anisotropy, dt 0.6"),
        ("districts", 0.6, "districts, dt 0.6"),
    ]
    for fname, rows, suptitle in (
        ("traces_states.png", panels, "Score per iteration, grid 256, stall rule off, recompute_every 10"),
        (
            "traces_counties.png",
            [("counties", 0.2, "3,108 counties, dt 0.2"), ("horiz", 0.2, "horizontal anisotropy, dt 0.2")],
            "Score per iteration, grid 256, stall rule off, recompute_every 10",
        ),
    ):
        fig, axes = plt.subplots(2, len(rows), figsize=(3.6 * len(rows) + 1, 7.0), squeeze=False, gridspec_kw={"hspace": 0.28, "wspace": 0.22})
        for c, (case, dt, title) in enumerate(rows):
            for rr_i, rr in enumerate(("off", "on")):
                ax = axes[rr_i, c]
                style_axes(ax)
                for v, (label, color) in STYLE.items():
                    run = idx.get((case, dt, rr, v))
                    if run is None:
                        continue
                    s = np.asarray(run["score"])
                    ax.plot(np.arange(1, len(s) + 1), s, color=color, linewidth=2.6 if v == "base" else 1.3, alpha=0.6 if v == "base" else 1.0, label=f"{label}: {len(s)} it, {run['rec']} rec")
                ax.axhline(1.0, color=INK, linestyle="--", linewidth=0.8)
                ax.set_yscale("log")
                ax.set_ylim(0.5, 100)
                ax.set_title(f"{title}, refresh on rise {rr}", fontsize=8, color=INK)
                if c == 0:
                    ax.set_ylabel("score (below 1 is converged)", fontsize=8, color=MUTED)
                if rr_i == 1:
                    ax.set_xlabel("iteration", fontsize=8, color=MUTED)
        h, l = axes[0, 0].get_legend_handles_labels()
        fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=8, labelcolor=INK)
        fig.suptitle(suptitle, fontsize=10, color=INK)
        fig.subplots_adjust(bottom=0.14)
        fig.patch.set_facecolor(SURFACE)
        fig.savefig(HERE / fname, dpi=140, facecolor=SURFACE)
        plt.close(fig)


def robustness() -> None:
    rows = []
    for name in ("grid_cheap.jsonl", "grid_counties.jsonl"):
        p = HERE / "data" / name
        if p.exists():
            rows += [json.loads(line) for line in open(p)]
    variants = [v for v in STYLE if any(r["variant"] == v for r in rows)]
    dts = sorted({r["dt"] for r in rows})
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"wspace": 0.12})
    for ax, rr in zip(axes, ("off", "on")):
        m = np.zeros((len(variants), len(dts)))
        n = np.zeros_like(m)
        for r in rows:
            if r["rr"] == rr and r["variant"] in variants:
                i, j = variants.index(r["variant"]), dts.index(r["dt"])
                n[i, j] += 1
                m[i, j] += r["cls"] == "converged"
        im = ax.imshow(m / np.maximum(n, 1), vmin=0, vmax=1, cmap="Blues", aspect="auto")
        for i in range(len(variants)):
            for j in range(len(dts)):
                ax.text(j, i, f"{int(m[i, j])}/{int(n[i, j])}", ha="center", va="center", fontsize=8, color=INK if m[i, j] / max(n[i, j], 1) < 0.7 else "white")
        ax.set_xticks(range(len(dts)), [str(d) for d in dts], fontsize=8, color=MUTED)
        ax.set_yticks(range(len(variants)), [STYLE[v][0] if rr == "off" else "" for v in variants], fontsize=8, color=INK)
        ax.set_xlabel("dt (maximum step, cells)", fontsize=8, color=MUTED)
        ax.set_title(f"converged runs, refresh on rise {rr}", fontsize=9, color=INK)
    fig.suptitle("Robustness grid: runs that converge, over cases, recompute_every 10 and 5 (stall rule at default)", fontsize=9, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "robustness.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    traces()
    robustness()
