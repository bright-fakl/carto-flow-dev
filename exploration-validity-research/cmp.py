import sys, numpy as np, os
d=os.path.dirname(os.path.abspath(__file__))+"/out/"
a=np.load(d+sys.argv[1]+"_county.npz"); b=np.load(d+sys.argv[2]+"_county.npz")
v=a["v"]
def err(z, mask):
    T=v/v[mask].sum()*z["area"][mask].sum(); return np.abs(z["area"]-T)/T*100
bv=a["valid"]
ea=err(a,bv); eb=err(b,bv)
print("base-valid", bv.sum(), "n>10: a", (ea[bv]>10).sum(), "b", (eb[bv]>10).sum())
worse=bv&(eb>10)&(ea<=10); better=bv&(ea>10)&(eb<=10)
print("worse (b>10, a<=10):", worse.sum(), "better:", better.sum())
# target area relative to final area scale
T=v/v[bv].sum()*a["area"][bv].sum()
print("median target area of worse (km2)", np.median(T[worse])/1e6, "of better", np.median(T[better])/1e6 if better.any() else None, "all", np.median(T)/1e6)
inv=~bv
print("invalid-in-base counties: err in b: median", np.median(eb[inv]), ">10:", (eb[inv]>10).sum(), "of", inv.sum())
# correlation with distance to invalid ones not available; print worst
idx=np.argsort(-(eb-ea)*bv)[:10]; print([(int(i), round(ea[i],1), round(eb[i],1), round(T[i]/1e6,1)) for i in idx])
