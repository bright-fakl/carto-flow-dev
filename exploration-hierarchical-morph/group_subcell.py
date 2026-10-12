"""Sub-cell regions of the counties on one global grid and on a grid fitted to each state.

    COUNTIES_PARQUET=counties_prepared.parquet uv run python group_subcell.py

The target area of a county is its vote share of the total area. A state group is assumed to end with the sum of
its members' targets as area; its grid is the square grid of build_multilevel_grids (margin 0.5) on the bounding
box of the state's original geometry.
"""
import os
from pathlib import Path

import geopandas as gpd
import numpy as np

HERE = Path(__file__).resolve().parent
g = gpd.read_parquet(os.environ["COUNTIES_PARQUET"])
g["state"] = g["GEOID"].astype(str).str[:2]
total = g.area.sum()
g["target"] = g["total_votes"].to_numpy(float) / g["total_votes"].sum() * total
xmin, ymin, xmax, ymax = g.total_bounds
side = 2 * max(xmax - xmin, ymax - ymin)

out = ["## Counties with a target below one cell: one global grid and a grid per state\n", "| grid | global grid | grid fitted to each state | states with at least one such county |", "|---|---|---|---|"]
worst = {}
for n in (128, 256, 512, 1024):
    cell_global = (side / n) ** 2
    glob = int((g["target"] / cell_global < 1).sum())
    per = 0
    states = 0
    for k, h in g.groupby("state"):
        x0, y0, x1, y1 = h.total_bounds
        cell = (2 * max(x1 - x0, y1 - y0) / n) ** 2
        r = h["target"].to_numpy() / cell
        per += int((r < 1).sum())
        states += int((r < 1).any())
        worst.setdefault(n, []).append((float(r.min()), k, len(h)))
    out.append(f"| {n} | {glob} ({100 * glob / len(g):.1f} %) | {per} ({100 * per / len(g):.1f} %) | {states} of {g['state'].nunique()} |")
out += ["\n## Smallest county of the states with the smallest values, in cells of the state grid\n", "| grid | state (counties): smallest county in cells |", "|---|---|"]
for n, w in worst.items():
    w.sort()
    out.append(f"| {n} | " + ", ".join(f"{k} ({c}): {r:.3g}" for r, k, c in w[:4]) + " |")
(HERE / "data" / "tables.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
