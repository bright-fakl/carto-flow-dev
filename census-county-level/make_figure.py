import geopandas as gpd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from carto_flow.data import load_us_census
g=load_us_census(level="county",race=True,poverty=True)
fig,axs=plt.subplots(1,2,figsize=(14,5))
g.plot(np.log10(g["Population Density"]),ax=axs[0],cmap="viridis",linewidth=0,legend=True,legend_kwds={"shrink":0.6,"label":"log10 people per km2"}); axs[0].set_title("Population density")
g.plot(g["Asian %"]*100,ax=axs[1],cmap="magma_r",linewidth=0,vmax=10,legend=True,legend_kwds={"shrink":0.6,"label":"% Asian (clipped at 10)"}); axs[1].set_title("Asian share")
for a in axs: a.axis("off")
fig.suptitle(f"load_us_census(level='county'): {len(g)} counties"); fig.tight_layout(); fig.savefig("/home/fakl/carto-flow-dev/census-county-level/fig_counties.png",dpi=100)
for c in ["Population","White","Black or African American","Asian","Hispanic or Latino"]:
    v=g[c].to_numpy(float); print(c, "min",int(v.min()),"median",int(np.median(v)),"max",int(v.max()),"zeros",int((v==0).sum()))
