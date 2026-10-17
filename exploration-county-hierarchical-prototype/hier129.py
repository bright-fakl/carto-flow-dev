import sys, time, warnings, json
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
warnings.filterwarnings("ignore")
S = "/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g = gpd.read_parquet(f"{S}/cty/counties_prepared.parquet")
pop = g["pop"].to_numpy(float)
G2, G1, GP = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])  # member grid, state grid, polish grid

def err(geoms, tag):
    a = shapely.area(np.asarray(geoms, dtype=object))
    t = pop / pop.sum() * a.sum()
    e = np.abs(a - t) / t * 100
    inv = int((~shapely.is_valid(np.asarray(geoms, dtype=object))).sum())
    print(f"{tag}: county mean {e.mean():.2f}% median {np.median(e):.2f}% max {e.max():.1f}% invalid {inv}", flush=True)
    return e

def opts(grid, n=500, **kw):
    return MorphOptions(grid=grid, grid_margin=0.5, grid_square=True, area_scale=1e-6, n_iter=n, show_progress=False, **kw)

err(list(g.geometry), "start")
# stage 1: states, county vertices carried as coords
t0 = time.time()
st = g.dissolve("STATEFP", aggfunc={"pop": "sum"}).reset_index()
xy = shapely.get_coordinates(g.geometry.values)
c1 = morph_geometries(list(st.geometry), st["pop"].to_numpy(float), coords=xy, options=opts(G1))
print("stage1", c1.status, c1.niterations, f"{time.time()-t0:.1f}s", flush=True)
xy1 = np.asarray(c1.get_coords())
geoms1 = shapely.set_coordinates(np.array(g.geometry.values, dtype=object).copy(), xy1)
sa = shapely.area(np.array(c1.get_geometry(), dtype=object))
print("state error mean %.2f%% max %.2f%%" % tuple(f(np.abs(sa - st["pop"].to_numpy(float)/pop.sum()*sa.sum())/(st["pop"].to_numpy(float)/pop.sum()*sa.sum())*100) for f in (np.mean, np.max)), flush=True)
err(geoms1, "after stage1")
# stage 2: per state
t1 = time.time()
geoms2 = geoms1.copy()
rows = []
for s in st.STATEFP:
    idx = np.flatnonzero(g.STATEFP.to_numpy() == s)
    if len(idx) == 1:
        continue
    before = shapely.union_all(shapely.make_valid(geoms1[idx]))
    c = morph_geometries(list(geoms1[idx]), pop[idx], options=opts(G2))
    new = np.array(c.get_geometry(), dtype=object)
    geoms2[idx] = new
    after = shapely.union_all(shapely.make_valid(new))
    seam = shapely.symmetric_difference(before, after).area / before.area * 100
    rows.append((s, len(idx), str(c.status).split(".")[-1], c.niterations, seam))
print(f"stage2 {time.time()-t1:.1f}s; states not converged:", [(r[0], r[1], r[2], r[3]) for r in rows if "CONVERGED" not in r[2].upper()], flush=True)
print("seam (symmetric difference of state outline, %% of state area): median %.1f max %.1f" % (np.median([r[4] for r in rows]), max(r[4] for r in rows)), flush=True)
err(geoms2, "after stage2")
# stage 3: global polish
t2 = time.time()
c3 = morph_geometries(list(geoms2), pop, options=opts(GP, n=150))
g3 = np.array(c3.get_geometry(), dtype=object)
print("polish", c3.status, c3.niterations, f"{time.time()-t2:.1f}s", flush=True)
err(g3, "after polish")
gpd.GeoDataFrame({"GEOID": g.GEOID, "s1": 0}, geometry=list(geoms1), crs=g.crs).to_parquet(f"{S}/h_{G2}_{G1}_{GP}_s1.parquet")
gpd.GeoDataFrame({"GEOID": g.GEOID}, geometry=list(geoms2), crs=g.crs).to_parquet(f"{S}/h_{G2}_{G1}_{GP}_s2.parquet")
gpd.GeoDataFrame({"GEOID": g.GEOID}, geometry=list(g3), crs=g.crs).to_parquet(f"{S}/h_{G2}_{G1}_{GP}_s3.parquet")
