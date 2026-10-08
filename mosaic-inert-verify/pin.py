import sys
import geopandas as gpd, numpy as np
from shapely.geometry import box
from carto_flow.symbol_cartogram import MosaicLayout
from carto_flow.symbol_cartogram.layouts import prepare_layout_data

COUNTS_4X3 = [4, 3, 5, 4, 6, 3, 4, 5, 3, 4, 3, 5]
geoms = [box(c, r, c + 1, r + 1) for r in range(3) for c in range(4)]
gdf = gpd.GeoDataFrame({"tiles": COUNTS_4X3}, geometry=geoms)
data = prepare_layout_data(gdf, tile_count="tiles", pre_scale=False)
res = MosaicLayout(morph=False).compute(data, show_progress=False)
grouped = {}
for slot, g in enumerate(np.asarray(res.source_indices).tolist()):
    grouped.setdefault(g, []).append(int(res.assignments[slot]))
print("EXPECTED = ", [sorted(grouped[g]) for g in range(len(COUNTS_4X3))])
print("tile_size", repr(float(res.tile_size)))
