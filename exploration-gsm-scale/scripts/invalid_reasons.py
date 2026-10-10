"""Reasons and names of the invalid polygons of states grid 256 for A, B1, B2 (refresh on rise 0.01)."""
import collections

from common import *

g, col, sc, kw, n = load_case("states")
for k in ("A", "B1", "B2"):
    r, res = run_one(g, col, sc, 256, 400, VARIANTS[k][1], 0.01)
    geoms = np.asarray(list(res.latest.geometry), dtype=object)
    bad = ~shapely.is_valid(geoms)
    print(k, collections.Counter(x[:30] for x in shapely.is_valid_reason(geoms[bad])),
          list(g["State Abbreviation"][bad]) if "State Abbreviation" in g else "")
