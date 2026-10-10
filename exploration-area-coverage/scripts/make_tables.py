"""Print markdown tables from data/*.pkl.   uv run python make_tables.py [section]"""

import pickle
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
D = HERE / "data"
COVS = ["center", "s2", "s4", "s8", "exact"]


def load(name):
    p = D / name
    return pickle.load(open(p, "rb")) if p.exists() else {}


def f(x, n=2):
    return "-" if x is None else f"{x:.{n}f}"


def main_table(case, grid, ro):
    r = load(f"out_{case}_{grid}.pkl")
    rows = []
    for c in COVS:
        k = f"{c}|ro{ro}|dtbase|re10"
        if k not in r:
            continue
        v = r[k]
        rows.append(
            f"| {grid} | {c} | {v['status']} | {v['it']} | {v['rec']} | {v['ratio']:.1f} | {v['cost']:.0f} | "
            f"{v['raster_per_call'] * 1e3:.1f} | {v['mean']:.2f} / {v['max']:.1f} | {v['ext_mean']:.2f} / {v['ext_max']:.1f} / {v['ext_gt10']:.1f} | "
            f"{v['rises20']} | {v['spike']:.2f} | {v['stall_at'] or '-'} | {v['best']:.2f} |"
        )
    return rows


HDR = (
    "| grid | raster | status | it | rec | ratio | cost | raster ms/call | lib mean / max % | ext mean / max / >10% | rises<20 | max spike | stall@ | best |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
)


def section_main(ro):
    for case in ("states", "horiz", "tang", "tilt", "districts", "counties"):
        rows = []
        for grid in (128, 256, 512):
            rows += main_table(case, grid, ro)
        if rows:
            print(f"\n### {case}, refresh_on_rise={ro}\n\n{HDR}")
            print("\n".join(rows))


def section_rob():
    print("\n| case | grid | raster | refresh_on_rise | converged | stalled (replay) | diverged | other | runs |\n|---|---|---|---|---|---|---|---|---|")
    for case in ("states", "horiz", "tang", "tilt", "districts"):
        for grid in (128, 256, 512):
            r = load(f"out_{case}_{grid}.pkl")
            for c in COVS:
                for ro in ("0.01", "None"):
                    ks = [k for k in r if k.startswith(f"{c}|ro{ro}|dt0.") and k.split("|")[2] != "dtbase"]
                    if not ks:
                        continue
                    conv = sum(r[k]["status"] == "converged" for k in ks)
                    st = sum(r[k]["status"] != "converged" and r[k]["stall_at"] is not None for k in ks)
                    dv = sum(r[k]["status"] != "converged" and r[k]["diverged"] for k in ks)
                    print(f"| {case} | {grid} | {c} | {ro} | {conv} | {st} | {dv} | {len(ks) - conv - st - dv} | {len(ks)} |")


if __name__ == "__main__":
    sec = sys.argv[1] if len(sys.argv) > 1 else "main"
    if sec == "main":
        section_main("0.01")
        section_main("None")
    elif sec == "rob":
        section_rob()
