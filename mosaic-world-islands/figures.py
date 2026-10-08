"""Before/after figures for the three inputs at both morph settings.

Left panel: the input, with every region that ends up with zero tiles in red
and every region short of tiles in amber.  Right panel: the mosaic, tiles
coloured by the connected component their owning region belongs to, with a red
cross at the location each dropped region should have occupied.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import wi_inputs as W  # noqa: E402
from run_all import load_case, run  # noqa: E402

PALETTE = ["#4c78a8", "#72b7b2", "#54a24b", "#eeca3b", "#b279a2", "#ff9da6",
           "#9d755d", "#bab0ac", "#e45756", "#f58518"]


def panel(case, budget, morph, ax_in, ax_out):
    gdf, tc, gb = load_case(case, budget)
    res, elapsed = run(gdf, tc, gb, morph=morph)
    names = [str(x) for x in gdf["name"]]
    want = gdf["tiles"].to_numpy()
    got = res.regions_gdf["tile_count"].to_numpy()
    drop = [i for i in range(len(gdf)) if got[i] == 0]
    shrt = [i for i in range(len(gdf)) if 0 < got[i] < want[i]]

    comps = W.components_of(gdf)
    comp_of = np.zeros(len(gdf), dtype=int)
    for ci, c in enumerate(comps):
        for i in c:
            comp_of[i] = ci

    gdf.plot(ax=ax_in, color="#e7eaee", edgecolor="white", linewidth=0.25)
    if shrt:
        gdf.iloc[shrt].plot(ax=ax_in, color="#f6c453", edgecolor="#8a6d1f", linewidth=0.5)
    if drop:
        gdf.iloc[drop].plot(ax=ax_in, color="#d94a3d", edgecolor="#7a1f16", linewidth=0.7)
    for i in drop + shrt:
        c = gdf.geometry.iloc[i].centroid
        ax_in.annotate(f"{names[i]} {got[i]}/{want[i]}", (c.x, c.y), fontsize=6.5,
                       color="#7a1f16" if i in drop else "#6b5310",
                       xytext=(5, 5), textcoords="offset points")
    ax_in.set_title(f"{case} - input, morph={morph}\n"
                    f"{len(drop)} region(s) with 0 tiles (red), {len(shrt)} short (amber)", fontsize=9)
    ax_in.set_axis_off()

    tiles = res.tiles_gdf
    gid = tiles["geometry_id"].to_numpy().astype(int)
    cols = [PALETTE[comp_of[g] % len(PALETTE)] if comp_of[g] != 0 else "#c8d4e0" for g in gid]
    tiles.plot(ax=ax_out, color=cols, edgecolor="white", linewidth=0.25)
    for i in drop:
        c = gdf.geometry.iloc[i].centroid
        ax_out.plot([c.x], [c.y], marker="x", color="#d94a3d", markersize=9, markeredgewidth=2.2)
    ax_out.set_title(f"{case} - mosaic, morph={morph}, budget {budget}\n"
                     f"{len(tiles)} of {int(want.sum())} requested tiles placed, {elapsed:.1f}s", fontsize=9)
    ax_out.set_axis_off()
    return dict(case=case, budget=budget, morph=morph, dropped=[names[i] for i in drop],
                short=[names[i] for i in shrt], elapsed=elapsed)


if __name__ == "__main__":
    specs = [("africa", 150), ("world", 384), ("world_mainland", 384)]
    for case, budget in specs:
        fig, axes = plt.subplots(2, 2, figsize=(17, 12))
        for row, morph in enumerate((True, False)):
            info = panel(case, budget, morph, axes[row][0], axes[row][1])
            print(info, flush=True)
        fig.tight_layout()
        out = HERE / f"fig_{case}_b{budget}.png"
        fig.savefig(out, dpi=105)
        plt.close(fig)
        print("wrote", out, flush=True)
