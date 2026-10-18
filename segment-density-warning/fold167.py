import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely, re
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/acs_county.parquet"); v=g["pop"].to_numpy(float); geo=list(g.geometry)
c=morph_geometries(geo,v,options=MorphOptions(grid=128,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=90,show_progress=False,stall_patience=None,snapshot_every=1))
prev=None
for it in range(1,91):
    sn=c.snapshots.get_snapshot(it)
    if sn is None: continue
    o=np.array(sn.geometry,dtype=object); inv=set(np.flatnonzero(~shapely.is_valid(o)))
    if prev is not None and inv-prev:
        new=sorted(inv-prev); print("iteration",it,"new invalid:",[(g.NAME[i][:22],shapely.is_valid_reason(o[i])[:22]) for i in new[:4]],"total",len(inv))
        if it>5: 
            i=new[0]; a0=shapely.area(np.array(c.snapshots.get_snapshot(it-1).geometry,dtype=object)[i]); print("   area before",round(a0/1e6),"km2 target",round(v[i]/v.sum()*shapely.area(o).sum()/1e6,1),"km2; n vertices",shapely.get_num_coordinates(o[i]))
            break
    prev=inv
