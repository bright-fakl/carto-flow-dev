import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from isotile import interpolate, enforce_symmetry
from isohedral_tiling_ui.editor_model import preset_curve, Draft, preset_availability
from isohedral_tiling_ui.utils.curve_presets import list_curve_presets, get_curve_preset
names=list_curve_presets()
rows=[("J","J",False),("S before","S",False),("S now","S",True),("U before","U",False),("U now","U",True)]
fig,ax=plt.subplots(len(rows),len(names),figsize=(len(names)*1.05,len(rows)*1.0))
for r,(lab,shape,new) in enumerate(rows):
    for c,n in enumerate(names):
        a=ax[r,c]
        pts=preset_curve(n,shape) if new or shape=="J" else enforce_symmetry(get_curve_preset(n),shape)
        xy=interpolate(pts,"spline")
        flat=np.abs(pts[:,1]).max()<1e-9 and n!="straight"
        a.plot(xy[:,0],xy[:,1],color="#c0392b" if flat else "#1a5fa0",lw=1.6)
        a.plot(pts[:,0],pts[:,1],".",color="#444",ms=2.5)
        a.set_xlim(-0.1,1.1); a.set_ylim(-0.3,0.3); a.set_xticks([]); a.set_yticks([]); a.axhline(0,color="#ddd",lw=0.5)
        for sp in a.spines.values(): sp.set_color("#ccc")
        if r==0: a.set_title(n.replace("_"," "),fontsize=5.5)
        if c==0: a.set_ylabel(lab,fontsize=7)
plt.tight_layout(pad=0.3); plt.savefig(sys.argv[1],dpi=170)
