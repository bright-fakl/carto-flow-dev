import warnings,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import expect as E
E.cases["districts lognormal1"]=(E.di,"Population",("ln",1.0))
for name,grids in (("AZ",[256,1024]),("states",[256,1024]),("districts",[256,1024]),("counties",[1024]),("districts lognormal1",[256,1024]),("districts lognormal2",[256,1024])):
    for grid in grids:
        me,dtau,k,c=E.run(name,grid,n=200)
        gr=c.grid; cell=min(gr.dx,gr.dy)
        a=shapely.area(np.array(c.get_geometry(),dtype=object))
        Ls={"mean":np.mean(np.sqrt(a)),"areaw":np.sqrt((a**2).sum()/a.sum()),"median":np.median(np.sqrt(a))}
        ctrl=np.array(E.LOG["ctrl"][:k]); d=0.2*ctrl*cell
        out={}
        for nm,L in Ls.items():
            vals=[]
            for w in (0,40,80):
                if w+10>=k: continue
                e0,e1=me[w],me[w+10]; vals.append((e0-e1)/e0/(d[w:w+10].sum()/L))
            out[nm]=[round(x,2) for x in vals]
        print(f"{name:20s} grid {grid:5d} {c.status.name[:5]} L/cell mean {Ls['mean']/cell:5.1f} areaw {Ls['areaw']/cell:6.1f} | eta mean-L {out['mean']} areaw-L {out['areaw']} median-L {out['median']}",flush=True)
