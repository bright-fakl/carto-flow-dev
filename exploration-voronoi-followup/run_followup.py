"""Follow-up runs for the Voronoi option audit (exploration-voronoi-options).

Three studies, each on top of the audit's helpers (bases F = fixed outline, E = ElasticBoundary(0.05),
P = premorph=True):

  prescale  A = 50 states + DC including Alaska and Hawaii (population weights), prescale_components
            off and on for each base, and for P also the pre-morph's own prescale_components.
  anchor    S = 49 contiguous states, D = 432 districts grouped by state, premorph=True with
            generator_anchor 0, 0.25 and 0.5.
  groups    D with intra_group_spring in {off, 0.25, 0.5, 1} (adjacency_spring 0 and 0.1) for each base,
            scored on whether each state's districts stay together.

Writes data/runs.jsonl (rows already present are skipped) and data/cells/<key>.pkl (WKB cells and
generator positions) for make_figures.py.

Run from a carto-flow checkout of main:
    NUMBA_NUM_THREADS=8 uv run python run_followup.py [prescale,anchor,groups]
"""

from __future__ import annotations

import gzip
import json
import pickle
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import shapely

import carto_flow.data as examples
import carto_flow.flow_cartogram as flow
import carto_flow.voronoi_cartogram as vor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "exploration-voronoi-options"))
import run_experiments as audit  # noqa: E402

_AUDIT_LOAD = audit.load

audit.CACHE = HERE / "data" / "cache"
OUT = HERE / "data" / "runs.jsonl"
CELLS = HERE / "data" / "cells"

BASES = {"F": {}, "E": {"elastic": 0.05}, "P": {"premorph": True}}


def load(ds: str):
    if ds == "A":
        return examples.load_us_census(population=True, contiguous_only=False), "Population (Millions)", None
    return _AUDIT_LOAD(ds)


def plan(study: str):
    if study == "prescale":
        for base, settings in BASES.items():
            yield "A", base, "prescale", "off", dict(settings)
            yield "A", base, "prescale", "on", {**settings, "prescale": True}
        morph_on = flow.MorphOptions.preset_balanced().copy_with(n_iter=400, show_progress=False, prescale_components=True)
        yield "A", "P", "prescale", "morph on", {"premorph": morph_on}
        yield "A", "P", "prescale", "morph on + cells on", {"premorph": morph_on, "prescale": True}
    elif study == "anchor":
        for ds in ("S", "D"):
            for anchor in (0.0, 0.25, 0.5):
                yield ds, "P", "anchor", f"{anchor:g}", {"premorph": True, "anchor": anchor}
    elif study == "groups":
        for base, settings in BASES.items():
            yield "D", base, "intra_group_spring", "off", dict(settings)
            for intra in (0.25, 0.5, 1.0):
                yield "D", base, "intra_group_spring", f"{intra:g}", {**settings, "intra": intra}
            yield "D", base, "intra_group_spring", "0.5 + adj 0.1", {**settings, "intra": 0.5, "spring": 0.1}
            yield "D", base, "adjacency_spring", "0.1", {**settings, "spring": 0.1}


def group_scores(cells, gdf, group_by):
    """Share of groups whose cells form one piece, and the adjacency kept inside and between groups."""
    labels = gdf[group_by].to_numpy()
    out = {}
    one_piece = []
    for g in np.unique(labels):
        idx = np.flatnonzero(labels == g)
        parts = shapely.get_parts(shapely.union_all(cells[idx]))
        areas = sorted((p.area for p in parts), reverse=True)
        one_piece.append(len(areas) == 1 or areas[1] < 0.01 * sum(areas))
    out["groups_whole"] = float(np.mean(one_piece))
    orig = audit.pairset(np.asarray(gdf.geometry, dtype=object))
    new = audit.pairset(cells)
    same = {p for p in orig if labels[p[0]] == labels[p[1]]}
    other = orig - same
    out["adj_within"] = len(same & new) / max(len(same), 1)
    out["adj_between"] = len(other & new) / max(len(other), 1)
    return out


def run(ds, base, factor, level, settings, ctx, gdf, col, group_by):
    kwargs = audit.build(settings, ds, gdf, col, group_by)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        t = time.perf_counter()
        r = vor.create_voronoi_cartogram(gdf, **kwargs)
        wall = time.perf_counter() - t
    cells = np.asarray(r.cells, dtype=object)
    w = gdf[col].to_numpy(float)
    a = shapely.area(cells)
    ratio = a / (w / w.sum() * a.sum())
    ab = gdf["State Abbreviation"].to_numpy() if "State Abbreviation" in gdf else None
    row = {
        "ds": ds, "base": base, "factor": factor, "level": level, "n": len(cells),
        "mean_err": float(np.abs(ratio - 1).mean() * 100), "max_err": float(np.abs(ratio - 1).max() * 100),
        "converged": bool(r.metrics["converged"]), "it": int(r.metrics["n_iterations"]), "time": wall,
        "compact": float(np.mean(4 * np.pi * a / np.maximum(shapely.length(cells), 1e-300) ** 2)),
        "adj_kept": len(audit.pairset(cells) & ctx["orig_pairs"]) / len(ctx["orig_pairs"]),
        "split": int(sum(1 for c in cells if c.geom_type == "MultiPolygon" and sorted(g.area for g in c.geoms)[-2] > 0.01 * c.area)),
        "invalid": int((~shapely.is_valid(cells)).sum()), "warnings": sorted({f"{x.category.__name__}: {str(x.message)[:80]}" for x in caught}),
    }
    outline = r._field._current_boundary
    cc = audit.centroids(np.where(shapely.is_empty(cells), shapely.points(r.positions), cells))
    cc_o = audit.to_frame(cc, outline, ctx["orig_outline"])
    row["d_orig_med"] = float(np.median(np.linalg.norm(cc_o - ctx["orig_c"], axis=1) / ctx["r0"]))
    row["d_flow_med"] = float(np.median(np.linalg.norm(cc_o - ctx["flow_c_o"], axis=1) / ctx["r0"]))
    if ab is not None:
        tx = np.flatnonzero(ab == "TX")
        reg = ctx["tx_flow"]
        row["tx_own"] = float(shapely.union_all(cells[tx]).intersection(reg).area / reg.area)
        for state in ("AK", "HI", "TX", "LA"):
            i = np.flatnonzero(ab == state)
            if len(i):
                row[f"{state}_area_ratio"] = float(ratio[i[0]])
                row[f"{state}_shift"] = float(np.linalg.norm(cc_o[i[0]] - ctx["orig_c"][i[0]]) / ctx["r0"])
    if group_by:
        row.update(group_scores(cells, gdf, group_by))
    CELLS.mkdir(parents=True, exist_ok=True)
    key = f"{ds}_{base}_{factor}_{level}".replace(" ", "_").replace("+", "p")
    with gzip.open(CELLS / f"{key}.pkl.gz", "wb", compresslevel=9) as fh:
        fh.write(pickle.dumps({"cells": shapely.to_wkb(shapely.set_precision(cells, 100.0)), "positions": np.asarray(r.positions)}))
    return row


def main():
    studies = sys.argv[1].split(",") if len(sys.argv) > 1 else ["prescale", "anchor", "groups"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT.exists():
        done = {(r["ds"], r["base"], r["factor"], r["level"]) for r in map(json.loads, OUT.read_text().splitlines()) if "error" not in r}
    contexts = {}
    for study in studies:
        for ds, base, factor, level, settings in plan(study):
            if (ds, base, factor, level) in done:
                continue
            if ds not in contexts:
                gdf, col, group_by = load(ds)
                audit.load = lambda d, _g=(gdf, col, group_by): _g  # context() and flow_reference() read the frame through load()
                contexts[ds] = (audit.context(ds), gdf, col, group_by)
            ctx, gdf, col, group_by = contexts[ds]
            try:
                row = run(ds, base, factor, level, settings, ctx, gdf, col, group_by)
            except Exception as exc:
                row = {"ds": ds, "base": base, "factor": factor, "level": level, "error": f"{type(exc).__name__}: {exc}"[:300]}
            with OUT.open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(study, ds, base, factor, level, "err" if "error" in row else f"{row['time']:.1f}s it {row['it']} err {row['mean_err']:.2f}%", flush=True)


if __name__ == "__main__":
    main()
