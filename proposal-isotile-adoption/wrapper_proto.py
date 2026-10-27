"""Prototype of the thin wrappers of the adoption design: carto-flow's tiling classes over isotile.

Builds a replacement for ``carto_flow/symbol_cartogram/tiling.py`` from the current file and the code below, writes it
into a copy of the carto-flow sources (never into the checkout), and leaves the rest of the sources unchanged. The copy
is then tested with carto-flow's own tests and used for the layout comparison (``golden_layouts.py``).

    python wrapper_proto.py <carto-flow checkout> <copy directory>      # copy directory holds src/ and tests/

What the replacement keeps: ``Tiling``, ``TilingResult``, ``TileTransform``, ``TileAdjacencyType``, the plotting
methods, ``resolve_tiling``, the constructors of the four families and their convenience classmethods, and
``IsohedralTiling(tiling_type, parameters, edge_curves, edge_curve_modes)``. What it replaces: every ``generate``, the
adjacency helpers, the tactile calls, the presets, the type metadata.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NEW_BASE = '''
# ---------------------------------------------------------------------------
# Tilings over isotile
# ---------------------------------------------------------------------------

#: Area of the regular hexagon with circumradius 1.
_HEX_AREA = 3.0 * math.sqrt(3.0) / 2.0

#: Set to ``False`` to return sparse adjacency in :class:`TilingResult` (the design of the second PR).
DENSE_ADJACENCY = True


def _orientation(m: NDArray[np.floating]) -> tuple[NDArray[np.floating], NDArray[np.bool_]]:
    """Rotation (degrees, carto-flow convention) and flip of 2x3 similarity maps."""
    det = m[:, 0, 0] * m[:, 1, 1] - m[:, 0, 1] * m[:, 1, 0]
    flipped = det < 0
    rot = np.degrees(np.where(flipped, np.arctan2(-m[:, 1, 0], -m[:, 0, 0]), np.arctan2(m[:, 1, 0], m[:, 0, 0])))
    return rot, flipped


class _IsotileTiling(Tiling):
    """A :class:`Tiling` that is an ``isotile.IsohedralTiling`` with a size convention.

    Subclasses set ``_iso`` (the isotile tiling, its frame giving the orientation) and ``_side_per_size``
    (``sqrt(tile area) = tile_size * _side_per_size``).
    """

    _iso: object
    _side_per_size: float = 1.0
    _n_vertices_label: int | None = None

    def generate(
        self,
        bounds: tuple[float, float, float, float] = DEFAULT_BOUNDS,
        n_tiles: int | None = None,
        tile_size: float | None = None,
        margin: float = 0.1,
        adjacency_type: TileAdjacencyType = TileAdjacencyType.EDGE,
        compute_adjacency: bool = True,
    ) -> TilingResult:
        bounds, n_tiles, tile_size = self._resolve_generate_args(bounds, n_tiles, tile_size)
        if tile_size is None:
            tiles = self._iso.fill_region(bounds, n_tiles=n_tiles, margin=margin)
        else:
            tiles = self._iso.fill_region(bounds, tile_size=tile_size * self._side_per_size, margin=margin)
        return self._result(tiles, adjacency_type, compute_adjacency)

    def _result(self, tiles, adjacency_type: TileAdjacencyType, compute_adjacency: bool) -> TilingResult:
        tiling = tiles.tiling
        tile_size = math.sqrt(tiling.area) / self._side_per_size
        polygons = tiles.polygons()
        centers = shapely.get_coordinates(shapely.centroid(np.asarray(polygons, dtype=object)))
        rotation, flipped = _orientation(tiles.transforms)
        transforms = [
            TileTransform(center=(float(c[0]), float(c[1])), rotation=float(r), flipped=bool(f))
            for c, r, f in zip(centers, rotation, flipped, strict=True)
        ]
        n = len(polygons)
        if compute_adjacency:
            kind = "edge" if adjacency_type == TileAdjacencyType.EDGE else "vertex"
            adj = tiles.adjacency(kind)
            vert = tiles.adjacency("vertex-only")
            if DENSE_ADJACENCY:
                adj, vert = adj.toarray(), vert.toarray()
        else:
            adj = vert = np.zeros((n, n), dtype=bool)
        outline = tiling.prototile(curved=True)
        canonical = Polygon(outline - shapely.centroid(Polygon(outline)).coords[0])
        return TilingResult(
            polygons=polygons,
            transforms=transforms,
            adjacency=adj,
            vertex_adjacency=vert,
            tile_size=tile_size,
            inscribed_radius=float(canonical.exterior.distance(Point(0.0, 0.0))),
            canonical_tile=canonical,
            n_base_vertices=self._n_vertices_label,
        )

    def rotated(self, angle: float):
        """The same tiling with the lattice rotated counterclockwise by ``angle`` degrees (about the region center)."""
        import copy

        new = copy.copy(self)
        new._iso = self._iso.rotated(angle)
        return new
'''

NEW_ISOHEDRAL = '''
class IsohedralTiling(_IsotileTiling):
    """Isohedral tiling of one of the 81 types, a :class:`Tiling` over ``isotile.IsohedralTiling``.

    The constructor arguments are those of the former tactile-based class. ``isotile`` is the underlying
    ``isotile.IsohedralTiling``; type metadata, presets and serialization are isotile's.
    """

    def __init__(self, tiling_type, parameters=None, edge_curves=None, edge_curve_modes=None) -> None:
        import isotile

        self._iso = isotile.IsohedralTiling(
            tiling_type,
            parameters,
            edge_curves=edge_curves,
            edge_curve_modes=edge_curve_modes,
        )
        self._finish()

    def _finish(self) -> None:
        self._n_vertices_label = self._iso.type.n_vertices
        outline = self._iso.prototile(normalized=True, curved=True)
        self._unit_tile = Polygon(outline - shapely.centroid(Polygon(outline)).coords[0])

    @property
    def isotile(self):
        """The underlying ``isotile.IsohedralTiling``."""
        return self._iso

    @property
    def _type(self) -> int:
        return self._iso.type.number

    @property
    def _edge_curves(self) -> dict:
        return {k: [tuple(p) for p in v] for k, v in self._iso.edge_curves.items()}

    @property
    def _edge_curve_modes(self) -> dict:
        return self._iso.edge_curve_modes

    @property
    def canonical_tile(self) -> Polygon:
        """Unit-area prototile centered at its area centroid."""
        return self._unit_tile

    @property
    def _n_base_vertices(self) -> int:
        return self._iso.type.n_vertices

    def canonical_symbol(self) -> Symbol:
        from .symbols import IsohedralTileSymbol

        return IsohedralTileSymbol(
            tiling_type=self._type,
            prototile_params=list(self._iso.parameters),
            edge_curves=self._edge_curves or None,
            edge_curve_modes=self._edge_curve_modes or None,
        )

    def tile_size_for_symbol_size(self, symbol_size: float, spacing: float = 0.0) -> float:
        coords = np.array(self._unit_tile.exterior.coords)
        r_orig = float(np.max(np.linalg.norm(coords, axis=1)))
        return (symbol_size / r_orig) * (1 + spacing)

    @classmethod
    def from_polygon(cls, polygon: Polygon) -> IsohedralTiling:
        raise NotImplementedError(
            "IsohedralTiling is defined by type number and parameters, "
            "not by polygon shape. Use IsohedralTiling(tiling_type=...) instead.",
        )

    @classmethod
    def _wrap(cls, iso) -> IsohedralTiling:
        new = cls.__new__(cls)
        new._iso = iso
        new._finish()
        return new

    # -- metadata, presets, serialization: isotile's, kept as delegates --------------------------------------

    @staticmethod
    def available_types() -> list[int]:
        import isotile

        return list(isotile.tiling_types())

    @staticmethod
    def find_types(**filters) -> list[int]:
        import isotile

        return isotile.find_types(**filters)

    @classmethod
    def from_preset(cls, name: str, **kwargs) -> IsohedralTiling:
        import isotile

        return cls._wrap(isotile.IsohedralTiling.from_preset(name, **kwargs))

    @classmethod
    def list_presets(cls) -> dict[str, str]:
        import isotile

        return isotile.list_presets()

    def to_dict(self) -> dict:
        return self._iso.to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> IsohedralTiling:
        import isotile

        return cls._wrap(isotile.IsohedralTiling.from_dict(data))

    def save(self, path) -> None:
        self._iso.save(path)

    @classmethod
    def load(cls, path) -> IsohedralTiling:
        import isotile

        return cls._wrap(isotile.IsohedralTiling.load(path))

    def type_info(self_or_type=None, tiling_type: int | None = None) -> dict:
        import isotile

        if isinstance(self_or_type, IsohedralTiling):
            return self_or_type._iso.type.info()
        number = self_or_type if isinstance(self_or_type, int) else tiling_type
        if number is None:
            raise TypeError("type_info() requires a tiling type number when called on the class")
        return isotile.get_type(number).info()

    def describe(self_or_type=None, tiling_type: int | None = None) -> str:
        import isotile

        if isinstance(self_or_type, IsohedralTiling):
            return self_or_type._iso.describe()
        number = self_or_type if isinstance(self_or_type, int) else tiling_type
        return isotile.get_type(number).describe()

    @styled
    def plot_prototile(self, ax=None, show_labels: bool = True):
        from isotile.plot import plot_prototile

        return plot_prototile(self._iso, ax=ax, show_labels=show_labels)
'''

SQUARE_INIT = '''
    _side_per_size = 1.0

    @property
    def _iso(self):
        import isotile

        return isotile.IsohedralTiling.square()
'''

HEX_INIT = '''
    _side_per_size = math.sqrt(_HEX_AREA)

    @property
    def _iso(self):
        import isotile

        return isotile.IsohedralTiling.hexagon(self.pointy_top)
'''

POLY_INIT = '''
    _side_per_size = 1.0

    @property
    def _iso(self):
        import isotile

        make = isotile.IsohedralTiling.triangle if len(self._unit_tile.exterior.coords) == 4 else isotile.IsohedralTiling.quadrilateral
        return make(np.array(self._unit_tile.exterior.coords[:-1]))
'''


def build(source: str) -> str:
    lines = source.split("\n")

    def find(prefix: str, start: int = 0) -> int:
        for i in range(start, len(lines)):
            if lines[i].startswith(prefix):
                return i
        raise KeyError(prefix)

    def cut_generate(class_prefix: str, init: str, next_marker: str) -> None:
        nonlocal lines
        c = find(class_prefix)
        g = next(i for i in range(c, len(lines)) if lines[i].startswith("    def generate("))
        end = next(i for i in range(g, len(lines)) if lines[i].startswith(next_marker))
        # insert the property after the class docstring/constructor: simply before generate
        lines[g:end] = init.split("\n") + ["", ""]

    # order matters: edit from the bottom up so earlier line numbers stay valid
    iso_start = find("class IsohedralTiling(Tiling):")
    reg = find("# Registry: string")
    reg_sep = reg - 1
    lines[iso_start:reg_sep] = NEW_ISOHEDRAL.split("\n") + ["", ""]
    cut_generate("class QuadrilateralTiling(Tiling):", POLY_INIT, "# ----")
    cut_generate("class TriangleTiling(Tiling):", POLY_INIT, "# ----")
    cut_generate("class HexagonTiling(Tiling):", HEX_INIT, "# ----")
    cut_generate("class SquareTiling(Tiling):", SQUARE_INIT, "# ----")
    # adjacency helpers
    a = find("def _compute_adjacency_from_lattice(")
    b = find("# SquareTiling")
    lines[a : b - 1] = NEW_BASE.split("\n") + [""]
    text = "\n".join(lines)
    for name in ("SquareTiling", "HexagonTiling", "TriangleTiling", "QuadrilateralTiling"):
        text = text.replace(f"class {name}(Tiling):", f"class {name}(_IsotileTiling):")
    text = text.replace("import math\nimport re", "import math\nimport re\n\nimport shapely", 1)
    text = text.replace("IsohedralTiling.from_preset(spec)", "IsohedralTiling.from_preset(spec)")
    text = text.replace("if spec in IsohedralTiling._PRESETS:", "if spec in IsohedralTiling.list_presets():")
    return text


def main() -> None:
    checkout, copy = Path(sys.argv[1]), Path(sys.argv[2])
    src = (checkout / "src/carto_flow/symbol_cartogram/tiling.py").read_text()
    out = copy / "src/carto_flow/symbol_cartogram/tiling.py"
    out.write_text(build(src))
    print(f"wrote {out} ({len(out.read_text().splitlines())} lines; the original has {len(src.splitlines())})")


if __name__ == "__main__":
    main()
