"""World: what forcing Malaysia/Indonesia into one block costs their neighbours.

Within-version comparison -- same shipping code, only `multipart_min_tiles`
differs -- so it isolates the sub-region effect from the relocation reach.
"""
import warnings, json, time; warnings.filterwarnings("ignore")
import numpy as np, shapely
from collections import deque
import carto_flow.data as cfdata
from carto_flow.symbol_cartogram.layouts import prepare_layout_data
from carto_flow.symbol_cartogram.layouts.mosaic import MosaicLayout

WORLD_CRS = "ESRI:54009"
BUDGET = 600


def blocks(lr, g):
    adj = lr.tiling_result.adjacency
    tiles = {int(t) for t, gg in zip(lr.assignments, lr.tiles_gdf["geometry_id"].tolist()) if int(gg) == g}
    todo, out = set(tiles), []
    while todo:
        s = todo.pop(); comp = {s}; q = deque([s])
        while q:
            t = q.popleft()
            for nb in np.flatnonzero(adj[t]):
                nb = int(nb)
                if nb in todo:
                    todo.discard(nb); comp.add(nb); q.append(nb)
        out.append(comp)
    return out


g = cfdata.load_world()
g = g[(g["name"] != "Antarctica") & (g["pop_est"] > 0)].copy().to_crs(WORLD_CRS)
pop = g["pop_est"].to_numpy(dtype=float)
g["tiles"] = np.maximum(1, np.round(pop / pop.sum() * BUDGET)).astype(int)
g = g.reset_index(drop=True)
names = list(g["name"]); counts = g["tiles"].to_numpy(); geoms = list(g.geometry)

multi = set()
for i, geom in enumerate(geoms):
    if int(counts[i]) < 2:
        continue
    parts = sorted((p.area for p in shapely.get_parts(geom)), reverse=True)
    if len(parts) > 1 and parts[1] >= 0.1 * sum(parts):
        multi.add(i)
print("multi-part candidates:", sorted(names[i] for i in multi))

data = prepare_layout_data(g, tile_count="tiles")
res = {}
for morph in (True, False):
    for thr, tag in ((1e9, "forced"), (0.5, "subregions")):
        t0 = time.perf_counter()
        lr = MosaicLayout(morph=morph, multipart_min_tiles=thr).compute(data, show_progress=False)
        m = lr.metrics.algorithm
        by = {}
        for t, gg in zip(lr.assignments, lr.tiles_gdf["geometry_id"].tolist()):
            by.setdefault(int(gg), []).append(int(t))
        single_split = sorted(names[gi] for gi, tl in by.items() if gi not in multi and len(blocks(lr, gi)) > 1)
        key = f"morph={morph}/{tag}"
        res[key] = {
            "split_single_part": len(single_split),
            "which_single_part": single_split[:20],
            "split_by_subregion_metric": m.n_noncontiguous_regions,
            "n_split_geometries": m.n_split_geometries,
            "repair_passes": m.repair_passes,
            "ring_used": int(len({int(t) for t in lr.assignments} - {int(x) for x in lr.core_tile_indices})),
            "empty_core": int(len({int(x) for x in lr.core_tile_indices} - {int(t) for t in lr.assignments})),
            "enclosed": m.n_enclosed_unassigned_tiles,
            "regions_correct": f"{m.regions_correct}/{m.regions_total}",
            "wall_s": round(time.perf_counter() - t0, 1),
        }
        for nm in ("Malaysia", "Indonesia", "New Zealand", "United States of America"):
            if nm in names:
                res[key][nm] = {"tiles": len(by.get(names.index(nm), [])), "blocks": len(blocks(lr, names.index(nm)))}
        print(key, json.dumps(res[key]))
json.dump(res, open("/tmp/mp/world_neighbours.json", "w"), indent=2)
