"""Runner for the mosaic world-islands investigation.

Every record is appended to ``results.jsonl`` the moment it finishes, so a
killed run leaves usable partial results on disk.

Modes
-----
diag    case x budget x morph: per-stage tile-loss trace + full layout + figure
passes  swap_repair_passes sweep (runtime + integrity)
hops    ring_swapback_max_hops sweep (runtime + integrity)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))

import wi_inputs as W  # noqa: E402

RESULTS = HERE / "results.jsonl"


def _default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def append(rec):
    with RESULTS.open("a") as f:
        f.write(json.dumps(rec, default=_default) + "\n")
        f.flush()


def fingerprint(res, G):
    a = res.regions_gdf
    tiles = res.tiles_gdf
    per = [sorted(tiles.index[tiles["geometry_id"] == g].tolist()) for g in range(G)]
    # tile index within tiles_gdf is not stable across option values; use tile
    # centroids instead, rounded, which are.
    cents = np.array([[p.centroid.x, p.centroid.y] for p in tiles.geometry])
    per = {}
    for i, g in enumerate(tiles["geometry_id"].tolist()):
        per.setdefault(int(g), []).append((round(float(cents[i, 0]), 3), round(float(cents[i, 1]), 3)))
    payload = json.dumps([[g, sorted(v)] for g, v in sorted(per.items())])
    return hashlib.sha1(payload.encode()).hexdigest()[:16]


def load_case(case, budget):
    if case == "world":
        return W.load_world(budget), "tiles", None
    if case == "africa":
        return W.load_africa(budget), "tiles", None
    if case == "world_mainland":
        return W.load_world_mainland(budget)[0], "tiles", None
    if case == "districts":
        import inputs as IN
        return IN.load_districts(), None, "State Name"
    if case == "states":
        import inputs as IN
        return IN.load_states(), "tiles", None
    raise SystemExit(case)


def run(gdf, tile_count, group_by, *, morph, **hung):
    from carto_flow.symbol_cartogram import create_layout
    from carto_flow.symbol_cartogram.layouts.mosaic import HungarianOptions, MosaicLayout

    layout = MosaicLayout(morph=morph, hungarian_options=HungarianOptions(**hung))
    t0 = time.perf_counter()
    res = create_layout(gdf, tile_count=tile_count, group_by=group_by, layout=layout, show_progress=False)
    return res, time.perf_counter() - t0


def integrity(res, gdf, tile_count):
    am = res.metrics.algorithm
    want = gdf[tile_count].to_numpy() if tile_count else np.ones(len(gdf), dtype=int)
    got = res.regions_gdf["tile_count"].to_numpy() if tile_count or True else None
    names = [str(x) for x in gdf["name"]] if "name" in gdf.columns else [str(i) for i in gdf.index]
    if len(got) != len(want):  # group_by mode: regions_gdf is per-group
        got = None
        short = []
    else:
        short = [(names[i], int(want[i]), int(got[i])) for i in range(len(want)) if got[i] != want[i]]
    return dict(
        tile_size=float(am.tile_size), n_components=int(am.n_components),
        regions_correct=int(am.regions_correct), regions_total=int(am.regions_total),
        n_noncontiguous_regions=int(am.n_noncontiguous_regions),
        n_split_groups=int(am.n_split_groups),
        n_unassigned_core_tiles=int(am.n_unassigned_core_tiles),
        n_enclosed_unassigned_tiles=int(am.n_enclosed_unassigned_tiles),
        repair_passes=int(am.repair_passes),
        n_short=len(short), n_zero=sum(1 for s in short if s[2] == 0), short=short,
    )


# ------------------------------------------------------------------ figures


def figure(case, budget, morph, gdf, res, short_names, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(17, 7))
    names = [str(x) for x in gdf["name"]] if "name" in gdf.columns else [str(i) for i in gdf.index]
    dropped = {n for n, w, g in short_names if g == 0}
    shorted = {n for n, w, g in short_names if g > 0}

    ax = axes[0]
    gdf.plot(ax=ax, color="#dfe3e8", edgecolor="white", linewidth=0.3)
    idx_drop = [i for i, n in enumerate(names) if n in dropped]
    idx_short = [i for i, n in enumerate(names) if n in shorted]
    if idx_short:
        gdf.iloc[idx_short].plot(ax=ax, color="#f6c453", edgecolor="#8a6d1f", linewidth=0.6)
    if idx_drop:
        gdf.iloc[idx_drop].plot(ax=ax, color="#d94a3d", edgecolor="#7a1f16", linewidth=0.8)
        for i in idx_drop:
            c = gdf.geometry.iloc[i].centroid
            ax.annotate(names[i], (c.x, c.y), fontsize=7, color="#7a1f16",
                        xytext=(6, 6), textcoords="offset points")
    ax.set_title(f"{case} input - red: 0 tiles placed ({len(idx_drop)}), amber: short ({len(idx_short)})", fontsize=10)
    ax.set_axis_off()

    ax = axes[1]
    tiles = res.tiles_gdf.copy()
    gid = tiles["geometry_id"].to_numpy()
    colors = np.array(["#8fb8de"] * len(tiles), dtype=object)
    tiles.plot(ax=ax, color=list(colors), edgecolor="white", linewidth=0.3)
    ax.set_title(f"{case} mosaic (budget {budget}, morph={morph}) - "
                 f"{len(tiles)} tiles placed of {int(gdf['tiles'].sum()) if 'tiles' in gdf else len(gdf)} requested",
                 fontsize=10)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ------------------------------------------------------------------ modes


def mode_diag(args):
    from trace_loss import trace

    for case in args.cases:
        for budget in args.budgets:
            for morph in args.morphs:
                tag = f"{case}_b{budget}_morph{int(morph)}"
                try:
                    gdf, tc, gb = load_case(case, budget)
                    res, elapsed = run(gdf, tc, gb, morph=morph)
                    integ = integrity(res, gdf, tc)
                    tr = trace(gdf, morph=morph)
                    rec = dict(mode="diag", case=case, budget=budget, morph=morph,
                               n_regions=len(gdf), requested=int(gdf["tiles"].sum()),
                               wall_clock_s=elapsed, fingerprint=fingerprint(res, len(gdf)),
                               **integ,
                               empty_pool=[tr["names"][i] for i in tr["empty_pool_regions"]],
                               overwrites=[[tr["names"][fg], fc, tr["names"][tg], tc2]
                                           for _t, fg, fc, tg, tc2 in tr["overwrites"]],
                               n_overwrites=len(tr["overwrites"]),
                               lsa_short=tr["lsa_short"],
                               comp_demand=tr["comp_demand"], comp_core=tr["comp_core"],
                               comp_pool=tr["comp_pool"])
                    append(rec)
                    figure(case, budget, morph, gdf, res, integ["short"], HERE / f"{tag}.png")
                    print(f"[done] {tag} {elapsed:.1f}s short={integ['n_short']} zero={integ['n_zero']} "
                          f"overwrites={len(tr['overwrites'])}", flush=True)
                except Exception:
                    append(dict(mode="diag", case=case, budget=budget, morph=morph,
                                error=traceback.format_exc(limit=4)))
                    print(f"[fail] {tag}", flush=True)


def mode_knob(args, knob, values):
    for case in args.cases:
        for budget in args.budgets:
            for morph in args.morphs:
                gdf, tc, gb = load_case(case, budget)
                for v in values:
                    tag = f"{case}_b{budget}_morph{int(morph)}_{knob}={v}"
                    try:
                        res, elapsed = run(gdf, tc, gb, morph=morph, **{knob: v})
                        rec = dict(mode=knob, case=case, budget=budget, morph=morph, value=v,
                                   wall_clock_s=elapsed, fingerprint=fingerprint(res, len(gdf)),
                                   **integrity(res, gdf, tc))
                        append(rec)
                        print(f"[done] {tag} {elapsed:.1f}s fp={rec['fingerprint']} "
                              f"noncontig={rec['n_noncontiguous_regions']} split={rec['n_split_groups']} "
                              f"short={rec['n_short']}", flush=True)
                    except Exception:
                        append(dict(mode=knob, case=case, budget=budget, morph=morph, value=v,
                                    error=traceback.format_exc(limit=4)))
                        print(f"[fail] {tag}", flush=True)


def mode_metrics(args, label):
    """Layout + integrity only, for any case (no 'tiles' column required)."""
    for case in args.cases:
        for budget in args.budgets:
            for morph in args.morphs:
                tag = f"{label}:{case}_b{budget}_morph{int(morph)}"
                try:
                    gdf, tc, gb = load_case(case, budget)
                    res, elapsed = run(gdf, tc, gb, morph=morph)
                    rec = dict(mode="metrics", label=label, case=case, budget=budget, morph=morph,
                               n_regions=len(gdf), wall_clock_s=elapsed,
                               fingerprint=fingerprint(res, len(gdf)), **integrity(res, gdf, tc))
                    append(rec)
                    print(f"[done] {tag} {elapsed:.1f}s fp={rec['fingerprint']} short={rec['n_short']} "
                          f"zero={rec['n_zero']} noncontig={rec['n_noncontiguous_regions']} "
                          f"split={rec['n_split_groups']} unasgn={rec['n_unassigned_core_tiles']} "
                          f"encl={rec['n_enclosed_unassigned_tiles']}", flush=True)
                except Exception:
                    append(dict(mode="metrics", label=label, case=case, budget=budget, morph=morph,
                                error=traceback.format_exc(limit=4)))
                    print(f"[fail] {tag}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="x")
    ap.add_argument("--mode", required=True)
    ap.add_argument("--cases", default="africa,world,world_mainland")
    ap.add_argument("--budgets", default="384")
    ap.add_argument("--morphs", default="1,0")
    ap.add_argument("--values", default=None)
    a = ap.parse_args()
    a.cases = a.cases.split(",")
    a.budgets = [int(x) for x in a.budgets.split(",")]
    a.morphs = [bool(int(x)) for x in a.morphs.split(",")]
    if a.mode == "metrics":
        mode_metrics(a, a.label)
    elif a.mode == "diag":
        mode_diag(a)
    elif a.mode == "passes":
        mode_knob(a, "swap_repair_passes", [int(x) for x in (a.values or "0,1,2,3,5,10").split(",")])
    elif a.mode == "hops":
        mode_knob(a, "ring_swapback_max_hops", [int(x) for x in (a.values or "0,1,2,4,8,16,32").split(",")])
    else:
        raise SystemExit(a.mode)
