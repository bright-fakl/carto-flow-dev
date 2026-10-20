import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness
from carto_flow.geo_utils.geometry import unpack_geometries, reconstruct_geometries
from vw import rebuild_metadata
for ds in ("coarse", "county"):
    g, v = harness.load(ds)
    geoms = list(g.geometry.values)
    info = unpack_geometries(geoms)
    sizes = np.diff(np.asarray(info.ragged_offsets[0]))
    md = rebuild_metadata(info.metadata, sizes)
    print(ds, "metadata equal:", md == info.metadata)
    info.metadata = md
    rec = np.array(reconstruct_geometries(info), dtype=object)
    print(" reconstruct equals input:", bool(shapely.equals_exact(rec, np.array(geoms, dtype=object), 0).all()), "invalid in input", int((~shapely.is_valid(np.array(geoms, dtype=object))).sum()))
    # ragged ring order vs metadata order
    rr = shapely.from_ragged_array(info.ragged_geometry_type, info.coords, info.ragged_offsets)
    print(" ragged rebuild valid:", int((~shapely.is_valid(rr)).sum()), "equal to input", bool(shapely.equals_exact(np.array(rr, dtype=object), np.array(geoms, dtype=object), 0).all()))
