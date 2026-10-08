"""Input definitions for the mosaic options sweep.

Reuses the three US inputs from ``grid-vs-mosaic-similarity`` and adds a
non-US input (world countries).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
GRID_WS = HERE.parent / "grid-vs-mosaic-similarity"
sys.path.insert(0, str(GRID_WS))

from metrics import build_study_union  # noqa: E402

N_TILES_STATES = 150
WORLD_CRS = "ESRI:54009"  # Mollweide: equal-area, so tile areas mean something
WORLD_BUDGET = 300


def load_states():
    from carto_flow.data import load_us_census

    states = load_us_census(population=True).reset_index(drop=True)
    pop = states["Population"].to_numpy(dtype=float)
    states["tiles"] = np.maximum(1, np.round(pop / pop.sum() * N_TILES_STATES)).astype(int)
    return states


def load_districts():
    from carto_flow.data import load_us_census

    return load_us_census(population=True, level="congressional_district").reset_index(drop=True)


def load_world_gdf():
    from carto_flow import data as cfdata

    g = cfdata.load_world()
    g = g[(g["name"] != "Antarctica") & (g["pop_est"] > 0)].copy().to_crs(WORLD_CRS)
    # Mollweide reprojection leaves self-intersecting rings; without this the
    # study-union build raises a GEOS side-location conflict.
    import shapely

    g["geometry"] = [shapely.make_valid(x).buffer(0) for x in g.geometry]
    pop = g["pop_est"].to_numpy(dtype=float)
    g["tiles"] = np.maximum(1, np.round(pop / pop.sum() * WORLD_BUDGET)).astype(int)
    return g.reset_index(drop=True)


def input_context(gdf, *, tile_count=None, group_by=None):
    from carto_flow.symbol_cartogram.adjacency import compute_adjacency
    from carto_flow.symbol_cartogram.options import AdjacencyMode

    cent = np.array([[g.centroid.x, g.centroid.y] for g in gdf.geometry])
    adj = compute_adjacency(gdf, mode=AdjacencyMode.BINARY)
    req = gdf[tile_count].to_numpy(dtype=int) if tile_count is not None else np.ones(len(gdf), dtype=int)
    groups = None
    if group_by is not None:
        _, groups = np.unique(gdf[group_by].to_numpy(), return_inverse=True)
    return {
        "orig_centroids": cent,
        "adjacency_G": adj,
        "requested_counts": req,
        "input_bounds": tuple(float(x) for x in gdf.total_bounds),
        "group_labels": groups,
        "study_union": build_study_union(gdf),
    }


CASES = {
    # name: (loader, tile_count, group_by, tiling)
    "states_uniform": (load_states, None, None, "hexagon"),
    "states_uniform_sq": (load_states, None, None, "square"),
    "states": (load_states, "tiles", None, "hexagon"),
    "districts": (load_districts, None, "State Name", "hexagon"),
    "world": (load_world_gdf, "tiles", None, "hexagon"),
}
