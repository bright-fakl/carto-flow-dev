"""Compare the footprints (set of (region, tile polygon) pairs) of two layout runs: python footprints.py old.pkl new.pkl"""
import pickle
import sys

import shapely

a = pickle.load(open(sys.argv[1], "rb"))
b = pickle.load(open(sys.argv[2], "rb"))


def foot(r):
    return sorted((g, shapely.to_wkt(shapely.from_wkb(w), rounding_precision=6)) for g, w in zip(r["tile_region"], r["tile_polygons_wkb"], strict=True))


print("| case | lattice tiles old / new | footprints identical |")
print("|---|---|---|")
for k in a:
    print(f"| {k} | {a[k]['lattice_tiles']} / {b[k]['lattice_tiles']} | {'yes' if foot(a[k]) == foot(b[k]) else 'NO'} |")
