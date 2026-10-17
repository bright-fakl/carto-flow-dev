import sys, time, warnings
import geopandas as gpd, numpy as np, shapely
from carto_flow.flow_cartogram import MorphOptions
from carto_flow.flow_cartogram.algorithm import morph_geometries
warnings.filterwarnings("ignore")
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
grid=int(sys.argv[1]); n=int(sys.argv[2]); start=sys.argv[3]
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet"); pop=g["pop"].to_numpy(float); st=g.STATEFP.to_numpy()
geo=np.array((gpd.read_parquet(f"{S}/h_512_512_1024_s1.parquet") if start=="s1" else g).geometry.values,dtype=object)
def err(geoms,tag):
    a=shapely.area(geoms); t=pop/pop.sum()*a.sum(); e=abs(a-t)/t*100
    sa=np.array([a[st==s].sum() for s in sorted(set(st))]); sp=np.array([pop[st==s].sum() for s in sorted(set(st))]); ste=abs(sa/sa.sum()-sp/sp.sum())/(sp/sp.sum())*100
    inv=int((~shapely.is_valid(geoms)).sum())
    print(f"{tag}: county mean {e.mean():.2f} median {np.median(e):.2f} p95 {np.percentile(e,95):.1f} max {e.max():.0f} | state mean {ste.mean():.2f} max {ste.max():.1f} | invalid {inv}",flush=True)
err(geo,"start")
t=time.time()
c=morph_geometries(list(geo),pop,options=MorphOptions(grid=grid,grid_margin=0.5,grid_square=True,area_scale=1e-6,n_iter=n,show_progress=False,stall_patience=None))
print(str(c.status).split('.')[-1],c.niterations,f"{time.time()-t:.0f}s",flush=True)
out=np.array(c.get_geometry(),dtype=object); err(out,"result")
gpd.GeoDataFrame({"GEOID":g.GEOID},geometry=list(out),crs=g.crs).to_parquet(f"{S}/glob_{grid}_{start}.parquet")
