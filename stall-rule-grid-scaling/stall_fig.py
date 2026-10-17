import json,warnings; warnings.filterwarnings("ignore")
import geopandas as gpd, numpy as np, shapely, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
g=gpd.read_parquet(f"{S}/cty/acs_county.parquet"); v=g["pop"].to_numpy(float)
fig,axs=plt.subplots(1,2,figsize=(15,6))
for ax,tag,lab in zip(axs,("old","new"),("before","after")):
    o=gpd.read_parquet(f"{S}/st_{tag}.parquet"); st,it=json.load(open(f"{S}/st_{tag}.json")); geo=np.array(o.geometry.values,dtype=object)
    a=shapely.area(geo); t=v/v.sum()*a.sum(); e=np.clip(np.log2(a/t),-1,1)
    gg=gpd.GeoDataFrame({"e":e,"s":o["s"]},geometry=list(shapely.make_valid(geo)),crs=g.crs)
    gg.plot("e",ax=ax,cmap="RdBu_r",vmin=-1,vmax=1,linewidth=0); gg.dissolve("s").boundary.plot(ax=ax,color="k",linewidth=0.3)
    ax.set_title(f"{lab}: {st.lower()} after {it} iterations, mean error {np.mean(abs(a-t)/t)*100:.1f}%",fontsize=10); ax.axis("off")
fig.suptitle("3,108 counties by population, single grid 1024, default options. Color: log2(area/target), red too large"); fig.tight_layout(); fig.savefig("/home/fakl/carto-flow-dev/stall-rule-grid-scaling/fig_counties.png",dpi=105)
