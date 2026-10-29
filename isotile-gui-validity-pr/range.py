"""Valid values of every parameter over a wide range, at the defaults and for the flowers preset (with its curves)."""
import sys, json, time, numpy as np
from isotile import IsohedralTiling, get_type, tiling_types
from isohedral_tiling_ui.editor_model import Draft
grid=np.unique(np.concatenate([-np.geomspace(1e4,10,40), np.arange(-10,10.0001,0.02), np.geomspace(10,1e4,40)]))
def valid_set(d,k):
    ok=[]
    for v in grid:
        p=list(d.parameters); p[k]=float(v)
        ok.append(d.with_parameters(p).report().valid)
    return np.array(ok)
def intervals(ok):
    out=[];i=0;n=len(ok)
    while i<n:
        if ok[i]:
            j=i
            while j+1<n and ok[j+1]: j+=1
            out.append((float(grid[i]),float(grid[j]), i==0, j==n-1)); i=j+1
        else: i+=1
    return out
def classify(d,k):
    ok=valid_set(d,k); iv=intervals(ok); v0=d.parameters[k]
    cur=[x for x in iv if x[0]<=v0+1e-9<=x[1]]
    cur=cur[0] if cur else None
    return dict(value=v0,intervals=[(round(a,3),round(b,3),lo,hi) for a,b,lo,hi in iv],current=cur,islands=len(iv)-1)
if __name__=="__main__":
    t0=time.time()
    d=Draft.from_tiling(IsohedralTiling.from_preset("flowers"))
    print("flowers type",d.type_number,"parameters",d.parameters,"curves",len(d.curves))
    info=get_type(d.type_number).info()
    for k in range(len(d.parameters)):
        print(k, info["parameters"][k]["description"], classify(d,k), "safe",get_type(d.type_number).safe_ranges[k])
    print("t",time.time()-t0)
