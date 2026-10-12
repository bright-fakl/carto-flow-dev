import time, warnings, numpy as np, shapely, geopandas as gpd
warnings.filterwarnings("ignore")
from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.geo_utils import densify_coverage
DISTRICTS = data.load_us_census(population=True, level="congressional_district").reset_index(drop=True)
MIN = data.load_us_census(population=True, race=True, simplify=1000); MIN["Minorities"] = MIN[["Black or African American","Asian","Hispanic or Latino"]].sum(axis=1)
COUNTIES = gpd.read_parquet("/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/counties_prepared.parquet")
def nverts(g): return int(sum(len(shapely.get_coordinates(x)) for x in g.geometry))
for label, gdf, col, kw in [("issue 85 map, grid 512", MIN, "Minorities", dict(grid_size=512)),
                            ("districts, grid 256", DISTRICTS, "Population", dict(grid_size=256)),
                            ("districts, grid 512, 0.5/1 %", DISTRICTS, "Population", dict(grid_size=512, mean_tol=.005, max_tol=.01, n_iter=400)),
                            ("counties, grid 512", COUNTIES, "total_votes", dict(grid_size=512, area_scale=1e-6, n_iter=300))]:
    o = MorphOptions(show_progress=False, **kw)
    cell = o.get_grid(o._calculate_bounds_from_geometries(gdf.geometry.values)).dx
    print(f"[{label}] cell {cell:.0f} m")
    for frac in (None, 1.0, 0.5, 0.25, 0.1):
        g = gdf if frac is None else densify_coverage(gdf, frac * cell)
        t = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore"); r = morph_gdf(g, col, options=o)
        inv = len(r.invalid_regions)
        print(f"   max segment {'input' if frac is None else f'{frac} cell':>9}: vertices {nverts(g):8d}; {r.status.value} {r.niterations}; invalid output regions {inv}; {time.perf_counter()-t:.1f}s", flush=True)
