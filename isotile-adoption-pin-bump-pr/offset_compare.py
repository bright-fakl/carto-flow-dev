"""Compare two experiments.py pickles (offsets, mosaic rotation) on assignments, regions and tile polygons: python offset_compare.py a.pkl b.pkl"""
import pickle
import sys

import numpy as np

a = pickle.load(open(sys.argv[1], "rb"))
b = pickle.load(open(sys.argv[2], "rb"))
bad = 0
for k in a:
    x, y = a[k], b[k]
    same = (
        np.array_equal(x["assignments"], y["assignments"])
        and np.array_equal(x["regions"], y["regions"])
        and x["lattice_tiles"] == y["lattice_tiles"]
        and np.all(x["polygons"] == y["polygons"])
        and x["tile_size"] == y["tile_size"]
    )
    bad += not same
    print(f"{k}: {'identical' if same else 'DIFFERENT'} ({x['lattice_tiles']} lattice tiles)")
print("ALL IDENTICAL" if not bad else f"{bad} DIFFER")
