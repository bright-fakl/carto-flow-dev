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
out += ["\n## Two squares after the remap (grid 256), observed / expected by distance to the shared border\n", f"| sectors | dots outside their region | when | region | share of the region's dots inside it | {hdr} |", "|---|---|---|---|---|" + "---|" * (len(edges) - 1)]
for r in tr["rows"]:
    for when in ("before", "after"):
        for k in ("0", "1"):
            ins = "-" if when == "before" else f"{r['inside_own'][k]:.3f}"
            out.append(f"| {r['sectors']} | {'pulled back' if r['signed'] else 'left alone'} | {when} | {'A' if k == '0' else 'B'} | {ins} | " + " | ".join("-" if v is None else f"{v:.2f}" for v in r[when][k]) + " |")

w = json.loads((D / "landmark_warp.json").read_text())
out += ["\n## Original map and the flow, z-score of the border band per dot seed\n", "| seed | original map | carried by the flow |", "|---|---|---|"]
out += [f"| {i} | {a} | {b} |" for i, (a, b) in enumerate(zip(w["original_z"], w["flow_z"]))]
out.append(f"| mean | {statistics.mean(w['original_z']):.2f} | {statistics.mean(w['flow_z']):.2f} |")
out += ["\n## Reference-point warp (thin-plate spline through boundary vertices and carried interior points), 8 seeds\n", "| boundary vertices | interior points | z mean (sd) | dots inside their region | shift against the flow: median / 95th pct | carried tracers against the warp: median / 95th pct |", "|---|---|---|---|---|---|"]
out += [f"| {r['boundary_vertices']} | {r['interior_points']} | {r['z_mean']} ({r['z_sd']}) | {r['inside']} | {r['shift_vs_flow_median']} / {r['shift_vs_flow_p95']} | {r['tracer_diff_median']} / {r['tracer_diff_p95']} |" for r in w["variants"]]
pe = w["profiles"]["edges"]
ph = " | ".join(f"{a:g}-{b:g}" for a, b in zip(pe[:-1], pe[1:]))
out += ["\n## Pooled distance profile on the states, observed / expected (mean over 8 seeds)\n", f"| dots | {ph} |", "|---|" + "---|" * (len(pe) - 1)]
out += [f"| {k} | " + " | ".join(f"{x:.2f}" for x in v) + " |" for k, v in w["profiles"]["rows"].items()]
v = json.loads((D / "velocity_profile.json").read_text())
ve = v["edges"]
vh = " | ".join(f"{a:g}-{b:g}" for a, b in zip(ve[:-1], ve[1:]))
out += ["\n## Velocity field against the distance to the border (median over the regions, states)\n", "Divergence relative to its value deep inside the region (1 = uniform scaling), and normal velocity (outward) divided by divergence x sqrt(area); the disk with uniform scaling gives 0.282 at the border and falls with slope -0.5.\n", f"| grid | field | quantity | {vh} |", "|---|---|---|" + "---|" * (len(ve) - 1)]
for g in ("grid 128", "grid 256", "grid 512"):
    for tag in ("first", "last"):
        out.append(f"| {g} | {tag} | divergence | " + " | ".join(f"{x:.2f}" for x in v[g][tag]["div"]) + " |")
        out.append(f"| {g} | {tag} | normal velocity | " + " | ".join(f"{x:.2f}" for x in v[g][tag]["vn"]) + " |")

j = json.loads((D / "jacobian_path.json").read_text())
je = j["edges"]
jh = " | ".join(f"{a:g}-{b:g}" for a, b in zip(je[:-1], je[1:]))
out += ["\n## Dot density predicted from the velocity field along the dot paths, against the observed one (states, grid 256, 8 seeds)\n", f"The step of every iteration is fitted from the displacements of the dots; the residual of the fit is {j['fit'][0]:.4f} (median) and {j['fit'][1]:.4f} (95th percentile). Predicted: harmonic mean of exp(-log J) times the area ratio over the dots in the bin.\n", f"| regions | | {jh} |", "|---|---|" + "---|" * (len(je) - 1)]
for cls in ("expanding", "shrinking"):
    for k in ("observed", "predicted"):
        out.append(f"| {cls} | {k} | " + " | ".join(f"{x:.2f}" for x in j["pooled"][cls][k]) + " |")
out += ["\n## Remap from the velocity field (no tracers), z-score of the border band\n", "| seed | before | after | shift: median / 95th pct (in sqrt(area)) |", "|---|---|---|---|"]
out += [f"| {r['seed']} | {r['before']} | {r['proxy']} | {r['shift_median']} / {r['shift_p95']} |" for r in j["seeds"]]
out.append(f"| mean | {statistics.mean([r['before'] for r in j['seeds']]):.2f} | {statistics.mean([r['proxy'] for r in j['seeds']]):.2f} | |")
ip = json.loads((D / "inplace_proxy.json").read_text())
sp = json.loads((D / "inplace_sampled.json").read_text())
out += ["\n## Without snapshots: the area scaling summed in place, and the first velocity field only (states, grid 256, 8 seeds)\n", "`inplace`: log J summed during the morph (no `save_internals`, no `snapshot_every`); F of the remap from 400 sample points per region. `first field only`: the divergence profile of the first velocity field per region and the area ratio of the region, no sum along the paths (F from polygon buffers).\n", "| seed | before | in place (sampled F) | first field only |", "|---|---|---|---|"]
out += [f"| {a['seed']} | {a['before']} | {a['inplace']} | {b['first_field']} |" for a, b in zip(sp["seeds"], ip["seeds"])]
out.append(f"| mean | {statistics.mean([r['before'] for r in sp['seeds']]):.2f} | {statistics.mean([r['inplace'] for r in sp['seeds']]):.2f} | {statistics.mean([r['first_field'] for r in ip['seeds']]):.2f} |")
cs = json.loads((D / "cost.json").read_text())
out += ["\n## Cost of the correction (states, one dot seed with %d dots, grid 256, %d iterations)\n" % (cs["landmarks"], cs["iterations"]), f"Morph time without the sum in place: {', '.join(str(x) for x in cs['morph_seconds_without'])} s (3 runs after a warm-up); with the sum in place in a Python wrapper: {', '.join(str(x) for x in cs['morph_seconds_with'])} s, of which {', '.join(str(x) for x in cs['seconds_in_the_sum'])} s in the sum itself. Memory: one float per dot, and the divergence of the current field (one grid) while it is in use.\n", "| remap | seconds | z after (before: %s) | median shift (x sqrt(area)) |" % cs["z_before"], "|---|---|---|---|"]
out += [f"| {r['grid_points'] if isinstance(r['grid_points'], str) else str(r['grid_points']) + ' distance points, polygon buffers'} | {r['seconds']} | {r['z']} | {r['shift_median']} |" for r in cs["remap"]]
sc_ = json.loads((D / "sections.json").read_text())
out += ["\n## Border sections: do they differ, and does a per-section correction help? (states, grid 256, 8 seeds)\n", "A morph with the dots and, per region, probe points along the inward normals at 24 points spread along the border (11 distances from 0 to 12 cells and 4 from 0.1 to 0.3 of sqrt(area)), all with the area scaling summed in place. Remaps of the dots, z-score of the border band: pooled c(d) from the dots (PR 133); per-section c(d) from the probes with a first-order strip remap (d' = w C(d) / C(w)); pooled c(d) from the probes with the full remap of PR 133.\n", "| seed | before | pooled, from the dots | per section, strip, from the probes | pooled, from the probes |", "|---|---|---|---|---|"]
out += [f"| {r['seed']} | {r['before']} | {r['pooled_from_dots']} | {r['sections_from_probes']} | {r['pooled_from_probes']} |" for r in sc_["seeds"]]
out.append("| mean | " + " | ".join(f"{statistics.mean([r[k] for r in sc_['seeds']]):.2f}" for k in ("before", "pooled_from_dots", "sections_from_probes", "pooled_from_probes")) + " |")
kh = " | ".join(f"{a:g}-{b:g}" for a, b in zip(je[:-1], je[1:]))
out += ["\n### Dot density by the kind of border section (the nearest border section faces another state or the outside)\n", f"| border | | {kh} |", "|---|---|" + "---|" * (len(je) - 1)]
for name, d_ in sc_["kinds"].items():
    for key, lab in (("observed", "observed / expected"), ("predicted_by_kind", "predicted from the probes of that kind"), ("predicted_pooled", "predicted from the pooled probes")):
        out.append(f"| {name} | {lab} | " + " | ".join(f"{x:.2f}" for x in d_[key]) + " |")
out += ["\n### Florida: crowding c = (A_final / A_original) / J of the probes by border section\n", "| section | neighbor | c at 1 cell | c at 3 cells | c at 0.2 sqrt(area) |", "|---|---|---|---|---|"]
out += [f"| {r['section']} | {r['neighbor']} | {r['c_at_1_cell']} | {r['c_at_3_cells']} | {r['c_at_0.2']} |" for r in sc_["florida"]]
(D / "tables.md").write_text("\n".join(out) + "\n")
