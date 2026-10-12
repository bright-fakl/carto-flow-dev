import warnings, numpy as np, shapely, geopandas as gpd
from shapely import STRtree
warnings.filterwarnings("ignore")
from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
MIN = data.load_us_census(population=True, race=True, simplify=1000); MIN["Minorities"] = MIN[["Black or African American","Asian","Hispanic or Latino"]].sum(axis=1)
COUNTIES = gpd.read_parquet("/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/counties_prepared.parquet")
def parts(g): return list(g.geoms) if hasattr(g, "geoms") else [g]
def rings(g):
    for p in parts(g):
        yield np.asarray(p.exterior.coords)
        for h in p.interiors: yield np.asarray(h.coords)
def crossing_vertices(ring):
    n = len(ring) - 1
    segs = shapely.linestrings(np.stack([ring[:-1], ring[1:]], axis=1)); tree = STRtree(segs)
    a, b = tree.query(segs, predicate="intersects"); keep = (a < b) & (b - a > 1) & ~((a == 0) & (b == n - 1))
    v = set()
    for i, j in zip(a[keep], b[keep]): v.update({i % n, (i + 1) % n, j % n, (j + 1) % n})
    return ring[sorted(v)]
def run(label, gdf, col, kw):
    o = MorphOptions(show_progress=False, **kw)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore"); r = morph_gdf(gdf, col, options=o)
    geoms = list(r.get_geometry()); bad = np.flatnonzero(~shapely.is_valid(np.array(geoms, dtype=object)))
    # all vertices of all rings, keyed by exact coordinates -> set of region indices
    owners = {}
    for i, g in enumerate(geoms):
        for ring in rings(g):
            for x, y in ring[:-1]: owners.setdefault((x, y), set()).add(i)
    shared_total = np.mean([len(s) > 1 for s in owners.values()])
    n_cross = shared = 0; regions_touching = 0
    for i in bad:
        touched = False
        for ring in rings(geoms[i]):
            for x, y in crossing_vertices(ring):
                n_cross += 1; s = owners.get((x, y), {i}); 
                if len(s) > 1: shared += 1; touched = True
        regions_touching += touched
    print(f"[{label}] vertices shared with another region in the whole map: {shared_total*100:.0f} %; invalid regions {len(bad)}; vertices at the crossings {n_cross}, of which shared with a neighbor {shared} ({shared/max(n_cross,1)*100:.0f} %); invalid regions with at least one shared crossing vertex {regions_touching}", flush=True)
run("issue 85 map", MIN, "Minorities", dict(grid_size=512))
run("districts 256", DISTRICTS, "Population", dict(grid_size=256))
run("counties 256", COUNTIES, "total_votes", dict(grid_size=256, area_scale=1e-6, n_iter=300))
run("counties 512", COUNTIES, "total_votes", dict(grid_size=512, area_scale=1e-6, n_iter=300))
