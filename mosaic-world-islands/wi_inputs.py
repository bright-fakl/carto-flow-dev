"""Inputs for the mosaic world-islands investigation.

Three inputs: africa (clean control), world (failing), world_mainland
(world with island states dropped).  ``load_world_gdf`` is reused verbatim
from ``mosaic-options-sweep/inputs.py`` with a parametrisable tile budget.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "mosaic-options-sweep"))
sys.path.insert(0, str(HERE.parent / "grid-vs-mosaic-similarity"))

WORLD_CRS = "ESRI:54009"


def _prep(g, budget):
    import shapely

    g = g.copy()
    g["geometry"] = [shapely.make_valid(x).buffer(0) for x in g.geometry]
    pop = g["pop_est"].to_numpy(dtype=float)
    g["tiles"] = np.maximum(1, np.round(pop / pop.sum() * budget)).astype(int)
    return g.reset_index(drop=True)


def _world_raw():
    from carto_flow import data as cfdata

    g = cfdata.load_world()
    return g[(g["name"] != "Antarctica") & (g["pop_est"] > 0)].copy().to_crs(WORLD_CRS)


def load_world(budget=384):
    return _prep(_world_raw(), budget)


def load_africa(budget=300):
    g = _world_raw()
    return _prep(g[g["continent"] == "Africa"], budget)


def components_of(gdf, tol=None):
    """Adjacency-graph connected components (same utility the layout uses)."""
    from carto_flow.geo_utils.adjacency import find_adjacent_pairs

    n = len(gdf)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, j, _ in find_adjacent_pairs(list(gdf.geometry)):
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
    comps = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(i)
    return list(comps.values())


def load_world_mainland(budget=384):
    """World restricted to the single mainland land mass.

    Criterion: keep only the countries in the **largest connected component
    of the land-adjacency graph**; drop every other component.  On this input
    that component holds 150 of 176 countries - all of Afro-Eurasia plus the
    Americas, which are linked to Europe because Natural Earth's France
    polygon includes French Guiana, which borders Brazil and Suriname.  The
    26 dropped countries form 23 separate island components (Australia,
    Japan, Cuba, the UK+Ireland pair, Fiji, ...), i.e. exactly the regions
    the layout has to give a tile pool of their own.
    """
    g = _prep(_world_raw(), budget)
    comps = components_of(g)
    biggest = max(comps, key=len)
    keep = sorted(biggest)
    dropped = [str(g["name"].iloc[i]) for i in range(len(g)) if i not in set(keep)]
    out = g.iloc[keep].reset_index(drop=True)
    pop = out["pop_est"].to_numpy(dtype=float)
    out["tiles"] = np.maximum(1, np.round(pop / pop.sum() * budget)).astype(int)
    return out, dropped


CASES = {
    "africa": (lambda b=150: load_africa(b), "tiles"),
    "world": (load_world, "tiles"),
    "world_mainland": (lambda b=384: load_world_mainland(b)[0], "tiles"),
}
