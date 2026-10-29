import sys, json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0,sys.argv[1])
from isotile import IsohedralTiling, get_type
from isohedral_tiling_ui.editor_model import Draft, parameter_ranges
from range import grid, valid_set, intervals
cases=[("flowers (IH21, with its 3 curves)",Draft.from_tiling(IsohedralTiling.from_preset("flowers")),[0,1]),
       ("IH21 at the defaults",Draft.of(21),[0,1]),
       ("IH1 at the defaults",Draft.of(1),[0,1])]
rows=[(t,d,k) for t,d,ks in cases for k in ks]
fig,ax=plt.subplots(len(rows),1,figsize=(9,1.05*len(rows)+0.8),sharex=True)
def sl(x): return np.arcsinh(np.asarray(x)*2)/np.arcsinh(20)   # symlog-like display axis
for a,(t,d,k) in zip(ax,rows):
    ok=valid_set(d,k)
    x=sl(grid)
    a.fill_between(x,0,1,where=ok,step="mid",color="#7fb77e",lw=0)
    a.fill_between(x,0,1,where=~ok,step="mid",color="#e6a1a1",lw=0)
    r=parameter_ranges(d,0)[k]
    a.axvspan(sl(0),sl(1),ymin=0,ymax=0.32,color="#1971c2",alpha=0.9,lw=0)
    a.axvspan(sl(r.window_lo),sl(r.window_hi),ymin=0.34,ymax=0.62,color="#ff9900",alpha=0.9,lw=0)
    a.axvline(sl(d.parameters[k]),color="k",lw=1.2)
    a.set_yticks([]); a.set_ylabel(f"{t.split(' (')[0]}\nP{k}",rotation=0,ha="right",va="center",fontsize=7.5)
    a.set_xlim(sl(-10),sl(10))
ticks=[-10,-3,-1,-0.3,0,0.3,1,3,10]; ax[-1].set_xticks(sl(ticks)); ax[-1].set_xticklabels([str(t) for t in ticks])
ax[0].set_title("Valid (green) and invalid (red) values; blue: window of the slider before (0 to 1); orange: window now; line: current value\n(axis: asinh scale, range -10 to 10)",fontsize=8)
plt.tight_layout(); plt.savefig(sys.argv[2],dpi=150)
