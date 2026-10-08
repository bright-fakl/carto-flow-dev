import sys, time
import numpy as np
import carto_flow.data as examples
import carto_flow.flow_cartogram as flow

def _geoms(result):
    return result.to_geodataframe()["geometry"]

def checksum(result):
    total = 0.0
    for geom in _geoms(result):
        if geom is None:
            continue
        if geom.geom_type == "Polygon":
            total += float(np.asarray(geom.exterior.coords).sum())
        elif geom.geom_type == "MultiPolygon":
            for p in geom.geoms:
                total += float(np.asarray(p.exterior.coords).sum())
    return total

def n_coords(result):
    n = 0
    for geom in _geoms(result):
        if geom is None:
            continue
        if geom.geom_type == "Polygon":
            n += len(geom.exterior.coords)
        elif geom.geom_type == "MultiPolygon":
            for p in geom.geoms:
                n += len(p.exterior.coords)
    return n

if __name__ == "__main__":
    n_iter = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    n_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    label = sys.argv[3] if len(sys.argv) > 3 else "states"

    from carto_flow.geo_utils.simplification import densify_coverage

    if label == "states":
        gdf = examples.load_us_census(population=True)
        value_col = "Population"
    elif label == "districts":
        gdf = examples.load_us_census(level="congressional_district", population=True)
        value_col = "Population"
    else:
        raise SystemExit(f"unknown label {label}")

    max_seg = float(sys.argv[4]) if len(sys.argv) > 4 else None
    if max_seg:
        gdf = densify_coverage(gdf, max_segment_length=max_seg)

    checksums = []
    times = []
    for i in range(n_runs):
        t0 = time.perf_counter()
        result = flow.morph_gdf(gdf, value_col, options=flow.MorphOptions(n_iter=n_iter, show_progress=False))
        dt = time.perf_counter() - t0
        cs = checksum(result)
        checksums.append(cs)
        times.append(dt)
        print(f"run {i}: checksum={cs!r} n_coords={n_coords(result)} time={dt:.3f}s")

    unique = len(set(checksums))
    print(f"n_iter={n_iter} runs={n_runs} unique_checksums={unique} mean_time={np.mean(times):.3f}s std={np.std(times):.3f}s")
