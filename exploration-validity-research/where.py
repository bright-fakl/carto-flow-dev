import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely, harness
g, v = harness.load("county")
d=os.path.dirname(os.path.abspath(__file__))+"/out/"
a=np.load(d+"baseline_county.npz"); b=np.load(d+sys.argv[1]+"_county.npz"); bv=a["valid"]
T=v/v[bv].sum()*b["area"][bv].sum(); e=np.abs(b["area"]-T)/T*100
big=bv&(T>=5*4.3e3**2)
bad=np.flatnonzero(big&(e>5))
geo=np.array(g.geometry.values,dtype=object)
cen=shapely.centroid(geo); cx=shapely.get_x(cen); cy=shapely.get_y(cen)
inv=np.flatnonzero(~bv)
dist=np.array([np.min(np.hypot(cx[inv]-cx[i],cy[inv]-cy[i])) for i in range(len(geo))])
print("n bad", len(bad), "median dist to a baseline-invalid county (km): bad", np.median(dist[bad])/1e3, "all", np.median(dist[big])/1e3)
# state grouping through coordinates: print x,y bins
import collections
print("by x-band (200km bins of centroid x):", np.histogram(cx[bad], bins=8)[0], "all:", np.histogram(cx[big], bins=8)[0])
print("by y-band:", np.histogram(cy[bad], bins=8)[0], "all:", np.histogram(cy[big], bins=8)[0])
print("target area (km2) quantiles of bad", np.quantile(T[bad]/1e6,[0,.25,.5,.75,1]))
print("final/original area ratio quantiles: bad", np.quantile(b["area"][bad]/shapely.area(geo[bad]),[0,.25,.5,.75,1]), " all", np.quantile(b["area"][big]/shapely.area(geo[big]),[0,.25,.5,.75,1]))
print("sign of error bad: over-target", (b["area"][bad]>T[bad]).sum(), "under", (b["area"][bad]<T[bad]).sum())
