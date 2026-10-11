"""Figures and tables for the follow-up page from data/runs.jsonl and data/cells/*.pkl.

Run from a carto-flow checkout (bundled data only):
    uv run python make_figures.py
"""

from __future__ import annotations

import gzip
import json
import pickle
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely

import carto_flow.data as examples

HERE = Path(__file__).resolve().parent
ROWS = [json.loads(line) for line in (HERE / "data" / "runs.jsonl").read_text().splitlines()]
BASE_NAMES = {"F": "fixed outline", "E": "elastic boundary", "P": "premorph"}


def row(ds, base, factor, level):
    return next(r for r in ROWS if (r["ds"], r["base"], r["factor"], r["level"]) == (ds, base, factor, level))


def cells(ds, base, factor, level):
    key = f"{ds}_{base}_{factor}_{level}".replace(" ", "_").replace("+", "p")
    return shapely.from_wkb(pickle.loads(gzip.open(HERE / "data" / "cells" / f"{key}.pkl.gz").read())["cells"])


def draw(ax, geoms, colors, edge="white", lw=0.3):
    gpd.GeoSeries(list(geoms)).plot(ax=ax, color=colors, edgecolor=edge, linewidth=lw)
    ax.set_axis_off()
    ax.set_aspect("equal")


def prescale():
    states = examples.load_us_census(population=True, contiguous_only=False)
    ab = states["State Abbreviation"].to_numpy()
    colors = ["#d62728" if a in ("AK", "HI") else "#9ecae1" for a in ab]
    layout = [("F", "off"), ("F", "on"), ("E", "off"), ("E", "on"), ("P", "off"), ("P", "on")]
    fig, axes = plt.subplots(3, 2, figsize=(10, 11))
    for ax, (base, level) in zip(axes.ravel(), layout, strict=True):
        r = row("A", base, "prescale", level)
        draw(ax, cells("A", base, "prescale", level), colors)
        ax.set_title(
            f"{BASE_NAMES[base]}, prescale_components {level}\n"
            f"{r['it']} iterations, mean area error {r['mean_err']:.2f} %, AK x{r['AK_area_ratio']:.2f}, HI x{r['HI_area_ratio']:.2f}",
            fontsize=9,
        )
    fig.suptitle("50 states with Alaska and Hawaii (red), population weights: cell area / target area in the titles", fontsize=11)
    fig.tight_layout()
    fig.savefig(HERE / "followup_prescale.png", dpi=110)
    plt.close(fig)


def anchor():
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.2))
    states = examples.load_us_census(population=True)
    ab = states["State Abbreviation"].to_numpy()
    palette = {"TX": "#d62728", "LA": "#ff7f0e", "AR": "#2ca02c", "OK": "#9467bd", "NM": "#8c564b"}
    colors = [palette.get(a, "#c6dbef") for a in ab]
    for j, level in enumerate(["0", "0.25", "0.5"]):
        r = row("S", "P", "anchor", level)
        draw(axes[0, j], cells("S", "P", "anchor", level), colors)
        axes[0, j].set_title(
            f"states, premorph, anchor {level}\nTexas inside its morphed region {r['tx_own']:.2f}, Louisiana shift {r['LA_shift']:.2f}\n"
            f"adjacency kept {r['adj_kept']:.2f}, compactness {r['compact']:.2f}",
            fontsize=8,
        )
    districts = examples.load_us_census(population=True, level="congressional_district")
    lab = districts["State Name"].to_numpy()
    cmap = plt.get_cmap("tab20")
    uniq = {s: cmap(i % 20) for i, s in enumerate(np.unique(lab))}
    for j, level in enumerate(["0", "0.25", "0.5"]):
        r = row("D", "P", "anchor", level)
        draw(axes[1, j], cells("D", "P", "anchor", level), [uniq[s] for s in lab], lw=0.1)
        axes[1, j].set_title(
            f"districts, premorph, anchor {level}\nsplit cells {r['split']}, adjacency kept {r['adj_kept']:.2f}, compactness {r['compact']:.2f}",
            fontsize=8,
        )
    fig.tight_layout()
    fig.savefig(HERE / "followup_anchor.png", dpi=110)
    plt.close(fig)


def groups():
    districts = examples.load_us_census(population=True, level="congressional_district")
    lab = districts["State Name"].to_numpy()
    cmap = plt.get_cmap("tab20")
    uniq = {s: cmap(i % 20) for i, s in enumerate(np.unique(lab))}
    colors = [uniq[s] for s in lab]
    levels = ["off", "0.25", "0.5", "1"]
    fig, axes = plt.subplots(3, 4, figsize=(15, 10))
    for i, base in enumerate("FEP"):
        for j, level in enumerate(levels):
            r = row("D", base, "intra_group_spring", level)
            draw(axes[i, j], cells("D", base, "intra_group_spring", level), colors, lw=0.1)
            axes[i, j].set_title(
                f"{BASE_NAMES[base]}, intra_group_spring {level}\nstates whole {r['groups_whole']:.2f}, within-state adjacency {r['adj_within']:.2f}",
                fontsize=8,
            )
    fig.tight_layout()
    fig.savefig(HERE / "followup_groups.png", dpi=110)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    names = ["off", "0.25", "0.5", "1", "0.5 + adj 0.1"]
    for ax, key, title in zip(axes, ["groups_whole", "adj_within", "adj_between"], ["states whole", "within-state adjacency kept", "between-state adjacency kept"], strict=True):
        for base, color in zip("FEP", ["#1f77b4", "#ff7f0e", "#2ca02c"], strict=True):
            ys = [row("D", base, "intra_group_spring", n)[key] for n in names]
            ax.plot(names, ys, "o-", color=color, label=BASE_NAMES[base])
        ax.set_title(title, fontsize=10)
        ax.tick_params(axis="x", labelrotation=30, labelsize=8)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "followup_groups_metrics.png", dpi=110)
    plt.close(fig)


def tables():
    out = []
    out.append("| base | prescale | iterations | converged | mean error % | max error % | AK area / target | HI area / target | adjacency kept | time s |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in ROWS:
        if r["factor"] == "prescale":
            out.append(
                f"| {r['base']} | {r['level']} | {r['it']} | {r['converged']} | {r['mean_err']:.2f} | {r['max_err']:.1f} | "
                f"{r['AK_area_ratio']:.2f} | {r['HI_area_ratio']:.2f} | {r['adj_kept']:.2f} | {r['time']:.1f} |"
            )
    out.append("")
    out.append("| data | anchor | iterations | TX inside morphed region | TX shift | LA shift | split cells | adjacency kept | compactness | d_flow | time s |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in ROWS:
        if r["factor"] == "anchor":
            out.append(
                f"| {r['ds']} | {r['level']} | {r['it']} | {r.get('tx_own', float('nan')):.2f} | {r.get('TX_shift', float('nan')):.2f} | "
                f"{r.get('LA_shift', float('nan')):.2f} | {r['split']} | {r['adj_kept']:.2f} | {r['compact']:.2f} | {r['d_flow_med']:.2f} | {r['time']:.1f} |"
            )
    out.append("")
    out.append("| base | setting | iterations | states whole | within-state adj | between-state adj | all adj kept | compactness | time s |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in ROWS:
        if r["factor"] in ("intra_group_spring", "adjacency_spring"):
            out.append(
                f"| {r['base']} | {r['factor']} {r['level']} | {r['it']} | {r['groups_whole']:.2f} | {r['adj_within']:.2f} | "
                f"{r['adj_between']:.2f} | {r['adj_kept']:.2f} | {r['compact']:.2f} | {r['time']:.1f} |"
            )
    (HERE / "data" / "tables.md").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    tables()
    prescale()
    anchor()
    groups()
