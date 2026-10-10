"""Tables and figures of the Voronoi option screen, from data/runs.jsonl (written by run_experiments.py).

Writes options_scorecard_<ds>.png (every run against its base, per dataset), options_effects.png
(main effects on the states), options_anchor.png (generator anchor by base, all datasets),
options_spring.png (adjacency spring by base and anchor), options_tradeoff.png (recipes:
position fidelity against compactness, adjacency preservation as color) and prints markdown tables
(noise, effects, recipes) to stdout. Runs with `uv run python make_figures.py` (no carto-flow needed).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

HERE = Path(__file__).resolve().parent
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
BASE_COLOR = {"F": "#0b0b0b", "E": "#2a78d6", "P": "#eb6834"}
BASE_NAME = {"F": "F fixed outline", "E": "E elastic 0.05", "P": "P premorph (anchor 0.5)"}
DS_NAME = {"S": "states, population", "L": "states, lognormal 1.5", "D": "districts, population", "U": "states, unweighted"}

# metric: (label, direction (+1 = higher is better), format, scale for the color: change that saturates it)
METRICS = {
    "mean_err": ("area err %", -1, "{:.2f}", 0.5),
    "d_flow_med": ("offset vs flow (R)", -1, "{:.2f}", 0.3),
    "d_flow_max": ("max offset vs flow (R)", -1, "{:.2f}", 1.0),
    "d_orig_med": ("offset vs orig (R)", -1, "{:.2f}", 0.4),
    "procrustes": ("Procrustes", -1, "{:.3f}", 0.05),
    "adj_kept": ("adjacency kept", 1, "{:.2f}", 0.1),
    "adj_new": ("new adjacencies", -1, "{:.0f}", None),
    "compact": ("compactness", 1, "{:.2f}", 0.05),
    "lag_med": ("lag (own R)", -1, "{:.2f}", 0.2),
    "split": ("split cells", -1, "{:.0f}", 4.0),
    "outline_vs_flow": ("outline vs flow", -1, "{:.2f}", 0.2),
    "tx_own": ("TX own region", 1, "{:.2f}", 0.15),
    "it": ("iterations", -1, "{:.0f}", None),
    "time": ("time (s)", -1, "{:.1f}", None),
}
CARD = ["mean_err", "d_flow_med", "d_orig_med", "adj_kept", "adj_new", "compact", "lag_med", "split",
        "outline_vs_flow", "tx_own", "it", "time"]
EFFECTS = ["d_flow_med", "adj_kept", "compact", "lag_med", "split", "time"]


def load():
    rows = [json.loads(line) for line in (HERE / "data" / "runs.jsonl").read_text().splitlines()]
    return [r for r in rows if "error" not in r], [r for r in rows if "error" in r]


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=7)


def base_means(rows):
    """Mean over the repeated base runs, per (dataset, base)."""
    acc = defaultdict(list)
    for r in rows:
        if r["factor"] == "base":
            acc[(r["ds"], r["base"])].append(r)
    return {k: {m: float(np.mean([x[m] for x in v])) for m in METRICS} for k, v in acc.items()}


def noise(rows):
    """Run-to-run range of each metric over repeated base runs (max over dataset and base)."""
    acc = defaultdict(list)
    for r in rows:
        if r["factor"] == "base":
            acc[(r["ds"], r["base"])].append(r)
    out = {}
    print("\n### Noise (range over repeated base runs)\n")
    print("| dataset | base | runs | " + " | ".join(METRICS[m][0] for m in CARD) + " |")
    print("|---|---|---|" + "---|" * len(CARD))
    for (ds, base), v in sorted(acc.items()):
        if len(v) < 2:
            continue
        rng = {m: float(np.ptp([x[m] for x in v])) for m in METRICS}
        for m in METRICS:
            out[m] = max(out.get(m, 0.0), rng[m])
        print(f"| {ds} | {base} | {len(v)} | " + " | ".join(METRICS[m][2].format(rng[m]) if m != "time" else f"{rng[m]:.1f}" for m in CARD) + " |")
    return out


def rel(m, x, ref):
    """Signed improvement of x over ref, scaled to about [-1, 1] (positive = better)."""
    _, direction, _, scale = METRICS[m]
    if scale is None:  # counts, iterations, time and error: log ratio
        return direction * np.log2((x + 1e-3) / (ref + 1e-3)) / 2.0
    return direction * (x - ref) / scale


def label(r):
    return f"{r['base']}  {r['factor']} = {r['level']}" if r["factor"] != "base" else f"{r['base']}  base ({BASE_NAME[r['base']]})"


def scorecard(rows, bases, ds):
    sel = [r for r in rows if r["ds"] == ds and r["rep"] == 0]
    sel.sort(key=lambda r: ("FEP".index(r["base"]), r["factor"] != "base", r["factor"], r["level"]))
    metrics = [m for m in CARD if not (m == "tx_own" and ds == "U")]
    grid = np.zeros((len(sel), len(metrics)))
    text = [[""] * len(metrics) for _ in sel]
    for i, r in enumerate(sel):
        ref = bases[(ds, r["base"])]
        for j, m in enumerate(metrics):
            grid[i, j] = 0.0 if r["factor"] == "base" else rel(m, r[m], ref[m])
            text[i][j] = METRICS[m][2].format(r[m])
        if r["mean_err"] > 1.0:
            text[i][0] += "!"
    fig, ax = plt.subplots(figsize=(1.0 * len(metrics) + 4, 0.22 * len(sel) + 1.6))
    ax.imshow(np.clip(grid, -1, 1), cmap="RdYlGn", norm=TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1), aspect="auto")
    for i in range(len(sel)):
        for j in range(len(metrics)):
            ax.text(j, i, text[i][j], ha="center", va="center", fontsize=5.8, color=INK)
        if i and sel[i]["base"] != sel[i - 1]["base"]:
            ax.axhline(i - 0.5, color=INK, lw=1.2)
    ax.set_xticks(range(len(metrics)), [METRICS[m][0] for m in metrics], fontsize=7, rotation=35, ha="right", color=INK)
    ax.set_yticks(range(len(sel)), [label(r) for r in sel], fontsize=6.5, color=INK)
    ax.xaxis.tick_top()
    ax.set_title(f"{DS_NAME[ds]}: each run against its base (green = better, red = worse; saturates at one scale unit); "
                 "values are the run's own; ! = area error above 1 %", fontsize=8, color=INK, pad=60)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / f"options_scorecard_{ds}.png", dpi=130, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def effects(rows, bases, noise_range, ds="S"):
    """Dot plot of each factor level's change against its base, per metric; shaded band = noise range."""
    sel = [r for r in rows if r["ds"] == ds and r["factor"] != "base" and " x " not in r["factor"]]
    levels = sorted({(r["factor"], r["level"]) for r in sel})
    fig, axes = plt.subplots(1, len(EFFECTS), figsize=(3.0 * len(EFFECTS) + 2.5, 0.24 * len(levels) + 1.5), sharey=True)
    for ax, m in zip(axes, EFFECTS, strict=True):
        style(ax)
        band = noise_range.get(m, 0.0)
        ax.axvspan(-band, band, color=GRID, zorder=0)
        ax.axvline(0, color=MUTED, lw=0.8)
        for r in sel:
            y = levels.index((r["factor"], r["level"]))
            d = r[m] - bases[(ds, r["base"])][m]
            ax.plot(d, y, "o", ms=4, color=BASE_COLOR[r["base"]], alpha=0.9)
        ax.set_title(f"Δ {METRICS[m][0]}" + (" (higher better)" if METRICS[m][1] > 0 else " (lower better)"), fontsize=7.5, color=INK)
        ax.grid(axis="x", color=GRID, lw=0.6)
    axes[0].set_yticks(range(len(levels)), [f"{f} = {lv}" for f, lv in levels], fontsize=7, color=INK)
    axes[0].invert_yaxis()
    for b, c in BASE_COLOR.items():
        axes[-1].plot([], [], "o", color=c, label=BASE_NAME[b])
    axes[-1].legend(fontsize=7, frameon=False, loc="lower right")
    fig.suptitle(f"{DS_NAME[ds]}: change of each metric against the base run (gray band = run-to-run range of repeated base runs)",
                 fontsize=9, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "options_effects.png", dpi=130, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def anchor_plot(rows, bases):
    """Interaction anchor x base: metric against the anchor, one line per base, one column per dataset."""
    ms = ["d_flow_med", "adj_kept", "compact", "lag_med"]
    dss = ["S", "L", "D", "U"]
    fig, axes = plt.subplots(len(ms), len(dss), figsize=(13, 9.5), sharex=True)
    for j, ds in enumerate(dss):
        for i, m in enumerate(ms):
            ax = axes[i, j]
            style(ax)
            for b in "FEP":
                pts, bad = {}, {}
                for r in rows:
                    if r["ds"] == ds and r["base"] == b and r["rep"] == 0 and r["factor"] == "anchor":
                        if r["mean_err"] > 1.0:  # failed solve: collapsed cells; shown as a cross, not joined
                            bad[float(r["level"])] = r[m] if np.isfinite(r[m]) else 0.0
                        else:
                            pts[float(r["level"])] = r[m]
                for x, y in bad.items():
                    ax.plot(x, y, "x", ms=9, mew=2, color="#c0392b")
                if (ds, b) in bases:
                    pts.setdefault(0.5 if b == "P" else 0.0, bases[(ds, b)][m])
                if len(pts) < 2:
                    if pts:
                        ax.plot(list(pts), list(pts.values()), "o", color=BASE_COLOR[b])
                    continue
                xs = sorted(pts)
                ax.plot(xs, [pts[x] for x in xs], "-o", ms=4, lw=1.8, color=BASE_COLOR[b], label=BASE_NAME[b].split(" (")[0])
            ax.grid(color=GRID, lw=0.6)
            if i == 0:
                ax.set_title(DS_NAME[ds], fontsize=8.5, color=INK)
            if j == 0:
                ax.set_ylabel(METRICS[m][0], fontsize=8, color=MUTED)
            if i == len(ms) - 1:
                ax.set_xlabel("generator_anchor", fontsize=8, color=MUTED)
    axes[0, 0].legend(fontsize=7, frameon=False)
    fig.suptitle("Generator anchor by base: F fixed outline, E elastic 0.05, P premorph; red cross = failed area solve "
                 "(cells collapsed, mean area error above 1 %; F with anchor 0.5 and 1 on L and D, and on U)", fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "options_anchor.png", dpi=130, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def spring_plot(rows, bases):
    """Adjacency spring by base (lines) on S and L, plus the anchor x spring grid on P."""
    ms = ["adj_kept", "adj_new", "d_flow_med", "compact"]
    fig, axes = plt.subplots(2, len(ms), figsize=(14, 6.5))
    for i, ds in enumerate(("S", "L")):
        for j, m in enumerate(ms):
            ax = axes[i, j]
            style(ax)
            for b in "FEP":
                pts = {0.0: bases[(ds, b)][m]}
                for r in rows:
                    if r["ds"] == ds and r["base"] == b and r["factor"] == "adjacency_spring":
                        pts[float(r["level"])] = r[m]
                xs = sorted(pts)
                ax.plot(xs, [pts[x] for x in xs], "-o", ms=4, lw=1.8, color=BASE_COLOR[b], label=BASE_NAME[b])
            # premorph with anchor 0 and 1 (pairs)
            for a, ls in ((0.0, ":"), (1.0, "--")):
                pts = {}
                for r in rows:
                    if r["ds"] != ds or r["base"] != "P" or r["rep"]:
                        continue
                    s = r["settings"]
                    if s.get("anchor") == a and r["factor"] in ("anchor", "anchor x spring"):
                        pts[float(s.get("spring", 0.0))] = r[m]
                if len(pts) > 1:
                    xs = sorted(pts)
                    ax.plot(xs, [pts[x] for x in xs], ls, marker="s", ms=3, lw=1.3, color=BASE_COLOR["P"], label=f"P with anchor {a:g}")
            ax.grid(color=GRID, lw=0.6)
            ax.set_title(f"{DS_NAME[ds]}: {METRICS[m][0]}", fontsize=8, color=INK)
            if i == 1:
                ax.set_xlabel("adjacency_spring", fontsize=8, color=MUTED)
    axes[0, 0].legend(fontsize=6.5, frameon=False)
    fig.suptitle("Adjacency spring by base, and against the anchor on the premorph base", fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "options_spring.png", dpi=130, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


RECIPES = [
    # (short name, description, (base, factor, level))
    ("fixed", "fixed outline (current weighted default)", ("F", "base", "base")),
    ("fixed+spring", "fixed outline, adjacency_spring 0.2", ("F", "adjacency_spring", "0.2")),
    ("fast", "fixed outline, resolution 128", ("F", "resolution", "128")),
    ("circle", "circle outline", ("F", "boundary", "circle")),
    ("elastic", "ElasticBoundary(0.05)", ("E", "base", "base")),
    ("elastic+anchor", "ElasticBoundary(0.05), anchor 0.5", ("E", "anchor", "0.5")),
    ("premorph a0", "premorph, anchor 0", ("P", "anchor", "0")),
    ("premorph a0.25", "premorph, anchor 0.25", ("P", "anchor", "0.25")),
    ("premorph a0.5", "premorph, anchor 0.5 (premorph=True)", ("P", "base", "base")),
    ("premorph a1", "premorph, anchor 1 (generators fixed)", ("P", "anchor", "1")),
    ("premorph+spring", "premorph, anchor 0.5, spring 0.2", ("P", "adjacency_spring", "0.2")),
    ("premorph+elastic", "premorph, ElasticBoundary(0.02), anchor 0.5", ("P", "boundary", "elastic 0.02")),
]


def find(rows, ds, key):
    b, f, lv = key
    for r in rows:
        if r["ds"] == ds and r["base"] == b and r["factor"] == f and r["level"] == lv and r["rep"] == 0:
            return r
    return None


def tradeoff(rows):
    dss = ["S", "L", "D", "U"]
    fig, axes = plt.subplots(1, len(dss), figsize=(18, 4.8))
    cmap = plt.get_cmap("viridis")
    for ax, ds in zip(axes, dss, strict=True):
        style(ax)
        pts = [(name, find(rows, ds, key)) for name, _, key in RECIPES]
        pts = [(n, r) for n, r in pts if r is not None]
        kept = np.array([r["adj_kept"] for _, r in pts])
        lo, hi = kept.min(), max(kept.max(), kept.min() + 1e-6)
        for name, r in pts:
            ax.scatter(r["d_flow_med"], r["compact"], s=30 + 10 * r["time"], color=cmap((r["adj_kept"] - lo) / (hi - lo)),
                       edgecolors=INK, linewidths=0.5, zorder=3)
            ax.annotate(name, (r["d_flow_med"], r["compact"]), fontsize=6.5, color=MUTED, xytext=(4, 3), textcoords="offset points")
        ax.set_title(f"{DS_NAME[ds]} (color: adjacency kept {lo:.2f} to {hi:.2f})", fontsize=8, color=INK)
        ax.set_xlabel("offset vs flow cartogram (R, median; left = more faithful)", fontsize=7.5, color=MUTED)
        ax.grid(color=GRID, lw=0.6)
    axes[0].set_ylabel("compactness (up = rounder cells)", fontsize=8, color=MUTED)
    fig.suptitle("Recipes: position fidelity against compactness; marker color = share of input adjacencies kept "
                 "(yellow = most), marker size = wall time", fontsize=10, color=INK)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(HERE / "options_tradeoff.png", dpi=130, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def recipe_table(rows):
    print("\n### Recipes\n")
    cols = ["mean_err", "d_flow_med", "d_orig_med", "adj_kept", "adj_new", "compact", "lag_med", "split", "outline_vs_flow", "tx_own", "it", "time"]
    print("| dataset | recipe | " + " | ".join(METRICS[m][0] for m in cols) + " | converged | warnings |")
    print("|---|---|" + "---|" * (len(cols) + 2))
    for ds in "SLDU":
        for name, _, key in RECIPES:
            r = find(rows, ds, key)
            if r is None:
                continue
            print(f"| {ds} | {name} | " + " | ".join(METRICS[m][2].format(r[m]) for m in cols) + f" | {r['converged']} | {len(r['warnings'])} |")


def all_runs_table(rows):
    print("\n### All runs\n")
    cols = ["mean_err", "d_flow_med", "d_flow_max", "d_orig_med", "procrustes", "adj_kept", "adj_new", "compact", "lag_med", "split",
            "outline_vs_flow", "tx_own", "it", "time"]
    print("| ds | base | factor | level | rep | " + " | ".join(METRICS[m][0] for m in cols) + " | inv | conv | warnings |")
    print("|---|---|---|---|---|" + "---|" * (len(cols) + 3))
    for r in sorted(rows, key=lambda r: ("SLDU".index(r["ds"]), "FEP".index(r["base"]), r["factor"] != "base", r["factor"], r["level"], r["rep"])):
        w = "; ".join(sorted({x.split(":")[0] + ": " + x.split(":", 1)[1][:45] for x in r["warnings"]}))
        print(f"| {r['ds']} | {r['base']} | {r['factor']} | {r['level']} | {r['rep']} | "
              + " | ".join(METRICS[m][2].format(r[m]) for m in cols) + f" | {r['invalid']} | {r['converged']} | {w} |")


def main():
    rows, failed = load()
    bases = base_means(rows)
    noise_range = noise(rows)
    for ds in "SLDU":
        if any(r["ds"] == ds for r in rows):
            scorecard(rows, bases, ds)
    effects(rows, bases, noise_range)
    anchor_plot(rows, bases)
    spring_plot(rows, bases)
    tradeoff(rows)
    recipe_table(rows)
    all_runs_table(rows)
    if failed:
        print("\n### Failed runs\n")
        for r in failed:
            print(f"- {r['ds']} {r['base']} {r['factor']} = {r['level']}: {r['error']}")


if __name__ == "__main__":
    main()
