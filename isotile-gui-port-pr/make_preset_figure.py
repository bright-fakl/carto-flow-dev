import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from isotile import interpolate, enforce_symmetry, get_type
from isohedral_tiling_ui.editor_model import preset_curve, Draft
from isohedral_tiling_ui.utils.curve_presets import list_curve_presets, get_curve_preset
names=list_curve_presets()
def old(n,shape): return np.asarray(enforce_symmetry(get_curve_preset(n),shape))
def cur(n,shape):
    p=np.array(get_curve_preset(n),float); out=np.asarray(enforce_symmetry(p,shape))
    if shape in("S","U") and n!="straight" and np.abs(out[:,1]).max()<1e-9:
        im=p[::-1].copy(); im[:,0]=1-im[:,0]
        if shape=="S": im[:,1]=-im[:,1]
        out=np.asarray(enforce_symmetry((p+im)/2,shape))
    return out
def chosen(n,shape): return preset_curve(n,shape)
def comp(n,shape):
    p=np.array(get_curve_preset(n),float); h=p.copy(); h[:,0]/=2
    img=h[::-1][1:].copy(); img[:,0]=1-img[:,0]
    if shape=="S": img[:,1]=-img[:,1]
    return np.vstack([h,img])
rules={"a old":old,"b first half":cur,"c compressed":comp,"d chosen":chosen}
def kink(pts):
    xy=interpolate(pts,"spline"); c=np.argmin(abs(xy[:,0]-0.5)); 
    a=xy[c]-xy[max(c-3,0)]; b=xy[min(c+3,len(xy)-1)]-xy[c]
    return np.degrees(np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1)))
rows=[(s,r) for s in "SU" for r in rules]
if len(sys.argv)>1:
    fig,ax=plt.subplots(len(rows),len(names),figsize=(len(names)*1.05,len(rows)*1.0))
    for ri,(shape,r) in enumerate(rows):
        for c,n in enumerate(names):
            a=ax[ri,c]; pts=rules[r](n,shape); xy=interpolate(pts,"spline")
            flat=np.abs(pts[:,1]).max()<1e-9 and n!="straight"
            a.plot(xy[:,0],xy[:,1],color="#c0392b" if flat else "#1a5fa0",lw=1.4); a.plot(pts[:,0],pts[:,1],".",color="#444",ms=2)
            a.set_xlim(-0.1,1.1); a.set_ylim(-0.3,0.3); a.set_xticks([]); a.set_yticks([]); a.axhline(0,color="#ddd",lw=.5)
            for sp in a.spines.values(): sp.set_color("#ccc")
            if ri==0: a.set_title(n.replace("_"," "),fontsize=5.5)
            if c==0: a.set_ylabel(f"{shape} {r}",fontsize=6)
    plt.tight_layout(pad=.3); plt.savefig(sys.argv[1],dpi=170)
# metrics
import collections
for shape in "SU":
    for r,f in rules.items():
        flat=[n for n in names if n!="straight" and np.abs(f(n,shape)[:,1]).max()<1e-9]
        k=[round(kink(f(n,shape)),0) for n in names]
        print(shape,r,"flat:",flat,"max kink",np.nanmax(k),"nodes",[len(f(n,shape)) for n in names][:6])
# validity
valid=collections.Counter(); tot=collections.Counter()
for t in (4,5,12,13,14,2,3,6,7,8,9,10,11,15,16,17,18,22,23):
    try: ty=get_type(t)
    except Exception: continue
    for sid,shape in enumerate(ty.shape_types):
        if shape not in ("S","U"): continue
        d=Draft.of(t)
        for r,f in rules.items():
            for n in names:
                if n=="straight": continue
                try: ok=d.with_curve(sid,f(n,shape)).report().valid
                except Exception: ok=False
                tot[(shape,r)]+=1; valid[(shape,r)]+=ok
for k in sorted(tot): print("valid",k,valid[k],"/",tot[k])
for r,f in rules.items():
    k=[(n,round(kink(f(n,"U")))) for n in names if n!="straight"]
    print("U kinks>10deg",r,sum(1 for n,v in k if v>10),[n for n,v in k if v>10])
