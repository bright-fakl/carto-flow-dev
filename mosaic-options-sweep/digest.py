"""Compact per-knob digest: effect size vs default, integrity screen, pathologies."""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = ["states_uniform", "states_uniform_sq", "states", "districts", "world"]
KEY = [("disp","displacement.median_tiles"),("adj","adjacency.frac_edge_adjacent"),
       ("dir","direction.median_abs_dev_deg"),("pp","compactness.polsby_popper_median"),
       ("iou","silhouette_vs_original.iou_aligned")]

def get(r,p):
    c=r
    for k in p.split("."):
        if not isinstance(c,dict) or k not in c: return None
        c=c[k]
    return c

def dq(r):
    it=r.get("integrity") or {}
    return (it.get("n_noncontiguous_regions") or 0, it.get("n_split_groups_component_adjusted") or 0,
            it.get("n_unassigned_core_tiles") or 0, it.get("n_enclosed_unassigned_tiles") or 0,
            it.get("tiles_short_total") or 0)

rows=[json.loads(l) for l in open(HERE/"results.jsonl") if l.strip()]
ok=[r for r in rows if "error" not in r]
base={(r["case"],r["morph"]):r for r in ok if r["knob"]=="baseline"}
knobs=[]
for r in ok:
    if r["knob"]!="baseline" and r["knob"] not in knobs: knobs.append(r["knob"])

print("### baseline integrity (noncontig, split, unassigned_core, enclosed, short)")
for (c,m),b in sorted(base.items()):
    print(f"  {c:18s} morph={int(m)} {dq(b)}  tile_size={b['tiling']['tile_size']:.0f} assigned={b['tiling']['n_assigned_tiles']}")

for knob in knobs:
    print(f"\n=== {knob}")
    for case in CASES:
        for morph in (True,False):
            sel=[r for r in ok if r["knob"]==knob and r["case"]==case and r["morph"]==morph]
            b=base[(case,morph)]
            if not sel: continue
            parts=[]
            for nm,p in KEY:
                bv=get(b,p)
                vals=[(r["value"],get(r,p)) for r in sel if get(r,p) is not None]
                if bv is None or not vals: continue
                dev=max(vals,key=lambda kv: abs(kv[1]-bv))
                parts.append(f"{nm} base={bv:.3f} worstdev={dev[1]-bv:+.3f}@{dev[0]}")
            bad=[(r["value"],dq(r)) for r in sel if dq(r)!=(0,0,0,0,0) and (dq(r)[0]>dq(b)[0] or dq(r)[1]>dq(b)[1] or dq(r)[4]>dq(b)[4])]
            print(f"  {case:18s} m={int(morph)} " + " | ".join(parts))
            if bad: print(f"      DQ: {bad}")
