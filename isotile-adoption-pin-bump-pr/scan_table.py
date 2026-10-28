"""Tables of the offset scan: python scan_table.py old.json new.json straight.json

All 15 presets x 6 offsets x {grid, mosaic}: old pin (main) against new pin (branch). A case is listed when the mean
distance changes by more than 25 percent of the old value (the acceptance rule of the step 1 page) or when the number of
non-contiguous regions or unassigned core tiles (mosaic) rises. The third file (new pin, outline forced to straight)
shows that these cases return to the old values when the tile set is the old one.
"""

import json
import sys

old, new, st = (json.load(open(p)) for p in sys.argv[1:4])
rows = []
for k in old:
    a, b, c = old[k], new[k], st[k]
    ch = (b["mean"] - a["mean"]) / a["mean"]
    worse = b.get("noncontiguous", 0) > a.get("noncontiguous", 0) or b.get("unassigned_core", 0) > a.get("unassigned_core", 0)
    rows.append((k, a, b, c, ch, worse))

print(f"cases {len(rows)}; grid {sum('|grid|' in r[0] for r in rows)}, mosaic {sum('|mosaic|' in r[0] for r in rows)}")
same_tiles = sum(r[1]["lattice"] == r[2]["lattice"] for r in rows)
print(f"same lattice tile count old/new: {same_tiles}; different: {len(rows) - same_tiles}")
ident = sum(abs(r[1]["mean"] - r[2]["mean"]) < 1e-9 for r in rows)
print(f"mean distance equal to 1e-9: {ident}; straight-forced run equal to old: {sum(abs(r[1]['mean'] - r[3]['mean']) < 1e-9 for r in rows)}")
print()
print("| preset | layout | offset | lattice tiles old / new | mean distance old / new | change | non-contiguous old / new | unassigned core old / new | new pin, straight outline |")
print("|---|---|---|---|---|---|---|---|---|")
for k, a, b, c, ch, worse in rows:
    if abs(ch) < 1e-9 and not worse:
        continue
    name, kind, u, v = k.split("|")
    nc = f"{a.get('noncontiguous', '-')} / {b.get('noncontiguous', '-')}"
    uc = f"{a.get('unassigned_core', '-')} / {b.get('unassigned_core', '-')}"
    flag = " **beyond 25 %**" if abs(ch) > 0.25 else (" worse contiguity" if worse else "")
    print(f"| {name} | {kind} | ({u}, {v}) | {a['lattice']} / {b['lattice']} | {a['mean']:.3f} / {b['mean']:.3f} | {100 * ch:+.0f} %{flag} | {nc} | {uc} | {c['mean']:.3f} |")
