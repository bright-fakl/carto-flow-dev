"""Figure for the interior_bonus default-change gating check.

    PYTHONPATH=<checkout of origin/main>/src uv run python \
        visual_checks/grid-vs-mosaic-similarity/figures_ibcheck.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent

CASES = [
    ("states_uniform_hex", "states, 1 tile/region (hexagon)"),
    ("states_uniform_sq", "states, 1 tile/region (square)"),
    ("states154", "states, 154 tiles"),
    ("districts", "432 districts"),
]
METRICS = [
    ("displacement", "median_tiles", "displacement median (tiles)", "lower better"),
    ("adjacency", "frac_edge_adjacent", "adjacency preserved", "higher better"),
    ("direction", "median_abs_dev_deg", "direction median |dev| (deg)", "lower better"),
    ("direction", "frac_reversed_gt90", "direction reversed >90", "lower better"),
    ("silhouette_vs_original", "iou_aligned", "silhouette IoU vs original", "higher better"),
]


def disqualified(r):
    i = r["integrity"]
    return (
        i["n_noncontiguous_regions"] > 0
        or i["n_split_groups_raw"] > 0
        or i["regions_correct"] != i["regions_total"]
        or i["n_enclosed_unassigned_tiles"] > 0
    )


def main():
    records = [json.loads(l) for l in (HERE / "results.jsonl").open()]
    S = [r for r in records if "ibcheck_value" in r]

    fig, axes = plt.subplots(len(CASES), len(METRICS), figsize=(3.3 * len(METRICS), 2.8 * len(CASES)))
    for i, (case, clabel) in enumerate(CASES):
        for j, (sec, key, mlabel, direction) in enumerate(METRICS):
            ax = axes[i, j]
            for morph, colour, ls, mlab in [
                (True, "#b00020", "-", "morph=True"),
                (False, "#3a6ea5", "--", "morph=False"),
            ]:
                rows = sorted(
                    [r for r in S if r["ibcheck_case"] == case and r["ibcheck_morph"] == morph],
                    key=lambda r: r["ibcheck_value"],
                )
                xs = [r["ibcheck_value"] for r in rows]
                ys = [r[sec][key] for r in rows]
                ax.plot(xs, ys, ls, marker="o", ms=4, color=colour, lw=1.5,
                        label=mlab if (i == 0 and j == 0) else None)
                bx = [r["ibcheck_value"] for r in rows if disqualified(r)]
                by = [r[sec][key] for r in rows if disqualified(r)]
                ax.plot(bx, by, "x", ms=11, mew=2.2, color="black",
                        label="integrity failure" if (i == 0 and j == 0 and bx) else None)
            # mark the current default and the proposed value
            ax.axvline(0.5, color="#888888", lw=0.9, ls=":")
            ax.axvline(2.0, color="#2e8b57", lw=0.9, ls=":")
            ax.set_xscale("symlog", linthresh=0.25)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.3)
            if i == 0:
                ax.set_title(f"{mlabel}\n({direction})", fontsize=8.5)
            if j == 0:
                ax.set_ylabel(clabel, fontsize=8)
            if i == len(CASES) - 1:
                ax.set_xlabel("interior_bonus", fontsize=8)
    axes[0, 0].legend(fontsize=7, loc="best")
    fig.suptitle(
        "interior_bonus gating check - grey dotted = current default 0.5, green dotted = proposed 2.0.\n"
        "Black X = run introduced a split group or a non-contiguous region (integrity failure).",
        fontsize=11,
    )
    fig.tight_layout()
    out = HERE / "interior_bonus_check.png"
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
