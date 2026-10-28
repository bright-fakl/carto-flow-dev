"""Tables of the repair-cost measurement: python repair_table.py repair_old.json repair_new.json"""

import json
import sys

old = {(r["input"], r["tiling"]): r for r in json.load(open(sys.argv[1]))}
new = {(r["input"], r["tiling"]): r for r in json.load(open(sys.argv[2]))}


def st(r, k):
    return r["best"]["stages"].get(k, {"seconds": 0.0, "calls": 0})


print("| input | tiling | wall old / new (s) | calibrate old / new | hungarian old / new | ring relocation old / new | chain swap old / new | _count_split_units calls old / new |")
print("|---|---|---|---|---|---|---|---|")
for key in old:
    a, b = old[key], new[key]
    cells = [
        f"{a['best']['wall']:.2f} / {b['best']['wall']:.2f}",
        f"{st(a,'calibrate_tiling')['seconds']:.2f} / {st(b,'calibrate_tiling')['seconds']:.2f}",
        f"{st(a,'hungarian_morphed_assignment')['seconds']:.2f} / {st(b,'hungarian_morphed_assignment')['seconds']:.2f}",
        f"{st(a,'_relocate_ring_tiles')['seconds']:.2f} / {st(b,'_relocate_ring_tiles')['seconds']:.2f}",
        f"{st(a,'_chain_swap_repair')['seconds']:.2f} / {st(b,'_chain_swap_repair')['seconds']:.2f}",
        f"{st(a,'_count_split_units')['calls']} / {st(b,'_count_split_units')['calls']}",
    ]
    print(f"| {key[0]} | {key[1]} | " + " | ".join(cells) + " |")
print()
print("| input | tiling | lattice tiles | hungarian passes | ring tiles relocated | contiguity passes / swaps | chain swap before -> after | noncontiguous regions | split groups | unassigned core | enclosed |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for key in old:
    row = []
    for r in (old[key], new[key]):
        w = r["work"]
        chain = ";".join(f"{c['before']}->{c['after']} {c['result']}" for c in w["chain_swap"]) or "-"
        row.append((w["lattice_tiles"], w["hungarian_repair_passes"], sum(w["ring_relocated"]), f"{w['contiguity_passes']}/{w['contiguity_swaps']}", chain, w["noncontiguous_regions"], w["split_groups"], w["unassigned_core_tiles"], w["enclosed_unassigned_tiles"]))
    print(f"| {key[0]} | {key[1]} | " + " | ".join(f"{x} / {y}" for x, y in zip(*row)) + " |")
