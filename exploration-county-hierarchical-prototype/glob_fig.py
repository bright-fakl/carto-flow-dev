import warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/counties_prepared.parquet"); pop=g["pop"].to_numpy(float)
fig,axs=plt.subplots(1,2,figsize=(15,6))
for ax,grid in zip(axs,(1024,2048)):
    o=np.array(gpd.read_parquet(f"{S}/glob_{grid}_orig.parquet").geometry.values,dtype=object)
    a=shapely.area(o); t=pop/pop.sum()*a.sum(); e=np.clip(np.log2(a/t),-1,1)
    gg=gpd.GeoDataFrame({"e":e,"s":g.STATEFP},geometry=list(shapely.make_valid(o)),crs=g.crs)
    gg.plot("e",ax=ax,cmap="RdBu_r",vmin=-1,vmax=1,linewidth=0); gg.dissolve("s").boundary.plot(ax=ax,color="k",linewidth=0.4)
    ax.set_title(f"single grid {grid}, stall rule off: mean {abs(a-t).__truediv__(t).mean()*100:.1f}%, median {np.median(abs(a-t)/t)*100:.2f}%",fontsize=10); ax.axis("off")
fig.suptitle("County area error log2(area/target), clipped to +-1 (red: too large)"); fig.tight_layout(); fig.savefig(f"{S}/glob_fig.png",dpi=110)
