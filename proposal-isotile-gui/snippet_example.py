from isotile import IsohedralTiling

tiling = IsohedralTiling(
    43,
    parameters=[0.230769230769, 0.5],
    edge_curves={
        0: [[0.0, 0.0], [0.3, 0.0], [0.5, 0.15], [0.7, 0.0], [1.0, 0.0]],
        1: [[0.0, 0.0], [0.3, 0.0], [0.5, -0.15], [0.7, 0.0], [1.0, 0.0]],
    },
    edge_curve_modes={0: 'linear', 1: 'linear'},
)

tiles = tiling.fill_region((-2, -2, 2, 2), n_tiles=100, margin=0.1)
outlines = tiles.outlines()  # (n_tiles, n_points, 2) array of the tile outlines
# polygons = tiles.polygons()  # shapely polygons; needs isotile[shapely]
print(len(outlines), 'tiles')
