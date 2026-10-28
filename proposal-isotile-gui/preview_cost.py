"""Cost of the curved preview and what it buys.

`fill_region` selects tiles with the curved outline by default when the tiling has edge curves (`outline=None`). At the
preview size (100 tiles in a 2 x 0.6 window grown by margin 0.25) nearly every tile touches the boundary of the region, so the
curved test clips most of them.

1. Time of fill_region with outline "curved" and "straight" for the 15 presets and for the 72 types with a bump on every
   curvable shape id, and a cProfile of one curved call.
2. Does the straight selection miss tiles that reach into the visible window through their curves? For margin 0.25, 0.1 and
   0.0: tiles that overlap the window with positive area in the curved selection and are not in the straight selection.
3. The same for the export sizes (50, 100, 200 tiles in (-2,-2,2,2), margin 0.1).

Run: python preview_cost.py > preview_cost.txt
"""
from __future__ import annotations

import cProfile
import io
import pstats
import statistics
import time
import warnings

import numpy as np
import shapely

warnings.simplefilter("ignore")
import isotile  # noqa: E402
from isotile import IsohedralTiling as IT, check_prototile, get_type, tiling_types  # noqa: E402

WINDOW = (-1.0, -0.3, 1.0, 0.3)


def bump(t, amplitude=0.08):
    return {i: isotile.edge_curve_preset("bump", s, amplitude).tolist() for i, s in enumerate(t.shape_types) if s != "I"}


cases = [(f"preset {n}", IT.from_preset(n)) for n in isotile.list_presets() if IT.from_preset(n).edge_curves]
for n in tiling_types():
    c = bump(get_type(n))
    if c and check_prototile(n, edge_curves=c).valid:
        cases.append((f"IH{n} bump", IT(n, edge_curves=c)))
print(f"{len(cases)} curved cases ({sum(1 for c in cases if c[0].startswith('preset'))} presets)")


def ms(fn, k=3):
    best = 1e9
    for _ in range(2):
        t0 = time.perf_counter()
        for _ in range(k):
            fn()
        best = min(best, (time.perf_counter() - t0) / k * 1000)
    return best


for margin in (0.25,):
    tc = [ms(lambda t=t: t.fill_region(WINDOW, n_tiles=100, margin=margin, outline="curved")) for _, t in cases]
    ts = [ms(lambda t=t: t.fill_region(WINDOW, n_tiles=100, margin=margin, outline="straight")) for _, t in cases]
    print(f"fill_region 100 tiles, margin {margin}: curved median {statistics.median(tc):.1f} ms (max {max(tc):.1f}), straight median {statistics.median(ts):.2f} ms (max {max(ts):.2f})")

pr = cProfile.Profile()
t = IT.from_preset("puzzle_piece")
pr.enable()
for _ in range(5):
    t.fill_region(WINDOW, n_tiles=100, margin=0.25)
pr.disable()
s = io.StringIO()
pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(8)
print("\ncProfile, puzzle_piece, 5 calls of fill_region (curved):")
print("\n".join(l for l in s.getvalue().splitlines() if l.strip())[:2500])

win = shapely.box(*WINDOW)


def window_set(ts_, eps=1e-9):
    out = set()
    for k, p in enumerate(ts_.polygons()):
        if p.intersection(win).area / p.area > eps:
            out.add((int(ts_.cell[k, 0]), int(ts_.cell[k, 1]), int(ts_.aspect[k])))
    return out


print("\n== tiles of the visible window missed by the straight selection ==")
for margin in (0.25, 0.1, 0.0):
    miss_cases = 0
    miss_total = 0
    for _, t in cases:
        a = window_set(t.fill_region(WINDOW, n_tiles=100, margin=margin, outline="curved"))
        b = window_set(t.fill_region(WINDOW, n_tiles=100, margin=margin, outline="straight"))
        d = len(a - b)
        miss_total += d
        miss_cases += d > 0
    print(f"preview window, 100 tiles, margin {margin}: cases with a missed tile {miss_cases} of {len(cases)}, missed tiles in all cases {miss_total}")

print("\n== stress: bump of amplitude 0.3 on every curvable shape id (valid cases only) ==")
deep = []
for n in tiling_types():
    c = bump(get_type(n), 0.3)
    if c and check_prototile(n, edge_curves=c).valid:
        deep.append((f"IH{n} bump0.3", IT(n, edge_curves=c)))
print(f"{len(deep)} valid cases")
for margin in (0.25, 0.1):
    miss_cases = miss_total = 0
    for _, t in deep:
        a = window_set(t.fill_region(WINDOW, n_tiles=100, margin=margin, outline="curved"))
        b = window_set(t.fill_region(WINDOW, n_tiles=100, margin=margin, outline="straight"))
        miss_total += len(a - b)
        miss_cases += len(a - b) > 0
    print(f"preview window, 100 tiles, margin {margin}: cases with a missed tile {miss_cases} of {len(deep)}, missed tiles {miss_total}")

print("\n== export region (-2,-2,2,2), margin 0.1 ==")
EXPORT = (-2.0, -2.0, 2.0, 2.0)
win_e = shapely.box(*EXPORT)


def window_set_e(ts_, eps=1e-9):
    return {(int(ts_.cell[k, 0]), int(ts_.cell[k, 1]), int(ts_.aspect[k])) for k, p in enumerate(ts_.polygons()) if p.intersection(win_e).area / p.area > eps}


for n_tiles in (50, 100, 200):
    for label, group in (("15 presets + bump 0.08", cases), ("bump 0.3", deep)):
        miss_cases = miss_total = 0
        for _, t in group:
            a = window_set_e(t.fill_region(EXPORT, n_tiles=n_tiles, margin=0.1, outline="curved"))
            b = window_set_e(t.fill_region(EXPORT, n_tiles=n_tiles, margin=0.1, outline="straight"))
            miss_total += len(a - b)
            miss_cases += len(a - b) > 0
        print(f"{n_tiles:3d} tiles, {label}: straight selection misses a window tile in {miss_cases} of {len(group)} cases ({miss_total} tiles)")
