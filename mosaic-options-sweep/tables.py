"""Markdown tables + dead-zone / pathology detection from results.jsonl."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = ["states_uniform", "states_uniform_sq", "states", "districts", "world"]

M = [
    ("disp", "displacement.median_tiles", 3),
    ("adj", "adjacency.frac_edge_adjacent", 3),
    ("dir", "direction.median_abs_dev_deg", 2),
    ("pp", "compactness.polsby_popper_median", 3),
    ("iou", "silhouette_vs_original.iou_aligned", 3),
    ("noncontig", "integrity.n_noncontiguous_regions", 0),
    ("split", "integrity.n_split_groups_component_adjusted", 0),
    ("unassigned_core", "integrity.n_unassigned_core_tiles", 0),
    ("enclosed", "integrity.n_enclosed_unassigned_tiles", 0),
    ("short", "integrity.tiles_short_total", 0),
    ("wall_s", "wall_clock_s", 1),
]


def get(rec, path):
    cur = rec
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def fmt(v, nd):
    if v is None:
        return "-"
    if nd == 0:
        return str(int(v))
    return f"{v:.{nd}f}"


def load():
    rows = []
    with (HERE / "results.jsonl").open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def vkey(r, knob):
    v = r["value"]
    if r["knob"] == "baseline":
        return "default"
    if isinstance(v, list):
        return f"dw={v[0]},op={v[1]}"
    return str(v)


def main():
    rows = load()
    errs = [r for r in rows if "error" in r]
    ok = [r for r in rows if "error" not in r]
    out = []
    out.append(f"Runs: {len(ok)} successful, {len(errs)} errors.\n")
    if errs:
        for e in errs:
            out.append(f"- ERROR `{e.get('run')}`: {e['error'].splitlines()[-1]}")
        out.append("")

    base = {(r["case"], r["morph"]): r for r in ok if r["knob"] == "baseline"}
    knobs = []
    for r in ok:
        if r["knob"] != "baseline" and r["knob"] not in knobs:
            knobs.append(r["knob"])

    # ---- dead zones -------------------------------------------------
    out.append("## Identity groups (dead zones)\n")
    out.append("Values whose full assignment fingerprint is byte-identical. `*` marks the group containing the default.\n")
    out.append("| knob | case | morph | identical groups |")
    out.append("|---|---|---|---|")
    for knob in knobs:
        for case in CASES:
            for morph in (True, False):
                sel = [r for r in ok if r["knob"] == knob and r["case"] == case and r["morph"] == morph]
                b = base.get((case, morph))
                if b is not None and knob in b.get("opts", {}) and knob != "tile_size":
                    sel = sel + [dict(b, value=b["opts"][knob], knob=knob)]
                if not sel:
                    continue
                groups = defaultdict(list)
                for r in sel:
                    groups[r["fingerprint"]].append(vkey(r, knob))
                desc = []
                for fp, vals in groups.items():
                    star = "*" if b is not None and fp == b["fingerprint"] else ""
                    desc.append("{" + ", ".join(sorted(vals, key=_sortk)) + "}" + star)
                out.append(f"| {knob} | {case} | {morph} | {' '.join(desc)} |")
    out.append("")

    # ---- per-knob metric tables -------------------------------------
    for knob in knobs:
        out.append(f"\n## {knob}\n")
        hdr = "| case | morph | value | " + " | ".join(n for n, _, _ in M) + " | fp |"
        out.append(hdr)
        out.append("|" + "---|" * (len(M) + 4))
        for case in CASES:
            for morph in (True, False):
                sel = [r for r in ok if r["knob"] == knob and r["case"] == case and r["morph"] == morph]
                b = base.get((case, morph))
                if b is not None:
                    sel = sel + [dict(b, knob=knob)]
                sel.sort(key=lambda r: _sortk(vkey(r, knob)))
                for r in sel:
                    cells = [fmt(get(r, p), nd) for _, p, nd in M]
                    label = vkey(r, knob)
                    if r["knob"] == "baseline":
                        label = f"**default**"
                    out.append(
                        f"| {case} | {morph} | {label} | " + " | ".join(cells) + f" | `{r['fingerprint'][:6]}` |"
                    )
        out.append("")

    (HERE / "tables.md").write_text("\n".join(out))
    print("wrote tables.md", len(out), "lines")


def _sortk(s):
    try:
        return (0, float(s), "")
    except (TypeError, ValueError):
        return (1, 0.0, str(s))


if __name__ == "__main__":
    main()
