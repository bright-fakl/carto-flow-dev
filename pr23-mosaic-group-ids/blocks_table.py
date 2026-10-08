import sys, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import carto_flow.data as d, carto_flow.symbol_cartogram as smb
from carto_flow.geo_utils import find_adjacent_pairs
g = d.load_us_census(population=True)
g["tiles"] = np.maximum(1, np.round(g["Population"]/g["Population"].sum()*150)).astype(int)
r = smb.create_symbol_cartogram(g, tile_count="tiles", layout="mosaic", show_progress=False)
lr = r.layout_result
tiles = lr.tiles_gdf  # geometry_id column?
gid_col = [c for c in tiles.columns if "geom" in c.lower() and "id" in c.lower()][0]
polys = list(tiles.geometry); pairs = find_adjacent_pairs(polys)
adj = {i: set() for i in range(len(polys))}
for i,j,_ in pairs: adj[i].add(j); adj[j].add(i)
rows=[]
for k,name in enumerate(g["State Name"]):
    idx=[i for i,v in enumerate(tiles[gid_col]) if v==k]
    seen=set(); blocks=0
    for s in idx:
        if s in seen: continue
        blocks+=1; stack=[s]
        while stack:
            u=stack.pop()
            if u in seen: continue
            seen.add(u); stack.extend(v for v in adj[u] if v in idx)
    rows.append((name, int(g["tiles"].iloc[k]), len(idx), blocks))
df=pd.DataFrame(rows, columns=["state","requested","obtained","blocks"])
df.to_csv(sys.argv[1], index=False)
print(sys.argv[1], "regions with obtained!=requested:", int((df.obtained!=df.requested).sum()), "split:", int((df.blocks>1).sum()))
