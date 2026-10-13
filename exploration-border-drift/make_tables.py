"""Writes data/tables.md from the JSON files of border_band.py, resolution_scan.py, two_regions.py, distance_remap.py,
sector_remap.py and toy_remap.py."""
import json
from pathlib import Path

import statistics

HERE = Path(__file__).resolve().parent
D = HERE / "data"
out = []

b = json.loads((D / "border_band_seed7.json").read_text())
out += ["## Border band z-score on the current code (dot seed 7)\n", "| variant | status | iterations | observed vs expected | z |", "|---|---|---|---|---|"]
out += [f"| {r['variant']} | {r['status']} | {r['iterations']} | {r['observed']} vs {r['expected']} | {r['z']} |" for r in b]

s = json.loads((D / "resolution_scan_128_256_512_1024.json").read_text())
out += ["\n## Field recomputed every iteration, grid size\n", "| variant | status | iterations | observed vs expected | z |", "|---|---|---|---|---|"]
out += [f"| {r['variant']} | {r['status']} | {r['iterations']} | {r['observed']} vs {r['expected']} | {r['z']} |" for r in s]

t = json.loads((D / "two_regions.json").read_text())
edges = t["edges"]
hdr = " | ".join(f"{a:g}-{b:g}" for a, b in zip(edges[:-1], edges[1:]))
out += ["\n## Two squares (A: value 1, B: value 4), observed / expected dots by distance to the shared border (in sqrt(area))\n", f"| variant | region | {hdr} |", "|---|---|" + "---|" * (len(edges) - 1)]
for r in t["rows"]:
    for k in ("0", "1"):
        out.append(f"| {r['variant']} | {'A' if k == '0' else 'B'} | " + " | ".join("-" if v is None else f"{v:.2f}" for v in r["ratio_by_distance"][k]) + " |")

d = json.loads((D / "distance_remap_states.json").read_text())["states"]
out += ["\n## Distance remap on the states, 8 dot seeds (z-score of the border band)\n", "| seed | before | per region | pooled | shift per region: median / 95th pct / max (in sqrt(area)) | shift pooled: median / 95th pct / max |", "|---|---|---|---|---|---|"]
for r in d["seeds"]:
    a, p = r["region"]["shift"], r["pooled"]["shift"]
    out.append(f"| {r['seed']} | {r['before']} | {r['region']['z']} | {r['pooled']['z']} | {a['median']} / {a['p95']} / {a['max']} | {p['median']} / {p['p95']} / {p['max']} |")
mean = lambda key: statistics.mean([r[key] if key == "before" else r[key]["z"] for r in d["seeds"]])
out.append(f"\nMean z over the seeds: before {mean('before'):.2f}, per region {mean('region'):.2f}, pooled {mean('pooled'):.2f}.")

sr = json.loads((D / "sector_remap.json").read_text())
out += ["\n## Fewer reference points and sectors around the centroid (states, 8 seeds; z before: mean %.2f)\n" % sr["before_mean"], "| sectors | tracers per region | z mean | z sd | z max | shift median | shift 95th pct |", "|---|---|---|---|---|---|---|"]
out += [f"| {r['sectors']} | {r['tracers_per_region']} | {r['z_mean']} | {r['z_sd']} | {r['z_max']} | {r['shift_median']} | {r['shift_p95']} |" for r in sr["rows"]]

tr = json.loads((D / "toy_remap.json").read_text())
out += ["\n## Two squares after the remap (grid 256), observed / expected by distance to the shared border\n", f"| sectors | when | region | {hdr} |", "|---|---|---|" + "---|" * (len(edges) - 1)]
for r in tr["rows"]:
    for when in ("before", "after"):
        for k in ("0", "1"):
            out.append(f"| {r['sectors']} | {when} | {'A' if k == '0' else 'B'} | " + " | ".join("-" if v is None else f"{v:.2f}" for v in r[when][k]) + " |")
(D / "tables.md").write_text("\n".join(out) + "\n")
