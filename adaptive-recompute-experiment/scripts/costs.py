from common import *
import warnings
import geopandas as gpd
warnings.filterwarnings("ignore")
SP = "/tmp/claude-1000/-home-fakl-carto-flow/1d808732-154c-4811-8451-b398efcea29f/scratchpad/"
cases = {"states": (data.load_us_census(population=True).reset_index(drop=True), "Population"),
         "districts": (data.load_us_census(level='congressional_district').reset_index(drop=True), "Population"),
         "counties": (gpd.read_parquet(SP + "counties_prepared.parquet"), "total_votes")}


GRIDS = (128,)


def one(g, col, grid, n, rec, extra):
    o = MorphOptions(show_progress=False, grid_size=grid, stall_patience=None, n_iter=n, recompute_every=rec,
                     mean_tol=1e-9, max_tol=1e-9, **extra)
    alg.LAST_STATS.clear()
    morph_gdf(g, col, options=o)
    return dict(alg.LAST_STATS)


for name, (g, col) in cases.items():
    extra = dict(area_scale=1e-6) if name == "counties" else {}
    for grid in GRIDS:
        if name == "counties" and grid == 1024:
            continue
        one(g, col, grid, 3, None, extra)
        a = [one(g, col, grid, 10, None, extra) for _ in range(2)]
        b = [one(g, col, grid, 50, None, extra) for _ in range(2)]
        c = [one(g, col, grid, 40, 1, extra) for _ in range(2)]
        step = (min(x["run_s"] for x in b) - min(x["run_s"] for x in a)) / 40
        rec = min(x["recompute_s"] / x["recomputes"] for x in c)
        print(name, grid, f"step={step*1e3:.2f} ms recompute={rec*1e3:.1f} ms ratio={rec/step:.1f}", flush=True)
