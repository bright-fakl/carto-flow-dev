import warnings,sys; warnings.filterwarnings("ignore")
import numpy as np, shapely
sys.path.insert(0,"/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad")
import expect as E
from carto_flow.flow_cartogram import MorphOptions
for name,grids in (("AZ",[128,256,512,1024]),("states",[256,1024]),("districts",[256,1024]),("counties",[1024]),("districts lognormal2",[256,1024])):
    for grid in grids:
        me,dtau,k,c=E.run(name,grid)
        g,col,mod=E.cases[name]; gr=c.grid; cell=min(gr.dx,gr.dy)
        # typical region size: mean sqrt(final area) (areas ~ target at the end; for non-converged runs use output areas)
        a=shapely.area(np.array(c.get_geometry(),dtype=object)); L=np.mean(np.sqrt(a))
        ctrl=np.array(E.LOG["ctrl"][:k]); d=0.2*ctrl*cell      # distance moved by the fastest point per iteration
        rows=[]
        for w in range(0,k-10,40):
            e0,e1=me[w],me[min(w+10,k-1)]
            if e0<=0: continue
            obs=(e0-e1)/e0; strain=d[w:w+10].sum()/L
            rows.append(round(obs/strain,2))
        print(f"{name:20s} grid {grid:5d} {c.status.name:9s} L/cell {L/cell:6.1f}  eta per window: {rows[:7]}",flush=True)
