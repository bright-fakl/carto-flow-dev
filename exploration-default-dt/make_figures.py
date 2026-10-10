"""Figures for the default-dt exploration. Reads data/*.jsonl (written by scripts/run_sweep.py and scripts/run_extra.py)
and data/shape.json (scripts/shape_compare.py); writes the PNGs next to this file. Run with `python make_figures.py`
(matplotlib and numpy only). The score is max(mean/mean_tol, max/max_tol) on the log2 errors; below 1 is converged."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
DTS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.8]
COLOR = {0.2: "#2a78d6", 0.3: "#1baf7a", 0.4: "#eda100", 0.5: "#eb6834", 0.6: "#e87ba4", 0.8: "#7a5bd6"}
RATIO = {("states", 128): 9, ("states", 256): 12, ("states", 512): 24, ("states", 1024): 71,
         ("districts", 128): 18, ("districts", 256): 21, ("districts", 512): 23, ("districts", 1024): 47,
         ("counties", 128): 21, ("counties", 256): 47.5, ("counties", 512): 28.5}
BASE = {"horiz": "states", "tang": "states", "tilt": "states", "states_mr": "states"}


def load_runs() -> dict:
    runs = {}
    for f in sorted(DATA.glob("*.jsonl")):
        if f.stem in ("pipeline", "presets", "landmarks"):
            continue
        for line in f.read_text().splitlines():
            r = json.loads(line)
            ratio = RATIO.get((BASE.get(r["case"], r["case"]), r["grid"]))
            r["cost"] = None if ratio is None else r["it"] + r["rec"] * ratio
            runs[(r["case"], r["grid"], r["dt"], r["rr"], r["rre"], r["tight"])] = r
    return runs


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def traces(ax, runs, case, grid, rr=0.01, tight=False, rre=10) -> None:
    style_axes(ax)
    for dt in DTS:
        r = runs.get((case, grid, dt, rr, rre, tight))
        if r is None:
            continue
        s = np.asarray(r["score"])
        ax.plot(np.arange(len(s)), s, color=COLOR[dt], linewidth=3.0 if dt == 0.2 else 1.4, alpha=0.65 if dt == 0.2 else 1.0,
                label=f"dt {dt}: {r['it']} it, {r['rec']} rec" + ("" if r["stop"] == "converged" else " (not conv.)"))
    ax.axhline(1.0, color=INK, linestyle="--", linewidth=0.8)
    ax.set_yscale("log")
    ax.legend(fontsize=6.5, frameon=False, labelcolor=INK, loc="upper right")


def grid_figure(items, nrows, ncols, title, path, figsize) -> None:
    runs = load_runs()
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, gridspec_kw={"hspace": 0.34, "wspace": 0.2})
    for ax, (case, grid, name, rr, tight) in zip(axes.ravel(), items):
        traces(ax, runs, case, grid, rr=rr, tight=tight)
        ax.set_title(name, fontsize=9, color=INK)
        ax.set_xlabel("iteration", fontsize=8, color=MUTED)
    for ax in axes[:, 0]:
        ax.set_ylabel("score (below 1 is converged)", fontsize=8, color=MUTED)
    fig.suptitle(title, fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(path, dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def scorecard() -> None:
    runs = load_runs()
    pipe = {}
    for line in (DATA / "pipeline.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["rr"] == 0.01:
            pipe[(r["case"], r["dt"])] = r
    cols = [("states", 128, "states\n128", False), ("states", 256, "states\n256", False), ("states", 512, "states\n512", False),
            ("states", 1024, "states\n1024", False), ("districts", 256, "districts\n256", False), ("districts", 512, "districts\n512", False),
            ("horiz", 256, "horizontal\naniso.", False), ("tang", 256, "tangential\naniso.", False), ("tilt", 256, "tilted\naniso.", False),
            ("states_mr", 128, "multires\ncoarse", False), ("counties", 256, "counties\n256", False),
            ("states", 256, "states 256\ntight tol.", True), ("districts", 256, "districts 256\ntight tol.", True),
            ("pipe-states", 0, "pipeline\nstates", False), ("pipe-districts", 0, "pipeline\ndistricts", False)]

    def get(case, grid, dt, tight):
        if case.startswith("pipe-"):
            r = pipe.get((case[5:], dt))
            if r is None:
                return None
            ok = all(l["status"] == "converged" for l in r["levels"][-1:])
            return dict(cost=r["cost"], invalid=r["invalid"], ok=ok)
        r = runs.get((case, grid, dt, 0.01, 10, tight))
        if r is None:
            return None
        return dict(cost=r["cost"], invalid=r["invalid"], ok=r["stop"] == "converged")

    fig, ax = plt.subplots(figsize=(13.5, 4.6))
    cmap = matplotlib.colormaps["RdYlGn_r"]
    for j, (case, grid, name, tight) in enumerate(cols):
        ref = get(case, grid, 0.2, tight)
        for i, dt in enumerate(DTS):
            r = get(case, grid, dt, tight)
            if r is None or ref is None:
                continue
            rel = r["cost"] / ref["cost"]
            color = cmap(np.clip((math.log2(rel) + 1.2) / 2.4, 0, 1)) if r["ok"] else "#d8d7d2"
            ax.add_patch(mpatches.Rectangle((j, i), 1, 1, facecolor=color, edgecolor=SURFACE, linewidth=2,
                                            hatch=None if r["ok"] else "////"))
            ax.text(j + 0.5, i + 0.4, f"{rel:.2f}x", ha="center", va="center", fontsize=8.5, color=INK, fontweight="bold")
            ax.text(j + 0.5, i + 0.72, f"{r['invalid']} inv.", ha="center", va="center", fontsize=6.8, color=INK)
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(DTS), 0)
    ax.set_xticks([j + 0.5 for j in range(len(cols))])
    ax.set_xticklabels([c[2] for c in cols], fontsize=7.5, color=INK)
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(DTS))])
    ax.set_yticklabels([f"dt {dt}" for dt in DTS], fontsize=9, color=INK)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    fig.suptitle("Cost relative to dt 0.2 (iterations + recomputes x ratio; pipeline: summed over levels), invalid polygons below; "
                 "hatched = did not converge (pipeline: last level)", fontsize=9, color=INK, y=0.03)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    fig.savefig(HERE / "scorecard.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def scatter() -> None:
    runs = load_runs()
    fams = [("states", "o", "states 128 to 512"), ("districts", "s", "districts 256, 512"), ("aniso", "^", "anisotropy 256"),
            ("tight", "D", "tight tolerances 256")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"wspace": 0.2})
    for ax, (ylab, yfun, ylog) in zip(axes, [("invalid polygons", lambda r, r0: r["invalid"], True),
                                              ("extra invalid polygons against dt 0.2", lambda r, r0: r["invalid"] - r0["invalid"], False)]):
        style_axes(ax)
        for fam, marker, label in fams:
            if fam == "states":
                keys = [("states", g, False) for g in (128, 256, 512)]
            elif fam == "districts":
                keys = [("districts", g, False) for g in (256, 512)]
            elif fam == "aniso":
                keys = [(c, 256, False) for c in ("horiz", "tang", "tilt")]
            else:
                keys = [("states", 256, True), ("districts", 256, True)]
            for case, grid, tight in keys:
                r0 = runs.get((case, grid, 0.2, 0.01, 10, tight))
                for dt in DTS:
                    r = runs.get((case, grid, dt, 0.01, 10, tight))
                    if r is None or r0 is None:
                        continue
                    ok = r["stop"] == "converged"
                    ax.scatter(r["cost"] / r0["cost"], yfun(r, r0), marker=marker, s=34,
                               facecolor=COLOR[dt] if ok else "none", edgecolor=COLOR[dt], linewidth=1.3, alpha=0.9)
        ax.set_xscale("log")
        ax.set_xticks([0.4, 0.6, 0.8, 1, 1.5, 2, 3])
        ax.set_xticklabels(["0.4", "0.6", "0.8", "1", "1.5", "2", "3"])
        if ylog:
            ax.set_yscale("symlog", linthresh=1)
            ax.set_ylim(-0.3, 250)
            ax.set_yticks([0, 1, 3, 10, 30, 100])
            ax.set_yticklabels(["0", "1", "3", "10", "30", "100"])
        ax.axvline(1, color=INK, linewidth=0.6, linestyle=":")
        ax.set_xlabel("cost relative to dt 0.2 of the same case", fontsize=8, color=MUTED)
        ax.set_ylabel(ylab, fontsize=8, color=MUTED)
    handles = [plt.Line2D([], [], marker="o", linestyle="", color=COLOR[dt], label=f"dt {dt}") for dt in DTS]
    handles += [plt.Line2D([], [], marker=m, linestyle="", color=MUTED, label=l) for _, m, l in fams]
    handles += [plt.Line2D([], [], marker="o", linestyle="", markerfacecolor="none", color=MUTED, label="not converged")]
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, fontsize=8, labelcolor=INK)
    fig.subplots_adjust(bottom=0.2)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "cost_vs_invalid.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def landmarks_and_shape() -> None:
    rows = [json.loads(l) for l in (DATA / "landmarks.jsonl").read_text().splitlines()]
    shape = json.loads((DATA / "shape.json").read_text())
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), gridspec_kw={"wspace": 0.28})
    ax = axes[0]
    style_axes(ax)
    combos = sorted({(r["dt"], r["rre"]) for r in rows if r["seed"] == 7 or True})
    for dt, rre in combos:
        zs = [r["z"] for r in rows if (r["dt"], r["rre"]) == (dt, rre)]
        if len(zs) < 5:
            continue
        x = dt * rre
        ax.scatter([x] * len(zs), zs, s=10, color=COLOR.get(dt, MUTED), alpha=0.35)
        ax.scatter([x], [np.mean(zs)], s=40, color=COLOR.get(dt, "#0b0b0b"), edgecolor=INK, linewidth=0.7, zorder=3)
        ax.annotate(f"{dt}, {rre}", (x, np.mean(zs)), textcoords="offset points", xytext=(4, -9), fontsize=6.5, color=MUTED)
    ax.axhline(0.27, color=INK, linestyle="--", linewidth=0.8)
    ax.text(0.05, 0.5, "start of the morph", fontsize=7, color=MUTED)
    ax.set_xlabel("dt x recompute_every (nominal cells moved per field)", fontsize=8, color=MUTED)
    ax.set_ylabel("border-band z at the end (5 dot seeds)", fontsize=8, color=MUTED)
    ax.set_title("Landmark border drift (issue 86)", fontsize=9, color=INK)
    # shape change vs dt for default-tolerance runs
    for k, (key, ylab, title) in enumerate([("symdiff", "symmetric difference, % of total area", "Final shape against dt 0.2"),
                                           ("cent_gt05", "regions with centroid shift > 0.5 cell, % of regions", "Centroid shifts against dt 0.2")]):
        ax = axes[k + 1]
        style_axes(ax)
        for case, grid, label, mark, n in [("states", 256, "states 256", "o", 49), ("districts", 256, "districts 256", "s", 432),
                                           ("horiz", 256, "horizontal", "^", 49), ("tang", 256, "tangential", "v", 49), ("tilt", 256, "tilted", "<", 49)]:
            pts = sorted((float(kk.split("|")[2]), (100 * v[key] if key == "symdiff" else 100 * v[key] / n)) for kk, v in shape.items()
                         if kk.startswith(f"{case}|{grid}|") and kk.endswith("|0.01|10|0"))
            pts = [(0.2, 0.0)] + pts
            ax.plot(*zip(*pts), marker=mark, markersize=4, linewidth=1.2, label=label)
        ax.set_xlabel("dt", fontsize=8, color=MUTED)
        ax.set_ylabel(ylab, fontsize=8, color=MUTED)
        ax.set_title(title, fontsize=9, color=INK)
        ax.legend(fontsize=7, frameon=False, labelcolor=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "landmarks_and_shape.png", dpi=140, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    grid_figure([("states", 128, "states, grid 128", 0.01, False), ("states", 256, "states, grid 256", 0.01, False),
                 ("states", 512, "states, grid 512", 0.01, False), ("states_mr", 128, "multiresolution coarse level (states)", 0.01, False)],
                2, 2, "US states, refresh_on_rise 0.01, recompute_every 10: score per iteration (thick: dt 0.2)", HERE / "convergence_states.png", (11, 7.4))
    grid_figure([("districts", 256, "districts, grid 256", 0.01, False), ("districts", 512, "districts, grid 512", 0.01, False),
                 ("horiz", 256, "states, horizontal anisotropy", 0.01, False), ("tang", 256, "states, tangential anisotropy", 0.01, False),
                 ("tilt", 256, "states, tilted anisotropy", 0.01, False), ("counties", 256, "counties, grid 256 (stall rule on)", 0.01, False)],
                2, 3, "Districts, anisotropy and counties, refresh_on_rise 0.01: score per iteration", HERE / "convergence_districts_aniso.png", (15, 7.4))
    grid_figure([("states", 256, "states 256, tight tolerances (0.5 % / 1 %)", 0.01, True), ("districts", 256, "districts 256, tight tolerances", 0.01, True),
                 ("states", 256, "states 256, tight, refresh_on_rise off", None, True), ("states", 256, "states 256, defaults, refresh_on_rise off", None, False)],
                2, 2, "Tight tolerances: larger steps oscillate near the end (score per iteration)", HERE / "convergence_tight.png", (11, 7.4))
    scorecard()
    scatter()
    landmarks_and_shape()
