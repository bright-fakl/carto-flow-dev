"""Premorph cells against the flow map they start from: adjacency and group cohesion.

The adjacency 'kept' metric of the audit compares cells with the original polygons. A cartogram does not have to
keep the original adjacency graph, and the flow morph itself is the natural reference for premorph runs. This
script scores the flow-morphed polygons with the same metrics as the cells, using the premorph runs saved by
run_followup.py (anchor 0.25 on the states and the districts; the groups study for the fixed and elastic bases).

Run from a carto-flow checkout of main:
    NUMBA_NUM_THREADS=8 uv run python premorph_reference.py
Writes data/premorph_reference.md.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import shapely

import carto_flow.data as examples
import carto_flow.flow_cartogram as flow

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "exploration-voronoi-options"))
sys.path.insert(0, str(HERE))  # first, so make_figures is the follow-up one
warnings.filterwarnings("ignore")
import make_figures as mf  # noqa: E402
import run_experiments as audit  # noqa: E402


def morph(gdf, col):
    """The flow map the saved premorph runs started from (balanced preset, 400 iterations, center rasterization)."""
    options = flow.MorphOptions.preset_balanced().copy_with(n_iter=400, show_progress=False, density_rasterization="center")
    m = flow.morph_gdf(gdf, col, options=options)
    return shapely.make_valid(np.asarray(m.to_geodataframe().geometry, dtype=object))


def compact(geoms):
    return float(np.mean(4 * np.pi * shapely.area(geoms) / shapely.length(geoms) ** 2))


def main():
    out = []
    states = examples.load_us_census(population=True)
    districts = examples.load_us_census(population=True, level="congressional_district")
    labels = districts["State Name"].to_numpy()

    out.append("Adjacency of the cells against the original polygons and against the flow map (all pairs; for the districts, pairs inside one state):")
    out.append("")
    out.append("| input | pairs | morph keeps of the original | cells keep of the original | cells keep of the morph | new pairs in the cells (not in the morph) |")
    out.append("|---|---|---|---|---|---|")
    for name, gdf, col, anchor_key in (("states", states, "Population (Millions)", "S"), ("districts", districts, "Population", "D")):
        geoms = np.asarray(gdf.geometry, dtype=object)
        mph = morph(gdf, col)
        cells = mf.cells(anchor_key, "P", "anchor", "0.25")
        p0, pm, pc = audit.pairset(geoms), audit.pairset(mph), audit.pairset(cells)
        scopes = [("all", lambda p: True)]
        if name == "districts":
            scopes.append(("within a state", lambda p: labels[p[0]] == labels[p[1]]))
        for scope, keep in scopes:
            a, b, c = {p for p in p0 if keep(p)}, {p for p in pm if keep(p)}, {p for p in pc if keep(p)}
            out.append(
                f"| {name} | {scope}, {len(a)} | {len(a & b) / len(a):.3f} | {len(a & c) / len(a):.3f} | {len(b & c) / len(b):.3f} | {len(c - b)} |"
            )

    out.append("")
    out.append("Group cohesion of the districts by state (metrics that do not depend on which cells are neighbors), flow map polygons against cells:")
    out.append("")
    out.append("| layout | largest piece | solidity | neighbor purity | compactness |")
    out.append("|---|---|---|---|---|")
    mph = morph(districts, "Population")
    rows = [("flow map (the premorph's own polygons)", mph)]
    rows.append(("premorph cells, anchor 0.25", mf.cells("D", "P", "anchor", "0.25")))
    rows.append(("fixed outline, no spring", mf.cells("D", "F", "intra_group_spring", "off")))
    rows.append(("fixed outline, intra_group_spring 0.5", mf.cells("D", "F", "intra_group_spring", "0.5")))
    rows.append(("elastic boundary, intra_group_spring 0.5", mf.cells("D", "E", "intra_group_spring", "0.5")))
    for label, geoms in rows:
        co = mf.cohesion(geoms, labels)
        out.append(f"| {label} | {co['largest_piece']:.3f} | {co['solidity']:.3f} | {co['neighbor_purity']:.3f} | {compact(geoms):.3f} |")

    (HERE / "data" / "premorph_reference.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
