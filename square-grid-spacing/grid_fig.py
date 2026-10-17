import json, geopandas as gpd, numpy as np, shapely, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
S="/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad"
fig,axs=plt.subplots(1,3,figsize=(16,5),gridspec_kw={"width_ratios":[1,1,1]})
for k,(lab,col) in enumerate([("before","tab:red"),("after","tab:blue")]):
    d=json.load(open(f"{S}/gf_{'old' if k==0 else 'new'}.json")); its=sorted(map(int,d)); axs[0].plot(its,[d[str(i)] for i in its],color=col,label=lab)
axs[0].set_xlabel("iteration"); axs[0].set_ylabel("invalid county polygons"); axs[0].set_title("Square grid 128, 3,108 counties"); axs[0].legend()
go=gpd.read_parquet(f"{S}/gf_old_it10.parquet"); bb=go[~go.geometry.is_valid].total_bounds; pad=0.4*max(bb[2]-bb[0],bb[3]-bb[1]); cx,cy=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2; R=0.5*max(bb[2]-bb[0],bb[3]-bb[1])+pad
for ax,tag,lab in zip(axs[1:],("old","new"),("before","after")):
    g=gpd.read_parquet(f"{S}/gf_{tag}_it10.parquet"); inv=~g.geometry.is_valid
    g[~inv].plot(ax=ax,color="#cfd8e3",edgecolor="white",linewidth=0.2)
    if inv.any(): g[inv].plot(ax=ax,color="tab:red",edgecolor="k",linewidth=0.3)
    ax.set_xlim(cx-R,cx+R); ax.set_ylim(cy-R,cy+R); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{lab}: iteration 11\n{int(inv.sum())} invalid polygons (red)",fontsize=10)
fig.tight_layout(); fig.savefig("/home/fakl/carto-flow-dev/square-grid-spacing/fig_invalid.png",dpi=110)
