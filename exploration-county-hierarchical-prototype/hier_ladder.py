import sys, time, warnings
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.api import multiresolution_morph
warnings.filterwarnings("ignore")
S = "/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
R0, L = int(sys.argv[1]), int(sys.argv[2])
g = gpd.read_parquet(f"{S}/cty/counties_prepared.parquet")
s1 = gpd.read_parquet(f"{S}/h_512_512_1024_s1.parquet")
pop = g["pop"].to_numpy(float)
def err(geoms, tag):
    a = shapely.area(np.asarray(geoms, dtype=object)); t = pop / pop.sum() * a.sum(); e = np.abs(a - t) / t * 100
    inv = int((~shapely.is_valid(np.asarray(geoms, dtype=object))).sum())
    print(f"{tag}: mean {e.mean():.2f}% median {np.median(e):.2f}% p95 {np.percentile(e,95):.1f}% max {e.max():.1f}% invalid {inv}", flush=True)
geoms = np.array(s1.geometry.values, dtype=object).copy()
err(geoms, "after stage1")
opt = MorphOptions(area_scale=1e-6, n_iter=500, show_progress=False)
t = time.time(); bad = []; seams = []
for s in sorted(set(g.STATEFP)):
    idx = np.flatnonzero(g.STATEFP.to_numpy() == s)
    if len(idx) == 1: continue
    sub = gpd.GeoDataFrame({"pop": pop[idx]}, geometry=list(geoms[idx]), crs=g.crs)
    before = shapely.union_all(shapely.make_valid(geoms[idx]))
    c = multiresolution_morph(sub, "pop", min_resolution=R0, levels=L, options=opt)
    new = np.array(c.get_geometry(), dtype=object); geoms[idx] = new
    seams.append(shapely.symmetric_difference(before, shapely.union_all(shapely.make_valid(new))).area / before.area * 100)
    if "CONVERGED" not in str(c.status).upper(): bad.append((s, len(idx), str(c.status).split(".")[-1], c.niterations))
print(f"stage2 ladder {R0}x{L}: {time.time()-t:.1f}s, not converged: {bad}", flush=True)
print("outline change (sym. difference, %% of state area): median %.1f max %.1f" % (np.median(seams), max(seams)), flush=True)
err(geoms, "after stage2")
gpd.GeoDataFrame({"GEOID": g.GEOID}, geometry=list(geoms), crs=g.crs).to_parquet(f"{S}/ladder_{R0}_{L}_s2.parquet")
