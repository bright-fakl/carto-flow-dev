"""Overview plots of the step-scale variants of the exploration-gsm-scale page.

Reads data/gsm_scale_tables.md (copy of exploration-gsm-scale/tables.md) and writes
overview_scorecard.png (cost relative to the baseline per case and variant),
overview_scatter.png (cost against invalid polygons per case) and
overview_summary.png (median cost ratio and number of converged cases per variant).
Cost = iterations + field recomputes x (recompute / step cost ratio of the case).
Runs with `uv run python make_overview.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm, TwoSlopeNorm

HERE = Path(__file__).resolve().parent
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"

CASES = [
    ("states grid 128", "states 128"), ("states grid 256", "states 256"), ("states grid 512", "states 512"),
    ("states_mr grid 128", "multires\ncoarse"), ("horiz grid 256", "horizontal"), ("tang grid 256", "tangential"),
    ("tilt grid 256", "tilted"), ("districts grid 256", "districts 256"), ("districts grid 512", "districts 512"),
    ("counties grid 256", "counties 256"), ("counties grid 512", "counties 512"),
]
# (exact variant name in the table, short id, family, description)
VARIANTS = [
    ("A constant", "A", "A", "baseline: constant scale, fastest point moves dt cells"),
    ("C3 A at B2-matched dt", "C3m", "C", "baseline with the dt that matches B2's mean displacement"),
    ("C3 A dt 0.6 (cap 1)", "C3 dt0.6", "C", "baseline with dt 0.6"),
    ("C3 A dt 1.0 (cap 1)", "C3 dt1.0", "C", "baseline with dt 1.0"),
    ("C4 dt_max 1.0 ref 10", "C4", "C", "step shrinks with the score, dt_max 1.0, no density pattern"),
    ("C1 physical, constant scale (cap 1)", "C1", "C", "physical magnitude, no density pattern"),
    ("C2 pattern at A's step, floor 0.02", "C2", "C", "GSM pattern at the baseline's mean step"),
    ("B1 gsm_normalized (floor 0.02)", "B1", "B", "GSM pattern, grid-max normalization"),
    ("B2 gsm_physical (cap 1 cell)", "B2", "B", "GSM pattern and physical magnitude"),
    ("B3 precomputed B2", "B3", "B", "B2 with the scale field precomputed per step"),
    ("B4ii integral physical (cap 1)", "B4ii", "B", "closed-form round integral, applied in sub-steps"),
    ("B4i one step per round (cap 3)", "B4i", "B", "closed-form round integral, one step per round (a recompute every iteration)"),
]
FAMILY_STYLE = {"A": ("o", "#0b0b0b"), "B": ("s", "#2a78d6"), "C": ("^", "#eb6834")}


def parse() -> dict:
    data: dict = {}
    case = None
    ratio = None
    for line in (HERE / "data" / "gsm_scale_tables.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"## (.+?)\s+\(ratio ([\d.]+)", line)
        if m:
            case, ratio = m.group(1).strip(), float(m.group(2))
            continue
        if line.startswith("## "):
            case = None
        if case is None or not line.startswith("| ") or line.startswith("| variant") or line.startswith("|---"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 12 or not c[3].replace(".", "").isdigit():
            continue
        data[(case, c[0], c[1])] = dict(status=c[2], it=int(c[3]), rec=int(c[4]), cost=int(c[3]) + int(c[4]) * ratio, invalid=int(c[10]))
    return data


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def scorecard(data: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"wspace": 0.04})
    cmap = plt.get_cmap("RdYlGn_r")
    for ax, refresh in zip(axes, ("off", "on")):
        grid = np.full((len(VARIANTS), len(CASES)), np.nan)
        text = [[""] * len(CASES) for _ in VARIANTS]
        failed = np.zeros_like(grid, dtype=bool)
        missing = np.zeros_like(grid, dtype=bool)
        for j, (case, _) in enumerate(CASES):
            base = data.get((case, "A constant", refresh))
            for i, (name, _, _, _) in enumerate(VARIANTS):
                r = data.get((case, name, refresh))
                if r is None:
                    missing[i, j] = True
                    text[i][j] = "not run"
                    continue
                if r["status"] != "converged":
                    failed[i, j] = True
                    text[i][j] = "stalled"
                elif base and base["status"] == "converged":
                    grid[i, j] = r["cost"] / base["cost"]
                    text[i][j] = f"{grid[i, j]:.2f}\n{r['invalid']} inv"
                else:
                    text[i][j] = f"{r['cost']:.0f}\n{r['invalid']} inv"
        norm = TwoSlopeNorm(vmin=0.2, vcenter=1.0, vmax=3.0)
        ax.imshow(np.where(np.isnan(grid), 1.0, grid), cmap=cmap, norm=norm, aspect="auto")
        for i in range(len(VARIANTS)):
            for j in range(len(CASES)):
                if missing[i, j]:
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="white", edgecolor="white"))
                if failed[i, j]:
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#cfcfca", edgecolor="white", hatch="///"))
                ax.text(j, i, text[i][j], ha="center", va="center", fontsize=6.5, color=INK)
        ax.set_xticks(range(len(CASES)), [c[1] for c in CASES], fontsize=7.5, color=INK, rotation=40, ha="right")
        ax.set_title(f"refresh on rise {refresh}: cost relative to the baseline A (green = cheaper)", fontsize=9, color=INK)
        if refresh == "off":
            ax.set_yticks(range(len(VARIANTS)), [f"{v[1]}  {v[3]}" for v in VARIANTS], fontsize=7.5, color=INK)
        else:
            ax.set_yticks([])
        ax.set_facecolor(SURFACE)
    fig.suptitle("Step-scale variants: cost relative to A (iterations + recomputes x ratio), invalid polygons below; hatched = did not converge, white = not run; multires coarse shows raw cost because A stalls there", fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "overview_scorecard.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def scatter(data: dict) -> None:
    fig, axes = plt.subplots(3, 4, figsize=(15, 9.5), gridspec_kw={"hspace": 0.4, "wspace": 0.25})
    for ax, (case, label) in zip(axes.ravel(), CASES):
        style(ax)
        for name, short, family, _ in VARIANTS:
            r = data.get((case, name, "on"))
            if r is None:
                continue
            marker, color = FAMILY_STYLE[family]
            filled = r["status"] == "converged"
            ax.scatter(r["cost"], r["invalid"], marker=marker, s=46, facecolors=color if filled else "none", edgecolors=color, linewidths=1.3)
            ax.annotate(short, (r["cost"], r["invalid"]), fontsize=6, color=MUTED, xytext=(3, 3), textcoords="offset points")
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=1)
        ax.set_title(label.replace("\n", " "), fontsize=9, color=INK)
        ax.grid(True, color=GRID, linewidth=0.7)
    ax = axes.ravel()[len(CASES)]
    ax.axis("off")
    for k, (fam, (marker, color)) in enumerate(FAMILY_STYLE.items()):
        ax.scatter([], [], marker=marker, color=color, label={"A": "A baseline", "B": "B: GSM scale variants", "C": "C: controls"}[fam])
    ax.scatter([], [], marker="o", facecolors="none", edgecolors=MUTED, label="hollow = did not converge")
    ax.legend(loc="center", frameon=False, fontsize=9)
    for ax in axes[-1]:
        ax.set_xlabel("cost (plain steps)", fontsize=8, color=MUTED)
    for ax in axes[:, 0]:
        ax.set_ylabel("invalid polygons", fontsize=8, color=MUTED)
    fig.suptitle("Cost against invalid polygons per case (refresh on rise on); lower left is better", fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "overview_scatter.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def summary(data: dict) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.6))
    style(ax)
    for i, (name, short, family, desc) in enumerate(VARIANTS):
        ratios, converged, total = [], 0, 0
        for case, _ in CASES:
            r, base = data.get((case, name, "on")), data.get((case, "A constant", "on"))
            if r is None:
                continue
            total += 1
            if r["status"] == "converged":
                converged += 1
                if base and base["status"] == "converged":
                    ratios.append(r["cost"] / base["cost"])
        marker, color = FAMILY_STYLE[family]
        if ratios:
            ax.scatter(np.median(ratios), len(VARIANTS) - 1 - i, marker=marker, s=40 + 14 * converged, color=color)
            ax.plot([min(ratios), max(ratios)], [len(VARIANTS) - 1 - i] * 2, color=color, linewidth=1, alpha=0.5)
        ax.text(3.3, len(VARIANTS) - 1 - i, f"{converged}/{total} converged", va="center", fontsize=8, color=MUTED)
    ax.axvline(1.0, color=INK, linestyle="--", linewidth=0.8)
    ax.set_xscale("log")
    ax.set_xlim(0.15, 6)
    ax.set_yticks(range(len(VARIANTS)), [f"{v[1]}  {v[3]}" for v in VARIANTS][::-1], fontsize=8, color=INK)
    ax.set_xlabel("cost relative to A over the cases where both converge (median, range; refresh on rise on)", fontsize=8, color=MUTED)
    ax.grid(True, axis="x", color=GRID, linewidth=0.7)
    ax.set_title("Median cost against the baseline and number of converged cases", fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "overview_summary.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    d = parse()
    scorecard(d)
    scatter(d)
    summary(d)
