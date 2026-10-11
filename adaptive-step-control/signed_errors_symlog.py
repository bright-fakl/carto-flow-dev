"""Signed per-region relative area error per iteration, tangential anisotropy at dt 0.6, adaptive_dt off and on (symlog axis and heatmap).

Run from a carto-flow checkout of the PR branch (the option adaptive_dt must exist):
    NUMBA_NUM_THREADS=8 uv run python signed_errors_symlog.py
Writes signed_errors_tangential.png next to this file.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
import warnings; warnings.filterwarnings("ignore")
import numpy as np, shapely
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
from carto_flow import data
from carto_flow.flow_cartogram import MorphOptions, morph_gdf
from carto_flow.flow_cartogram.anisotropy import DirectionalTensor
S=data.load_us_census(population=True).reset_index(drop=True); w=S["Population"].to_numpy(float)
share=w/w.sum()
order=np.argsort(-share)                   # largest target area first
def run(adaptive):
    o=MorphOptions.preset_balanced().copy_with(area_scale=1e-6,n_iter=400,show_progress=False,dt=0.6,snapshot_every=1,
        anisotropy=DirectionalTensor.tangential(Dpar=4,Dperp=0.3),adaptive_dt=adaptive)
    r=morph_gdf(S,"Population",options=o)
    E=[]
    for i in range(1,r.niterations+1):
        a=shapely.area(np.asarray(r.get_geometry(iteration=i),dtype=object)); E.append((a/(w/w.sum()*a.sum())-1)*100)
    return np.array(E),r
res={a:run(a) for a in (False,True)}
nmax=max(len(res[a][0]) for a in res)
fig,axes=plt.subplots(2,2,figsize=(14,9),sharex="col")
cmap=plt.get_cmap("viridis"); lg=np.log10(share); norm=plt.Normalize(lg.min(),lg.max())
for j,a in enumerate((False,True)):
    E,r=res[a]; n=len(E); its=np.arange(1,n+1)
    ax=axes[0,j]
    for k in range(E.shape[1]):
        ax.plot(its,E[:,k],color=cmap(norm(lg[k])),linewidth=0.7,alpha=0.9)
    ax.set_yscale("symlog",linthresh=1.0); ax.axhline(0,color="k",linewidth=0.5)
    for t in (10,-10): ax.axhline(t,color="gray",linestyle="--",linewidth=0.7)
    ax.set_xlim(40,nmax+3); ax.set_ylim(-300,300)
    ax.set_title(f"adaptive_dt={a}: {n} iterations ({r.status.value})",fontsize=10)
    ax.set_ylabel("signed relative area error % (symlog)")
    ax=axes[1,j]
    H=E[:,order].T                          # regions sorted by target area, largest at top
    im=ax.imshow(H,aspect="auto",origin="upper",cmap="RdBu_r",norm=SymLogNorm(linthresh=1.0,vmin=-100,vmax=100),extent=[0.5,n+0.5,len(order)-0.5,-0.5],interpolation="nearest")
    ax.set_xlim(40,nmax+3); ax.set_xlabel("iteration"); ax.set_ylabel("regions, largest target area at top")
sm=plt.cm.ScalarMappable(norm=norm,cmap=cmap); fig.colorbar(sm,ax=axes[0,:],label="log10 target area share",shrink=0.8,pad=0.01)
fig.colorbar(im,ax=axes[1,:],label="signed relative error % (symlog)",shrink=0.8,pad=0.01)
fig.suptitle("Tangential anisotropy, states grid 256, dt 0.6: signed per-region relative area error per iteration (dashed: +-10 % tolerance)",fontsize=11)
fig.savefig(str(HERE / "signed_errors_tangential.png"),dpi=105)
for a in (False,True):
    E,r=res[a]; print(a,r.niterations,r.status.value)
