"""The same scenario on a linear axis (clipped at +-40 %), with the peak-to-peak statistics of the last 40 iterations.

Run from a carto-flow checkout of the PR branch (the option adaptive_dt must exist):
    NUMBA_NUM_THREADS=8 uv run python signed_errors_linear.py
Writes signed_errors_tangential_linear.png next to this file.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
import warnings; warnings.filterwarnings("ignore")
import numpy as np, shapely
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor
S=data.load_us_census(population=True).reset_index(drop=True); w=S["Population"].to_numpy(float); nm=S["State Abbreviation"].to_numpy(); share=w/w.sum()
res={}
for a in (False,True):
    o=MorphOptions.preset_balanced().copy_with(area_scale=1e-6,n_iter=400,show_progress=False,dt=0.6,snapshot_every=1,anisotropy=DirectionalTensor.tangential(Dpar=4,Dperp=0.3),adaptive_dt=a)
    r=morph_gdf(S,"Population",options=o); n=r.niterations
    E=np.array([(shapely.area(np.asarray(r.get_geometry(iteration=i),dtype=object))/(w/w.sum()*shapely.area(np.asarray(r.get_geometry(iteration=i),dtype=object)).sum())-1)*100 for i in range(1,n+1)])
    res[a]=E
    win=E[n-40:n]; pp=win.max(axis=0)-win.min(axis=0)       # peak-to-peak per region over the last 40 iterations
    amp=np.abs(win).max(axis=0)
    print(f"adaptive_dt={a} (stop {n}), last 40 iterations, per region (linear %):")
    print("   peak-to-peak: median %.1f  75th %.1f  90th %.1f  max %.1f | regions with peak-to-peak >5%%: %d, >10%%: %d, >20%%: %d (of 49)"%(np.median(pp),*np.percentile(pp,[75,90]),pp.max(),(pp>5).sum(),(pp>10).sum(),(pp>20).sum()))
    print("   max |error|: median %.1f  90th %.1f | mean over regions of |error| at the stop: %.2f%% (tolerance mean 5%%)"%(np.median(amp),np.percentile(amp,90),np.abs(E[-1]).mean()))
    top=np.argsort(-pp)[:6]; print("   largest peak-to-peak:",[(nm[k],round(pp[k]),f"{share[k]*100:.2f}% area") for k in top])
fig,axes=plt.subplots(1,2,figsize=(14,5),sharey=True)
cmap=plt.get_cmap("viridis"); lg=np.log10(share); norm=plt.Normalize(lg.min(),lg.max())
for ax,a in zip(axes,(False,True)):
    E=res[a]; n=len(E)
    for k in range(49): ax.plot(np.arange(1,n+1),E[:,k],color=cmap(norm(lg[k])),linewidth=0.8)
    ax.axhline(0,color="k",linewidth=0.5)
    for t in (10,-10): ax.axhline(t,color="gray",linestyle="--",linewidth=0.7)
    ax.set_ylim(-40,40); ax.set_xlim(55,170); ax.set_title(f"adaptive_dt={a}: {n} iterations",fontsize=10); ax.set_xlabel("iteration")
axes[0].set_ylabel("signed relative area error %, LINEAR axis (clipped at +-40 %)")
fig.suptitle("Tangential anisotropy, dt 0.6, linear scale (dashed: +-10 %); lines colored by target area, dark = small",fontsize=10)
fig.tight_layout(); fig.savefig(str(HERE / "signed_errors_tangential_linear.png"),dpi=105)
