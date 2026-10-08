"""Figures + tables from results.jsonl."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
CASES = ["states_uniform", "states_uniform_sq", "states", "districts", "world"]
COLORS = dict(zip(CASES, ["#1f77b4", "#9467bd", "#2ca02c", "#d62728", "#ff7f0e"]))

METRICS = [
    ("displacement.median_tiles", "displacement (tiles, median)"),
    ("adjacency.frac_edge_adjacent", "adjacency kept (frac)"),
    ("direction.median_abs_dev_deg", "direction dev (deg, median)"),
    ("compactness.polsby_popper_median", "Polsby-Popper (median)"),
    ("silhouette_vs_original.iou_aligned", "silhouette IoU (aligned)"),
    ("__defects", "integrity defects (noncontig + split groups)"),
]


def get(rec, path):
    cur = rec
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def defects(rec):
    it = rec.get("integrity") or {}
    return (it.get("n_noncontiguous_regions") or 0) + (it.get("n_split_groups_component_adjusted") or 0)


def load():
    rows = []
    with (HERE / "results.jsonl").open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def value_of(rec):
    v = rec["value"]
    if isinstance(v, list):
        return tuple(v)
    if isinstance(v, bool):
        return int(v)
    return v


def main():
    rows = load()
    errs = [r for r in rows if "error" in r]
    ok = [r for r in rows if "error" not in r]
    print(f"{len(ok)} runs, {len(errs)} errors")

    base = {(r["case"], r["morph"]): r for r in ok if r["knob"] == "baseline"}

    byknob = defaultdict(list)
    for r in ok:
        if r["knob"] != "baseline":
            byknob[r["knob"]].append(r)

    for knob, recs in byknob.items():
        if knob == "distance_x_outside":
            continue
        fig, axes = plt.subplots(2, 3, figsize=(16, 8))
        for ax, (path, title) in zip(axes.ravel(), METRICS):
            for case in CASES:
                for morph, ls, mk in ((True, "-", "o"), (False, "--", "s")):
                    sel = [r for r in recs if r["case"] == case and r["morph"] == morph]
                    b = base.get((case, morph))
                    if b is not None and knob in b["opts"]:
                        sel = sel + [dict(b, value=b["opts"][knob])]
                    elif b is not None and knob == "tile_size":
                        sel = sel
                    if not sel:
                        continue
                    pts = []
                    for r in sel:
                        y = defects(r) if path == "__defects" else get(r, path)
                        if y is None:
                            continue
                        pts.append((value_of(r), y))
                    pts = [p for p in pts if isinstance(p[0], (int, float))]
                    pts.sort()
                    if not pts:
                        continue
                    ax.plot(
                        [p[0] for p in pts],
                        [p[1] for p in pts],
                        ls,
                        marker=mk,
                        ms=4,
                        color=COLORS[case],
                        alpha=0.9,
                        label=f"{case} morph={morph}",
                    )
            ax.set_title(title, fontsize=10)
            ax.set_xlabel(knob)
            ax.grid(alpha=0.3)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=7)
        fig.suptitle(f"mosaic option sweep: {knob}  (solid = morph=True, dashed = morph=False)")
        fig.tight_layout(rect=(0, 0.07, 1, 0.97))
        fig.savefig(HERE / f"knob_{knob}.png", dpi=120)
        plt.close(fig)
        print("wrote", f"knob_{knob}.png")

    # joint distance_weight x outside_penalty heatmaps
    joint = byknob.get("distance_x_outside", [])
    if joint:
        dws = sorted({r["value"][0] for r in joint})
        ops = sorted({r["value"][1] for r in joint})
        panels = [
            ("displacement.median_tiles", "displacement (tiles)"),
            ("adjacency.frac_edge_adjacent", "adjacency kept"),
            ("silhouette_vs_original.iou_aligned", "silhouette IoU"),
            ("__defects", "integrity defects"),
        ]
        for morph in (True, False):
            fig, axes = plt.subplots(len(panels), len(CASES), figsize=(3.1 * len(CASES), 2.7 * len(panels)))
            for i, (path, title) in enumerate(panels):
                for j, case in enumerate(CASES):
                    ax = axes[i, j]
                    grid = [[float("nan")] * len(ops) for _ in dws]
                    for r in joint + [base[(case, morph)]] if (case, morph) in base else joint:
                        if r["case"] != case or r["morph"] != morph:
                            continue
                        dw, op = r["opts"]["distance_weight"], r["opts"]["outside_penalty"]
                        if dw not in dws or op not in ops:
                            continue
                        y = defects(r) if path == "__defects" else get(r, path)
                        if y is None:
                            continue
                        grid[dws.index(dw)][ops.index(op)] = y
                    im = ax.imshow(grid, cmap="viridis", aspect="auto")
                    ax.set_xticks(range(len(ops)), [str(o) for o in ops], fontsize=7)
                    ax.set_yticks(range(len(dws)), [str(d) for d in dws], fontsize=7)
                    for a in range(len(dws)):
                        for b in range(len(ops)):
                            v = grid[a][b]
                            if v == v:
                                ax.text(b, a, f"{v:.2f}", ha="center", va="center", fontsize=6, color="w")
                    if i == 0:
                        ax.set_title(case, fontsize=9)
                    if j == 0:
                        ax.set_ylabel(f"{title}\ndistance_weight", fontsize=7)
                    ax.set_xlabel("outside_penalty", fontsize=7)
                    fig.colorbar(im, ax=ax, fraction=0.04)
            fig.suptitle(f"distance_weight x outside_penalty, morph={morph}")
            fig.tight_layout(rect=(0, 0, 1, 0.96))
            fig.savefig(HERE / f"joint_distance_outside_morph{int(morph)}.png", dpi=120)
            plt.close(fig)
            print("wrote joint heatmap morph", morph)


if __name__ == "__main__":
    main()
