import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from carto_flow.geo_utils import densify_coverage
from carto_flow.flow_cartogram import MorphOptions, CartogramWorkflow
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g0=gpd.read_parquet(f"{S}/cty/acs_county.parquet")
fig,axs=plt.subplots(1,2,figsize=(15,6))
for ax,(lab,seg) in zip(axs,(("segments up to 5 km (bundled)",None),("segments up to 1 km",1000))):
    g=g0 if seg is None else densify_coverage(g0,max_segment_length=seg); v=g["pop"].to_numpy(float); gdf=g[["geometry"]].copy(); gdf["v"]=v
    w=CartogramWorkflow(gdf,"v",validate=False); w.morph_multiresolution(min_resolution=128,levels=5,options=MorphOptions(area_scale=1e-6,n_iter=1000,show_progress=False))
    o=np.array(w.last.get_geometry(),dtype=object); a=shapely.area(o); t=v/v.sum()*a.sum(); e=np.clip(np.log2(a/t),-1,1)
    inv=~shapely.is_valid(o); gg=gpd.GeoDataFrame({"e":e,"s":g["STATE"]},geometry=list(shapely.make_valid(o)),crs=g.crs)
    gg.plot("e",ax=ax,cmap="RdBu_r",vmin=-1,vmax=1,linewidth=0); gg.dissolve("s").boundary.plot(ax=ax,color="k",linewidth=0.3)
    gg[inv].plot(ax=ax,facecolor="none",edgecolor="limegreen",linewidth=0.6)
    ax.set_title(f"{lab}: mean error {np.mean(abs(a-t)/t)*100:.1f} %, median {np.median(abs(a-t)/t)*100:.2f} %, {int(inv.sum())} invalid (green outline)",fontsize=10); ax.axis("off")
fig.suptitle("3,108 counties by population, ladder from 128 to 2048 cells, default options. Color: log2(area/target), red too large"); fig.tight_layout(); fig.savefig("/home/fakl/carto-flow-dev/segment-density-warning/fig_ladder.png",dpi=105)
