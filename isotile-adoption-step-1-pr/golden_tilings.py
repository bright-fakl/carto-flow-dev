"""Writes the golden fixtures of the tilings, from the tactile-based tiling code of carto-flow a9b4b7f.

    PYTHONPATH=<checkout of a9b4b7f>/src python golden_tilings.py <output directory>

Writes ``tilings.npz`` (G1: 19 named cases, 15 presets, 81 types), ``symbols.npz`` (G2: unit polygons of the symbols of
the 15 presets) and ``saved_cartogram.json`` (G5: a SymbolCartogram written by ``save``).

Per tiling case the old ``generate`` output is reduced to what the new code is compared with: the tiles that overlap the
requested region (with the margin) with positive area, as the center, rotation and flip of each tile, the old canonical
tile, and the edge and vertex-only adjacency pairs among these tiles. The script checks that the polygons of the old
result are the canonical tile placed by these transforms, so that the polygons can be rebuilt from the fixture.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import shapely
from shapely.affinity import rotate, translate
from shapely.geometry import Polygon, box

from carto_flow.symbol_cartogram.tiling import (
    HexagonTiling,
    IsohedralTiling,
    QuadrilateralTiling,
    SquareTiling,
    TriangleTiling,
)

BOUNDS = (-1.0, -1.0, 1.0, 1.0)
MARGIN = 0.1
REGION = (-1.2, -1.2, 1.2, 1.2)  # BOUNDS with the margin
N_TILES = 100  # presets and types
TILE_SIZE = 0.2
HEX_TILE_SIZE = 0.12  # circumradius

NAMED = [
    ("SquareTiling()", SquareTiling(), TILE_SIZE),
    ("HexagonTiling(pointy_top=True)", HexagonTiling(pointy_top=True), HEX_TILE_SIZE),
    ("HexagonTiling(pointy_top=False)", HexagonTiling(pointy_top=False), HEX_TILE_SIZE),
    ("TriangleTiling.equilateral()", TriangleTiling.equilateral(), TILE_SIZE),
    ("TriangleTiling.right_isosceles()", TriangleTiling.right_isosceles(), TILE_SIZE),
    ("TriangleTiling.right(2.0)", TriangleTiling.right(2.0), TILE_SIZE),
    ("TriangleTiling.right(0.3)", TriangleTiling.right(0.3), TILE_SIZE),
    ("TriangleTiling.isosceles(30)", TriangleTiling.isosceles(30.0), TILE_SIZE),
    ("TriangleTiling.isosceles(120)", TriangleTiling.isosceles(120.0), TILE_SIZE),
    (
        "TriangleTiling.from_polygon(clockwise scalene)",
        TriangleTiling.from_polygon(Polygon([(0, 0), (0.3, 1.0), (1.7, 0.2)])),
        TILE_SIZE,
    ),
    ("QuadrilateralTiling.parallelogram(60, 1)", QuadrilateralTiling.parallelogram(), TILE_SIZE),
    ("QuadrilateralTiling.parallelogram(75, 1.7)", QuadrilateralTiling.parallelogram(75.0, 1.7), TILE_SIZE),
    ("QuadrilateralTiling.rectangle(1)", QuadrilateralTiling.rectangle(), TILE_SIZE),
    ("QuadrilateralTiling.rectangle(2.5)", QuadrilateralTiling.rectangle(2.5), TILE_SIZE),
    ("QuadrilateralTiling.rhombus(45)", QuadrilateralTiling.rhombus(45.0), TILE_SIZE),
    ("QuadrilateralTiling.trapezoid(0.5, 1)", QuadrilateralTiling.trapezoid(), TILE_SIZE),
    ("QuadrilateralTiling.trapezoid(0.2, 0.6)", QuadrilateralTiling.trapezoid(0.2, 0.6), TILE_SIZE),
    (
        "QuadrilateralTiling.from_polygon(convex)",
        QuadrilateralTiling.from_polygon(Polygon([(0, 0), (1.2, 0.1), (1.0, 0.9), (0.1, 0.7)])),
        TILE_SIZE,
    ),
    (
        "QuadrilateralTiling.from_polygon(non-convex)",
        QuadrilateralTiling.from_polygon(Polygon([(0, 0), (1.5, 0.0), (0.6, 0.5), (0.0, 1.2)])),
        TILE_SIZE,
    ),
]


def place(canonical: Polygon, center, rotation: float, flipped: bool) -> Polygon:
    """The canonical tile (centered at its centroid) flipped about the vertical axis, rotated, and moved to ``center``."""
    p = canonical
    if flipped:
        p = shapely.affinity.scale(p, xfact=-1.0, yfact=1.0, origin=(0, 0))
    p = rotate(p, rotation, origin=(0, 0))
    return translate(p, center[0], center[1])


def pairs(matrix: np.ndarray, keep: np.ndarray) -> np.ndarray:
    sub = np.asarray(matrix)[np.ix_(keep, keep)]
    return np.argwhere(np.triu(sub, 1)).astype(np.int32)


def reduce_case(tiling, **kwargs) -> dict:
    res = tiling.generate(bounds=BOUNDS, margin=MARGIN, **kwargs)
    s = res.tile_size
    region = box(*REGION)
    overlap = np.array([p.intersection(region).area for p in res.polygons])
    keep = np.flatnonzero(overlap > 1e-9 * s * s)
    centers = np.array([res.transforms[i].center for i in keep])
    rotation = np.array([res.transforms[i].rotation for i in keep])
    flipped = np.array([res.transforms[i].flipped for i in keep])
    canonical = np.array(res.canonical_tile.exterior.coords[:-1])
    # the polygons of the old result are the canonical tile placed by the transforms
    for k, i in enumerate(keep):
        rebuilt = place(res.canonical_tile, centers[k], rotation[k], bool(flipped[k]))
        a = np.array(rebuilt.exterior.coords)
        b = np.array(res.polygons[i].exterior.coords)
        # same vertex order for the families (the old polygons are transformed copies of the canonical tile);
        # as sets for the isohedral tilings, whose polygons start at another vertex after make_valid or flips
        gap = max(
            np.linalg.norm(a[:, None] - b[None], axis=2).min(axis=1).max(),
            np.linalg.norm(a[:, None] - b[None], axis=2).min(axis=0).max(),
        )
        assert gap < 1e-9 * s, (gap, i)
    return {
        "tile_size": float(s),
        "n_old_total": len(res.polygons),
        "n_old_kept": len(keep),
        "centers": centers,
        "rotation": rotation,
        "flipped": flipped,
        "canonical": canonical,
        "edge_pairs": pairs(res.adjacency, keep),
        "vertex_pairs": pairs(res.vertex_adjacency, keep),
    }


def tilings(out: Path) -> None:
    arrays: dict[str, np.ndarray] = {}
    meta: dict[str, dict] = {}

    def add(key: str, data: dict, extra: dict) -> None:
        for name in ("centers", "rotation", "flipped", "canonical", "edge_pairs", "vertex_pairs"):
            arrays[f"{key}/{name}"] = data[name]
        meta[key] = {
            "tile_size": data["tile_size"],
            "n_old_total": data["n_old_total"],
            "n_old_kept": data["n_old_kept"],
            **extra,
        }

    for name, tiling, size in NAMED:
        add(f"named/{name}", reduce_case(tiling, tile_size=size), {"tile_size_argument": size})
    for name in IsohedralTiling._PRESETS:
        add(f"preset/{name}", reduce_case(IsohedralTiling.from_preset(name), n_tiles=N_TILES), {"n_tiles": N_TILES})
    for number in IsohedralTiling.available_types():
        add(f"type/{number}", reduce_case(IsohedralTiling(number), n_tiles=N_TILES), {"n_tiles": N_TILES})
    arrays["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(out / "tilings.npz", **arrays)
    print("tilings.npz", (out / "tilings.npz").stat().st_size, "bytes,", len(meta), "cases")


def symbols(out: Path) -> None:
    arrays = {}
    for name in IsohedralTiling._PRESETS:
        sym = IsohedralTiling.from_preset(name).canonical_symbol()
        arrays[f"{name}/unit_polygon"] = np.array(sym.unit_polygon().exterior.coords[:-1])
        arrays[f"{name}/radii"] = np.array([sym.bounding_radius, sym.inscribed_radius])
    np.savez_compressed(out / "symbols.npz", **arrays)
    print("symbols.npz", (out / "symbols.npz").stat().st_size, "bytes")


def saved(out: Path) -> None:
    import geopandas as gpd

    from carto_flow.symbol_cartogram import GridBasedLayout, create_symbol_cartogram

    rng = np.random.default_rng(42)
    geoms = [box(c, r, c + 1, r + 1) for r in range(3) for c in range(3)]
    gdf = gpd.GeoDataFrame({"population": rng.integers(100, 10000, size=9).astype(float)}, geometry=geoms)
    result = create_symbol_cartogram(gdf, "population", layout=GridBasedLayout(tiling="hexagon"), show_progress=False)
    path = out / "saved_cartogram.json"
    result.save(path)
    print("saved_cartogram.json", (out / "saved_cartogram.json").stat().st_size, "bytes")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    tilings(target)
    symbols(target)
    saved(target)
